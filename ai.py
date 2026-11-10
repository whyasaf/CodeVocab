"""
Ücretsiz AI sağlayıcı zinciri.

Tüm sağlayıcılar OpenAI uyumlu API sunduğu için tek bir `openai` istemcisiyle
konuşuyoruz. Anahtarı tanımlı olan sağlayıcılar sırayla denenir; biri kota
(429) ya da sunucu hatası verirse bir süre "soğumaya" alınır ve sıradakine
geçilir. Böylece tek bir ücretsiz kotaya bağlı kalmayız.

Sıra ve modeller .env üzerinden değiştirilebilir (bkz. .env.example).
"""

import json
import os
import re
import time
from dataclasses import dataclass, field

from openai import OpenAI, APIStatusError, APIConnectionError, APITimeoutError


@dataclass
class Provider:
    name: str
    base_url: str
    key_env: str
    model_env: str
    default_model: str
    extra_headers: dict = field(default_factory=dict)
    cooldown_until: float = 0.0
    supports_json_mode: bool = True
    _client: OpenAI | None = None

    @property
    def api_key(self):
        return os.environ.get(self.key_env, "").strip()

    @property
    def model(self):
        return os.environ.get(self.model_env, "").strip() or self.default_model

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=25,
                max_retries=0,
                default_headers=self.extra_headers or None,
            )
        return self._client


PROVIDERS = {
    "groq": Provider(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        key_env="GROQ_API_KEY",
        model_env="GROQ_MODEL",
        default_model="openai/gpt-oss-120b",
    ),
    "cerebras": Provider(
        name="cerebras",
        base_url="https://api.cerebras.ai/v1",
        key_env="CEREBRAS_API_KEY",
        model_env="CEREBRAS_MODEL",
        default_model="qwen-3.8-27b",
    ),
    "gemini": Provider(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        key_env="GEMINI_API_KEY",
        model_env="GEMINI_MODEL",
        default_model="gemini-3.5-flash-lite",  # hızlı; büyük flash modeller ücretsiz katmanda sık 503 veriyor
    ),
    # Aynı ücretsiz Groq anahtarıyla ikinci model. Groq kotaları MODEL BAŞINA ayrı tutulur,
    # yani bu sağlayıcı ana modelden bağımsız kendi 8k token/dk hakkına sahip.
    # Kalitesi daha düşük olduğu için zincirin sonunda, son yedek olarak durur.
    "groq-mini": Provider(
        name="groq-mini",
        base_url="https://api.groq.com/openai/v1",
        key_env="GROQ_API_KEY",
        model_env="GROQ_FALLBACK_MODEL",
        default_model="openai/gpt-oss-20b",
    ),
    "openrouter": Provider(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        key_env="OPENROUTER_API_KEY",
        model_env="OPENROUTER_MODEL",
        default_model="openrouter/free",
        extra_headers={"HTTP-Referer": "https://codevocab.app", "X-Title": "CodeVocab"},
    ),
}

DEFAULT_ORDER = "groq,gemini,openrouter,cerebras,groq-mini"
COOLDOWN_RATE_LIMIT = 60      # 429'da bekleme süresi bilinmiyorsa kaç saniye atlayalım
COOLDOWN_SERVER_ERROR = 20    # 5xx / bağlantı hatası sonrası
MAX_INLINE_WAIT = 6           # kota bu kadar saniyede açılacaksa hata verme, bekle


class AIUnavailable(Exception):
    """Hiçbir sağlayıcı yanıt veremedi."""

    def __init__(self, message, rate_limited=False):
        super().__init__(message)
        self.rate_limited = rate_limited


def active_providers():
    order = os.environ.get("AI_PROVIDER_ORDER", DEFAULT_ORDER)
    names = [n.strip().lower() for n in order.split(",") if n.strip()]
    return [PROVIDERS[n] for n in names if n in PROVIDERS and PROVIDERS[n].api_key]


def _extract_json(text):
    """Model bazen ```json ... ``` ya da açıklama ekler; ilk JSON nesnesini ayıkla."""
    if not text:
        raise ValueError("Empty response")
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced:
        text = fenced.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _call(provider, messages, temperature, max_tokens):
    kwargs = dict(
        model=provider.model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if provider.supports_json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        resp = provider.client.chat.completions.create(**kwargs)
    except APIStatusError as e:
        # Bazı ücretsiz modeller json_object desteklemiyor -> bir kez onsuz dene
        if e.status_code == 400 and provider.supports_json_mode and "response_format" in str(e).lower():
            provider.supports_json_mode = False
            return _call(provider, messages, temperature, max_tokens)
        raise
    return resp.choices[0].message.content


def _retry_after(err):
    """429 yanıtından kaç saniye beklenmesi gerektiğini çıkar (header ya da mesaj)."""
    try:
        value = err.response.headers.get("retry-after")
        if value:
            return float(value)
    except (AttributeError, ValueError):
        pass
    # Groq: "Please try again in 4.53s" / "in 1m2.5s"
    m = re.search(r"try again in (?:(\d+)m)?([\d.]+)s", str(err))
    if m:
        return int(m.group(1) or 0) * 60 + float(m.group(2))
    return None


def complete_json(system_prompt, messages, temperature=0.3, max_tokens=1200, required_keys=()):
    """
    Sağlayıcıları sırayla dener, ilk geçerli JSON yanıtını döndürür.
    Hepsi kota hatası verirse ve en kısa bekleme süresi MAX_INLINE_WAIT'ten azsa
    bir kez bekleyip yeniden dener.
    Dönen değer: (data: dict, provider_name: str)
    """
    providers = active_providers()
    if not providers:
        raise AIUnavailable(
            "Hiçbir AI anahtarı tanımlı değil. .env dosyasına en az bir sağlayıcı anahtarı ekle."
        )

    full_messages = [{"role": "system", "content": system_prompt}, *messages]
    errors = []

    for attempt in range(2):
        now = time.time()
        # Soğumada olmayanlar önce; hepsi soğumadaysa yine de sırayla dene
        ready = [p for p in providers if p.cooldown_until <= now]
        queue = ready or providers

        all_rate_limited, shortest_wait = True, None
        for provider in queue:
            try:
                text = _call(provider, full_messages, temperature, max_tokens)
                data = _extract_json(text)
                missing = [k for k in required_keys if k not in data]
                if missing:
                    raise ValueError(f"missing keys {missing}")
                return data, provider.name
            except APIStatusError as e:
                if e.status_code == 429:
                    wait = _retry_after(e) or COOLDOWN_RATE_LIMIT
                    provider.cooldown_until = time.time() + wait
                    shortest_wait = wait if shortest_wait is None else min(shortest_wait, wait)
                else:
                    all_rate_limited = False
                    if e.status_code >= 500:
                        provider.cooldown_until = time.time() + COOLDOWN_SERVER_ERROR
                errors.append(f"{provider.name}: HTTP {e.status_code}")
            except (APIConnectionError, APITimeoutError) as e:
                all_rate_limited = False
                provider.cooldown_until = time.time() + COOLDOWN_SERVER_ERROR
                errors.append(f"{provider.name}: {type(e).__name__}")
            except (ValueError, json.JSONDecodeError) as e:
                all_rate_limited = False
                errors.append(f"{provider.name}: invalid JSON ({e})")
            print(f"[ai] {errors[-1]}")

        # Sadece kota sorunu varsa ve kısa sürede açılacaksa bekle, bir kez daha dene
        if attempt == 0 and all_rate_limited and shortest_wait is not None and shortest_wait <= MAX_INLINE_WAIT:
            print(f"[ai] rate limited, retrying in {shortest_wait:.1f}s")
            time.sleep(shortest_wait + 0.3)
            continue
        break

    raise AIUnavailable("; ".join(errors), rate_limited=all_rate_limited)
