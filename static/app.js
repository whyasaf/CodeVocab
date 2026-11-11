/* ════════════════════════════════════════════════════════════
   CodeVocab — chat client
   Tüm sohbetler ve öğrenilen kelimeler localStorage'da tutulur.
   ════════════════════════════════════════════════════════════ */
(() => {
  "use strict";

  const STORE_CHATS = "cv_chats_v1";
  const STORE_KNOWN = "cv_known_words"; // eski sürümle uyumlu anahtar
  const STORE_THEME = "cv_theme";
  const STORE_COLLAPSED = "cv_sidebar_collapsed";
  const STORE_TOPICS = "cv_topics"; // { "present perfect": { name, level, best, last, attempts, updatedAt } }
  const MAX_CHATS = 150;
  const MAX_LEN = 500;
  const HISTORY_FOR_API = 8;

  const SUGGESTIONS = {
    analyze: [
      { icon: "clock", title: "I have seen this movie two days ago", sub: "Tense hatası var mı?" },
      { icon: "flag", title: "We should discuss about the plan", sub: "Türkçe kalıp tuzağı" },
      { icon: "chat", title: "Present perfect ne zaman kullanılır?", sub: "Mentora soru sor" },
      { icon: "dice", title: "Rastgele 5 kelime getir", sub: "Kelime avına başla", mode: "word", random: true },
    ],
    word: [
      { icon: "dice", title: "Rastgele 5 kelime", sub: "Havuzdan sürpriz seçki", random: true },
      { icon: "book", title: "although", sub: "Sık kullanılan bağlaç" },
      { icon: "book", title: "awkward", sub: "Günlük konuşmanın favorisi" },
      { icon: "book", title: "nevertheless", sub: "Resmi bağlaç" },
    ],
  };

  // Konu kataloğu: "günün kalıbı" ve öneriler buradan seçilir. Kullanıcı istediği konuyu da yazabilir.
  const TOPICS = [
    { name: "Present Simple vs Present Continuous", tr: "Geniş zaman mı, şimdiki zaman mı?", level: "A2" },
    { name: "Present Perfect", tr: "Geçmişte olup etkisi süren", level: "B1" },
    { name: "Present Perfect vs Past Simple", tr: "'ago' ile asla have/has", level: "B1" },
    { name: "Present Perfect Continuous", tr: "since / for ile süren işler", level: "B1" },
    { name: "Past Continuous", tr: "Tam o sırada ne oluyordu?", level: "A2" },
    { name: "will vs going to", tr: "Gelecek planı mı, anlık karar mı?", level: "A2" },
    { name: "Present Continuous for future plans", tr: "We're meeting on Friday", level: "B1" },
    { name: "should / must / have to", tr: "Zorunluluk ve tavsiye", level: "A2" },
    { name: "could / would / might for politeness", tr: "Kibar rica ve öneri", level: "B1" },
    { name: "First Conditional", tr: "If + present, will", level: "A2" },
    { name: "Second Conditional", tr: "Hayali durumlar", level: "B1" },
    { name: "Third Conditional", tr: "Geçmişe dair pişmanlık", level: "B2" },
    { name: "Passive Voice", tr: "The bug was fixed", level: "B1" },
    { name: "Relative Clauses: who / which / that", tr: "Cümleleri bağlamak", level: "B1" },
    { name: "Articles: a / an / the", tr: "Türkçede olmayan zor konu", level: "A2" },
    { name: "Countable vs Uncountable nouns", tr: "much / many, information, feedback", level: "A2" },
    { name: "Prepositions of time: in / on / at", tr: "Saat, gün, ay", level: "A2" },
    { name: "Prepositions after verbs", tr: "depend on, discuss (edatsız!)", level: "B1" },
    { name: "Gerund vs Infinitive", tr: "enjoy doing / want to do", level: "B1" },
    { name: "used to / be used to / get used to", tr: "Eski alışkanlık mı, alışmak mı?", level: "B1" },
    { name: "make vs do", tr: "make a decision, do a review", level: "A2" },
    { name: "say vs tell", tr: "tell someone, say something", level: "A2" },
    { name: "Reported Speech", tr: "He said that…", level: "B1" },
    { name: "Comparatives and Superlatives", tr: "faster, the most reliable", level: "A2" },
    { name: "Phrasal verbs at work", tr: "roll back, set up, figure out", level: "B1" },
    { name: "Indirect Questions", tr: "Could you tell me where…?", level: "B1" },
    { name: "since vs for", tr: "Başlangıç noktası mı, süre mi?", level: "A2" },
    { name: "already / yet / still", tr: "Zaten, henüz, hâlâ", level: "A2" },
    { name: "however / although / despite", tr: "Zıtlık bağlaçları", level: "B1" },
    { name: "some / any / no", tr: "Olumlu, olumsuz, soru", level: "A2" },
    { name: "too vs enough", tr: "too slow / fast enough", level: "A2" },
    { name: "wish / if only", tr: "Keşke cümleleri", level: "B2" },
    { name: "Causative: have / get something done", tr: "Bir işi yaptırmak", level: "B2" },
    { name: "Question Tags", tr: "It works, doesn't it?", level: "B1" },
    { name: "Polite phrases for work emails", tr: "I'd like to, Would you mind…", level: "B1" },
    { name: "Modal verbs of deduction: must / might / can't", tr: "Tahmin ve çıkarım", level: "B2" },
  ];

  /** Günün kalıbı: tarihe göre her gün değişir, gün içinde sabit kalır. */
  function dayIndex(offset = 0) {
    const d = new Date();
    const days = Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 864e5);
    return (days + offset) % TOPICS.length;
  }
  const dailyTopic = () => TOPICS[dayIndex()];

  function topicSuggestions() {
    const daily = dailyTopic();
    const studied = studiedTopics();
    // Bugünün konusu + henüz çalışılmamış konulardan gün bazlı 3 öneri
    const pool = TOPICS.filter((t) => t !== daily && !studied[t.name.toLowerCase()]);
    const list = pool.length >= 3 ? pool : TOPICS.filter((t) => t !== daily);
    const start = dayIndex() % list.length;
    const picks = [0, 7, 14].map((k) => list[(start + k) % list.length]);
    return [
      { icon: "sun", title: `Günün kalıbı: ${daily.name}`, sub: `${daily.level} · ${daily.tr}`, topic: daily.name },
      ...picks.map((t) => ({ icon: "cap", title: t.name, sub: `${t.level} · ${t.tr}`, topic: t.name })),
    ];
  }

  const HERO_SUB = {
    analyze: "İngilizce cümleni yaz, bir mentor gibi düzeltelim.<br />Takıldığın yeri sor, sohbet ederek öğren.",
    word: "Bir kelime yaz ya da rastgele seçki iste.<br />Anlamı, telaffuzu ve üç seviyede örnek cümlesi hazır.",
    topic: "Bir gramer konusu ya da kalıp yaz, ders kartını hazırlayayım.<br />Sonra 5 soruluk mini quiz ile kendini dene.",
  };

  const FOLLOWUPS = ["Neden böyle?", "Daha resmi nasıl yazarım?", "Benzer bir örnek ver"];

  // ───────────────────────── helpers ─────────────────────────

  const $ = (sel, root = document) => root.querySelector(sel);
  const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);

  const store = {
    get(key, fallback) {
      try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
      } catch {
        return fallback;
      }
    },
    set(key, value) {
      try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
      } catch {
        toast("Tarayıcı depolama alanı dolu ya da kapalı.");
        return false;
      }
    },
  };

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  }

  /** AI metnini güvenli HTML'e çevirir: sadece b/strong/i/em/code etiketlerine izin verir. */
  function rich(text) {
    let s = String(text ?? "").replace(/\\n/g, "\n").trim();
    s = escapeHtml(s)
      .replace(/&lt;(\/?)(b|strong|i|em|code)&gt;/gi, "<$1$2>")
      .replace(/&lt;br\s*\/?&gt;/gi, "\n")
      .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
    return s
      .split(/\n{2,}/)
      .map((p) => `<p>${p.replace(/\n/g, "<br>")}</p>`)
      .join("");
  }

  function stripTags(s) {
    return String(s ?? "").replace(/<[^>]+>/g, "").replace(/\\n/g, " ");
  }

  function el(html) {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }

  function toast(message) {
    const stack = $("#toast-stack");
    const node = el(`<div class="toast">${escapeHtml(message)}</div>`);
    stack.appendChild(node);
    requestAnimationFrame(() => node.classList.add("visible"));
    setTimeout(() => {
      node.classList.remove("visible");
      setTimeout(() => node.remove(), 250);
    }, 3200);
  }

  async function api(url, options = {}) {
    let res;
    try {
      res = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options,
      });
    } catch {
      throw new Error("Sunucuya ulaşılamadı. İnternet bağlantını kontrol et.");
    }
    let body = null;
    try {
      body = await res.json();
    } catch {
      /* boş/HTML yanıt */
    }
    if (!res.ok || (body && body.error)) {
      throw new Error((body && body.error) || `Sunucu hatası (${res.status}).`);
    }
    return body;
  }

  /** Kelime bazlı fark: orijinal → düzeltilmiş. Büyük/küçük harf ve noktalama yok sayılır. */
  function wordDiff(a, b) {
    const A = a.split(/\s+/).filter(Boolean);
    const B = b.split(/\s+/).filter(Boolean);
    if (A.length > 120 || B.length > 120) return null;
    const norm = (w) => w.toLowerCase().replace(/[.,!?;:"“”'’]+$/g, "").replace(/^["“'‘]+/, "");
    const n = A.length, m = B.length;
    const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
    for (let i = n - 1; i >= 0; i--)
      for (let j = m - 1; j >= 0; j--)
        dp[i][j] = norm(A[i]) === norm(B[j]) ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    // ops: [tür, kelime] — tür: "=" aynı, "-" silinen, "+" eklenen
    const ops = [];
    let i = 0, j = 0;
    while (i < n && j < m) {
      if (norm(A[i]) === norm(B[j])) ops.push(["=", B[j]]), i++, j++;
      else if (dp[i + 1][j] >= dp[i][j + 1]) ops.push(["-", A[i++]]);
      else ops.push(["+", B[j++]]);
    }
    while (i < n) ops.push(["-", A[i++]]);
    while (j < m) ops.push(["+", B[j++]]);
    if (!ops.some((o) => o[0] !== "=")) return null;

    // Art arda gelen aynı türdeki kelimeleri tek parça yap: "have been" iki kutu değil, bir kutu
    const out = [];
    for (let k = 0; k < ops.length; ) {
      const type = ops[k][0];
      const words = [];
      while (k < ops.length && ops[k][0] === type) words.push(escapeHtml(ops[k++][1]));
      const text = words.join(" ");
      out.push(type === "=" ? text : `<span class="diff-${type === "-" ? "del" : "add"}">${text}</span>`);
    }
    return out.join(" ");
  }

  // ───────────────────────── speech ─────────────────────────

  let voice = null;
  function pickVoice() {
    if (!("speechSynthesis" in window)) return;
    const voices = speechSynthesis.getVoices();
    voice =
      voices.find((v) => v.lang === "en-US" && /Samantha|Google US|Aria|Jenny/i.test(v.name)) ||
      voices.find((v) => v.lang === "en-US") ||
      voices.find((v) => v.lang.startsWith("en")) ||
      null;
  }
  if ("speechSynthesis" in window) {
    pickVoice();
    speechSynthesis.onvoiceschanged = pickVoice;
  }

  function speak(text, btn) {
    if (!("speechSynthesis" in window)) return toast("Tarayıcın sesli okumayı desteklemiyor.");
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US";
    u.rate = 0.92;
    if (voice) u.voice = voice;
    if (btn) {
      btn.classList.add("speaking");
      u.onend = u.onerror = () => btn.classList.remove("speaking");
    }
    speechSynthesis.speak(u);
  }

  // ───────────────────────── state ─────────────────────────

  const state = {
    chats: store.get(STORE_CHATS, []),
    currentId: null,
    mode: "analyze",
    busy: false,
    search: "",
  };
  if (!Array.isArray(state.chats)) state.chats = [];

  const knownWords = () => {
    const w = store.get(STORE_KNOWN, []);
    return Array.isArray(w) ? w : [];
  };
  const isKnown = (word) => knownWords().includes(word.toLowerCase());
  function setKnown(word, known) {
    word = word.toLowerCase();
    const list = knownWords().filter((w) => w !== word);
    if (known) list.push(word);
    store.set(STORE_KNOWN, list);
    updateLearnedCount();
  }

  function studiedTopics() {
    const t = store.get(STORE_TOPICS, {});
    return t && typeof t === "object" && !Array.isArray(t) ? t : {};
  }

  function saveTopicResult(lesson, score, total) {
    const all = studiedTopics();
    const key = lesson.topic.toLowerCase();
    const prev = all[key] || { attempts: 0, best: 0 };
    const pct = Math.round((score / total) * 100);
    all[key] = {
      name: lesson.topic,
      name_tr: lesson.topic_tr || "",
      level: lesson.level || "",
      best: Math.max(prev.best || 0, pct),
      last: pct,
      attempts: (prev.attempts || 0) + 1,
      updatedAt: Date.now(),
    };
    store.set(STORE_TOPICS, all);
    updateLearnedCount();
  }

  // ── Quiz cevap kontrolü ──
  const CONTRACTIONS = [
    [/\bwon't\b/g, "will not"],
    [/\bcan't\b/g, "can not"],
    [/\bcannot\b/g, "can not"],
    [/\bshan't\b/g, "shall not"],
    [/n't\b/g, " not"],
    [/'ve\b/g, " have"],
    [/'re\b/g, " are"],
    [/'ll\b/g, " will"],
    [/'m\b/g, " am"],
  ];

  function normAnswer(s) {
    let x = String(s ?? "")
      .toLowerCase()
      .replace(/[’‘`]/g, "'")
      .replace(/[.!?,;:"]+$/g, "")
      .replace(/\s+/g, " ")
      .trim();
    for (const [re, rep] of CONTRACTIONS) x = x.replace(re, rep);
    return x.replace(/\s+/g, " ").trim();
  }

  function isFillCorrect(q, value) {
    const given = normAnswer(value);
    if (!given) return false;
    return [q.answer, ...(q.accept || [])].some((a) => normAnswer(a) === given);
  }

  const quizDone = (quiz) => quiz.every((q) => q.user != null);
  const quizScore = (quiz) => quiz.filter((q) => q.ok).length;

  function quizSummaryForApi(topic, quiz) {
    const wrong = quiz.filter((q) => q.user != null && !q.ok);
    const head = `"${topic}" quiz: ${quizScore(quiz)}/${quiz.length} doğru.`;
    if (!wrong.length) return head;
    return `${head} Yanlışlar: ${wrong.map((q) => `"${q.q}" → "${q.user}" (doğrusu "${q.answer}")`).join("; ")}`;
  }

  const currentChat = () => state.chats.find((c) => c.id === state.currentId) || null;

  function saveChats() {
    state.chats.sort((a, b) => b.updatedAt - a.updatedAt);
    if (state.chats.length > MAX_CHATS) state.chats.length = MAX_CHATS;
    store.set(STORE_CHATS, state.chats);
  }

  function ensureChat(titleSeed) {
    let chat = currentChat();
    if (!chat) {
      chat = {
        id: uid(),
        title: titleSeed.slice(0, 60) || "Yeni sohbet",
        createdAt: Date.now(),
        updatedAt: Date.now(),
        messages: [],
      };
      state.chats.unshift(chat);
      state.currentId = chat.id;
    }
    return chat;
  }

  function pushMessage(msg) {
    const chat = currentChat();
    msg.id = msg.id || uid();
    chat.messages.push(msg);
    chat.updatedAt = Date.now();
    saveChats();
    renderAll();
    return msg;
  }

  function removeMessage(id) {
    const chat = currentChat();
    if (!chat) return;
    chat.messages = chat.messages.filter((m) => m.id !== id);
    saveChats();
  }

  /** Modelin bağlamı için son mesajları sadeleştirilmiş metne çevirir. */
  function historyForApi(chat) {
    const items = [];
    for (const m of chat.messages) {
      if (m.role === "user") items.push({ role: "user", content: m.text });
      else if (m.kind === "analysis")
        items.push({
          role: "assistant",
          content: `Puan: ${m.data.score}/100. Düzeltilmiş: "${m.data.corrected_sentence}". Açıklama: ${stripTags(m.data.explanation)}`,
        });
      else if (m.kind === "reply") items.push({ role: "assistant", content: stripTags(m.data.text) });
      else if (m.kind === "word")
        items.push({ role: "assistant", content: `"${m.data.word}" kelime kartı: ${m.data.meaning_tr}. Örnek: ${m.data.sentences?.B1 || ""}` });
      else if (m.kind === "lesson") {
        const L = m.data.lesson;
        items.push({
          role: "assistant",
          content: `"${L.topic}" konusu anlatıldı. Özet: ${stripTags(L.summary)} Formül: ${L.formula.join(" | ")}`,
        });
        if (m.data.quiz.some((q) => q.user != null)) items.push({ role: "assistant", content: quizSummaryForApi(L.topic, m.data.quiz) });
      } else if (m.kind === "quiz" && m.data.quiz.some((q) => q.user != null))
        items.push({ role: "assistant", content: quizSummaryForApi(m.data.topic, m.data.quiz) });
    }
    return items.slice(-HISTORY_FOR_API);
  }

  // ───────────────────────── rendering ─────────────────────────

  const ui = {
    app: $("#app"),
    list: $("#chat-list"),
    messages: $("#messages"),
    thread: $("#thread"),
    input: $("#input"),
    send: $("#send-btn"),
    charCount: $("#char-count"),
    random: $("#random-btn"),
    title: $("#topbar-title"),
    suggestions: $("#suggestions"),
    learnedCount: $("#learned-count"),
    learnedModal: $("#learned-modal"),
    learnedBody: $("#learned-body"),
    themeLabel: $("#theme-label"),
  };

  function groupLabel(ts) {
    const d = new Date(ts);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diff = (today - new Date(d.getFullYear(), d.getMonth(), d.getDate())) / 864e5;
    if (diff <= 0) return "Bugün";
    if (diff === 1) return "Dün";
    if (diff < 7) return "Son 7 gün";
    if (diff < 30) return "Son 30 gün";
    return "Daha eski";
  }

  function renderSidebar() {
    const q = state.search.trim().toLowerCase();
    const chats = state.chats.filter(
      (c) =>
        !q ||
        c.title.toLowerCase().includes(q) ||
        c.messages.some((m) => m.role === "user" && m.text.toLowerCase().includes(q)),
    );
    if (!chats.length) {
      ui.list.innerHTML = `<p class="chat-list-empty">${q ? "Sonuç bulunamadı." : "Henüz sohbet yok. İlk cümleni yaz!"}</p>`;
      return;
    }
    let html = "";
    let lastGroup = "";
    for (const c of chats) {
      const g = groupLabel(c.updatedAt);
      if (g !== lastGroup) {
        html += `<div class="chat-group-label">${g}</div>`;
        lastGroup = g;
      }
      html += `
        <div class="chat-item ${c.id === state.currentId ? "active" : ""}">
          <button class="chat-item-link" data-action="open-chat" data-id="${c.id}" title="${escapeHtml(c.title)}">${escapeHtml(c.title)}</button>
          <button class="chat-item-del" data-action="delete-chat" data-id="${c.id}" aria-label="Sohbeti sil">
            <svg viewBox="0 0 24 24" width="14" height="14"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14" /></svg>
          </button>
        </div>`;
    }
    ui.list.innerHTML = html;
  }

  const ICON = {
    speaker: `<svg viewBox="0 0 24 24" width="15" height="15"><path d="M11 5 6 9H2v6h4l5 4V5Z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14"/></svg>`,
    copy: `<svg viewBox="0 0 24 24" width="15" height="15"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>`,
    check: `<svg viewBox="0 0 24 24" width="15" height="15"><path d="M20 6 9 17l-5-5"/></svg>`,
    bulb: `<svg viewBox="0 0 24 24" width="16" height="16"><path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2Z"/></svg>`,
    dice: `<svg viewBox="0 0 24 24" width="14" height="14"><rect x="3" y="3" width="18" height="18" rx="4"/><circle cx="8.5" cy="8.5" r="1.2"/><circle cx="15.5" cy="15.5" r="1.2"/></svg>`,
    pen: `<svg viewBox="0 0 24 24" width="14" height="14"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>`,
    retry: `<svg viewBox="0 0 24 24" width="14" height="14"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>`,
    clock: `<svg viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>`,
    flag: `<svg viewBox="0 0 24 24" width="16" height="16"><path d="M4 21V4h11l-1 4h6v9H9l1-4H4"/></svg>`,
    chat: `<svg viewBox="0 0 24 24" width="16" height="16"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12Z"/></svg>`,
    book: `<svg viewBox="0 0 24 24" width="16" height="16"><path d="M4 19.5V5a2 2 0 0 1 2-2h13v16H6.5A2.5 2.5 0 0 0 4 21.5Z"/></svg>`,
    cap: `<svg viewBox="0 0 24 24" width="16" height="16"><path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/></svg>`,
    sun: `<svg viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>`,
    x: `<svg viewBox="0 0 24 24" width="15" height="15"><path d="M18 6 6 18M6 6l12 12"/></svg>`,
    warn: `<svg viewBox="0 0 24 24" width="16" height="16"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>`,
    link: `<svg viewBox="0 0 24 24" width="16" height="16"><path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/></svg>`,
    scale: `<svg viewBox="0 0 24 24" width="16" height="16"><path d="M12 3v18M5 7h14M5 7l-3 7a4 4 0 0 0 6 0L5 7Zm14 0-3 7a4 4 0 0 0 6 0l-3-7Z"/></svg>`,
  };

  function scoreInfo(score) {
    if (score >= 95) return { label: "Mükemmel", color: "var(--good)", sub: "Native speaker böyle yazar." };
    if (score >= 80) return { label: "Gayet iyi", color: "var(--info)", sub: "Küçük bir dokunuş yeterli." };
    if (score >= 60) return { label: "Geliştirilebilir", color: "var(--warn)", sub: "Önemli bir hata var." };
    return { label: "Tekrar dene", color: "var(--bad)", sub: "Cümlenin yapısı bozulmuş." };
  }

  function renderAnalysis(m, isLast) {
    const d = m.data;
    const info = scoreInfo(d.score);
    const C = 2 * Math.PI * 24;
    const diff = d.original && d.score < 100 ? wordDiff(d.original, d.corrected_sentence) : null;
    return `
      <div class="card" style="--score-color:${info.color};--circ:${C}">
        <div class="card-section score-row">
          <div class="score-ring">
            <svg viewBox="0 0 56 56"><circle class="track" cx="28" cy="28" r="24"/><circle class="bar" cx="28" cy="28" r="24"
              stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - d.score / 100)}"/></svg>
            <b>${d.score}</b>
          </div>
          <div class="score-meta">
            <span class="score-status">${info.label}</span>
            <span class="score-sub">${info.sub}</span>
          </div>
        </div>
        ${
          d.corrected_sentence
            ? `<div class="card-section">
                <p class="label">${d.score >= 100 ? "Cümlen" : "Doğrusu"}</p>
                <div class="corrected">
                  <span class="corrected-text">${diff || escapeHtml(d.corrected_sentence)}</span>
                  <span class="mini-actions">
                    <button class="mini-btn" data-action="speak" data-text="${escapeHtml(d.corrected_sentence)}" aria-label="Dinle">${ICON.speaker}</button>
                    <button class="mini-btn" data-action="copy" data-text="${escapeHtml(d.corrected_sentence)}" aria-label="Kopyala">${ICON.copy}</button>
                  </span>
                </div>
              </div>`
            : ""
        }
        ${d.explanation ? `<div class="card-section"><p class="label">Mentor notu</p><div class="explanation">${rich(d.explanation)}</div></div>` : ""}
        ${d.motivation ? `<div class="card-section motivation">${escapeHtml(stripTags(d.motivation))}</div>` : ""}
      </div>
      ${isLast ? followupChips() : ""}`;
  }

  function followupChips() {
    return `<div class="followups">${FOLLOWUPS.map(
      (f) => `<button class="chip" data-action="followup" data-text="${escapeHtml(f)}">${escapeHtml(f)}</button>`,
    ).join("")}</div>`;
  }

  function renderWord(m) {
    const d = m.data;
    const known = isKnown(d.word);
    const levels = ["A1", "B1", "C1"]
      .filter((l) => d.sentences?.[l])
      .map(
        (l) => `
        <div class="level-row">
          <span class="level-badge ${l}">${l}</span>
          <span class="level-text">${escapeHtml(d.sentences[l])}</span>
          <button class="mini-btn" data-action="speak" data-text="${escapeHtml(d.sentences[l])}" aria-label="Dinle">${ICON.speaker}</button>
        </div>`,
      )
      .join("");
    return `
      <div class="card">
        <div class="card-section word-hero">
          <div class="word-head">
            <div>
              <h3 class="word-title">${escapeHtml(d.word)}</h3>
              <div class="word-sub">
                ${d.phonetic ? `<span class="mono">${escapeHtml(d.phonetic)}</span>` : ""}
                ${d.part_of_speech ? `<span class="pos-pill">${escapeHtml(d.part_of_speech)}</span>` : ""}
              </div>
            </div>
            <button class="mini-btn speak-lg" data-action="speak" data-text="${escapeHtml(d.word)}" aria-label="Telaffuzu dinle">${ICON.speaker}</button>
          </div>
          <div class="meaning">${escapeHtml(d.meaning_tr)}</div>
        </div>
        ${levels ? `<div class="card-section levels">${levels}</div>` : ""}
        ${d.tip ? `<div class="card-section tip">${ICON.bulb}<span>${escapeHtml(d.tip)}</span></div>` : ""}
        <div class="card-section card-actions">
          <button class="btn ${known ? "is-known" : "btn-primary"}" data-action="toggle-known" data-word="${escapeHtml(d.word)}">
            ${ICON.check} ${known ? "Öğrenildi" : "Biliyorum"}
          </button>
          <button class="btn btn-outline" data-action="practice" data-word="${escapeHtml(d.word)}">${ICON.pen} Cümle kur</button>
          <button class="btn btn-outline" data-action="random-words">${ICON.dice} Yeni kelimeler</button>
        </div>
      </div>`;
  }

  // ───────── Konu: ders kartı + quiz ─────────

  function speakBtn(text) {
    return `<button class="mini-btn" data-action="speak" data-text="${escapeHtml(text)}" aria-label="Dinle">${ICON.speaker}</button>`;
  }

  /** Model metninde <b> dışında etiket olmasın; satır içi güvenli HTML */
  const inline = (s) => rich(s).replace(/^<p>|<\/p>$/g, "").replace(/<\/p><p>/g, "<br><br>");

  function renderLesson(m) {
    const L = m.data.lesson;
    const uses = L.uses
      .map(
        (u) => `
        <div class="use">
          <p class="use-title">${escapeHtml(u.title)}</p>
          <p class="use-text">${inline(u.text)}</p>
          ${
            u.en
              ? `<div class="example">
                  <div class="example-body"><span class="example-en">${escapeHtml(u.en)}</span>${u.tr ? `<span class="example-tr">${escapeHtml(u.tr)}</span>` : ""}</div>
                  ${speakBtn(u.en)}
                </div>`
              : ""
          }
        </div>`,
      )
      .join("");
    const traps = L.traps
      .map(
        (t) => `
        <div class="trap">
          <div class="trap-row bad">${ICON.x}<span>${escapeHtml(t.wrong)}</span></div>
          <div class="trap-row good">${ICON.check}<span>${escapeHtml(t.right)}</span></div>
          ${t.why ? `<p class="trap-why">${inline(t.why)}</p>` : ""}
        </div>`,
      )
      .join("");
    const c = L.compare;
    return `
      <div class="card lesson">
        <div class="card-section lesson-hero">
          <div class="lesson-meta">
            ${L.level ? `<span class="level-pill">${escapeHtml(L.level)}</span>` : ""}
            ${L.topic_tr ? `<span>${escapeHtml(L.topic_tr)}</span>` : ""}
          </div>
          <h3 class="lesson-title">${escapeHtml(L.topic)}</h3>
          <div class="lesson-summary">${rich(L.summary)}</div>
        </div>
        ${
          L.formula.length
            ? `<div class="card-section"><p class="label">Formül</p><div class="formula">${L.formula
                .map((f) => `<code>${escapeHtml(f)}</code>`)
                .join("\n")}</div></div>`
            : ""
        }
        ${uses ? `<div class="card-section"><p class="label">Ne zaman kullanılır?</p><div class="uses">${uses}</div></div>` : ""}
        ${
          L.turkish_link
            ? `<div class="card-section lesson-callout">${ICON.link}<div><p class="label">Türkçe ile karşılaştır</p><div>${rich(L.turkish_link)}</div></div></div>`
            : ""
        }
        ${traps ? `<div class="card-section"><p class="label">Türklerin düştüğü tuzaklar</p><div class="traps">${traps}</div></div>` : ""}
        ${
          c
            ? `<div class="card-section"><p class="label">${escapeHtml(c.with)} ile farkı</p>
                <div class="compare-text">${rich(c.text)}</div>
                <div class="compare-pair">
                  ${c.a ? `<div class="compare-item"><span class="compare-tag">${escapeHtml(L.topic)}</span>${escapeHtml(c.a)}</div>` : ""}
                  ${c.b ? `<div class="compare-item"><span class="compare-tag">${escapeHtml(c.with)}</span>${escapeHtml(c.b)}</div>` : ""}
                </div></div>`
            : ""
        }
        ${
          L.signal_words.length
            ? `<div class="card-section"><p class="label">Sinyal kelimeler</p><div class="signal-words">${L.signal_words
                .map((w) => `<span>${escapeHtml(w)}</span>`)
                .join("")}</div></div>`
            : ""
        }
        ${L.tip ? `<div class="card-section tip">${ICON.bulb}<span>${inline(L.tip)}</span></div>` : ""}
      </div>`;
  }

  function quizTopic(m) {
    return m.kind === "lesson" ? m.data.lesson.topic : m.data.topic;
  }

  function renderBlank(q) {
    const parts = escapeHtml(q.q).split("___");
    if (parts.length < 2) return escapeHtml(q.q);
    let fill = `<span class="blank"></span>`;
    if (q.user != null) {
      fill = q.ok
        ? `<span class="blank filled ok">${escapeHtml(q.type === "fill" ? q.user : q.answer)}</span>`
        : `<span class="blank filled bad"><s>${escapeHtml(q.user)}</s> ${escapeHtml(q.answer)}</span>`;
    }
    return parts[0] + fill + parts.slice(1).join("___");
  }

  function renderQuestion(m, i) {
    const q = m.data.quiz[i];
    const answered = q.user != null;
    let body = "";
    if (q.type === "choice") {
      body = `<div class="quiz-options">${q.options
        .map((o, oi) => {
          let cls = "";
          if (answered) {
            if (o === q.answer) cls = "correct";
            else if (o === q.user) cls = "wrong";
            else cls = "dim";
          }
          return `<button class="quiz-option ${cls}" data-action="quiz-choice" data-mid="${m.id}" data-qi="${i}" data-oi="${oi}" ${answered ? "disabled" : ""}>
              <span class="opt-key">${String.fromCharCode(65 + oi)}</span><span>${escapeHtml(o)}</span></button>`;
        })
        .join("")}</div>`;
    } else if (!answered) {
      body = `<form class="quiz-fill" data-mid="${m.id}" data-qi="${i}">
          <input type="text" name="answer" placeholder="Boşluğa ne gelmeli?" autocomplete="off" autocapitalize="off" spellcheck="false" maxlength="60" aria-label="Cevap" />
          <button type="submit" class="btn btn-primary">Kontrol et</button>
        </form>`;
    }
    const feedback = answered
      ? `<div class="quiz-feedback ${q.ok ? "ok" : "bad"}">
          <span class="fb-icon">${q.ok ? ICON.check : ICON.x}</span>
          <div>
            <b>${q.ok ? "Doğru!" : `Doğrusu: ${escapeHtml(q.answer)}`}</b>
            ${q.explain ? `<span>${inline(q.explain)}</span>` : ""}
            ${
              !q.ok
                ? `<button class="link-btn" data-action="quiz-dispute" data-mid="${m.id}" data-qi="${i}">Benim cevabım da doğru olabilir mi? Mentora sor →</button>`
                : ""
            }
          </div>
        </div>`
      : "";
    return `
      <div class="quiz-q ${answered ? (q.ok ? "is-ok" : "is-bad") : ""}" data-qid="${m.id}-${i}">
        <div class="quiz-q-head">
          <span class="quiz-num">${i + 1}</span>
          <span class="quiz-type">${q.type === "choice" ? "Doğru seçeneği bul" : "Boşluğu doldur"}</span>
        </div>
        <p class="quiz-text">${renderBlank(q)}</p>
        ${body}
        ${feedback}
      </div>`;
  }

  function renderQuizFoot(m) {
    const quiz = m.data.quiz;
    if (!quizDone(quiz)) {
      const n = quiz.filter((q) => q.user != null).length;
      return `<div class="quiz-foot pending" data-foot="${m.id}">
          <div class="quiz-progress"><span style="width:${(n / quiz.length) * 100}%"></span></div>
          <span class="quiz-progress-label">${n}/${quiz.length} cevaplandı</span>
        </div>`;
    }
    const score = quizScore(quiz);
    const pct = score / quiz.length;
    const msg =
      pct === 1 ? "Kusursuz! Bu kalıp artık senin. 🎯" : pct >= 0.6 ? "İyi gidiyor, yanlışlara bir kez daha göz at. 💪" : "Dersi bir kez daha oku, sonra yeni sorularla dene. 📚";
    const topic = quizTopic(m);
    return `<div class="quiz-foot done" data-foot="${m.id}" style="--score-color:${pct === 1 ? "var(--good)" : pct >= 0.6 ? "var(--info)" : "var(--warn)"}">
        <div class="quiz-result">
          <b>${score}<small>/${quiz.length}</small></b>
          <span>${msg}</span>
        </div>
        <div class="card-actions">
          <button class="btn btn-primary" data-action="quiz-more" data-mid="${m.id}">${ICON.retry} Yeni sorular</button>
          <button class="btn btn-outline" data-action="topic-ask" data-topic="${escapeHtml(topic)}">${ICON.chat} Soru sor</button>
          <button class="btn btn-outline" data-action="topic-new">${ICON.cap} Başka konu</button>
        </div>
      </div>`;
  }

  function renderQuiz(m) {
    const quiz = m.data.quiz;
    return `
      <div class="card quiz">
        <div class="card-section quiz-head">
          <div>
            <p class="label">Mini quiz</p>
            <h4>${escapeHtml(quizTopic(m))}</h4>
          </div>
          <span class="quiz-count">${quiz.length} soru</span>
        </div>
        <div class="quiz-list">${quiz.map((_, i) => renderQuestion(m, i)).join("")}</div>
        ${renderQuizFoot(m)}
      </div>`;
  }

  function renderPicker(m) {
    const words = m.data.words || [];
    if (!words.length) return `<div class="reply-text"><p>Tebrikler, havuzdaki tüm kelimeleri öğrenmişsin! 🎉</p></div>`;
    return `
      <div class="word-picker">
        <p>Birini seç, kartını hazırlayayım:</p>
        <div class="word-chips">${words
          .map((w) => `<button class="word-chip" data-action="pick-word" data-word="${escapeHtml(w)}">${escapeHtml(w)}</button>`)
          .join("")}</div>
      </div>`;
  }

  function renderMessage(m, isLast) {
    if (m.role === "user") {
      return `<div class="msg msg-user${fresh(m)}"><div class="bubble-user">${escapeHtml(m.text)}</div></div>`;
    }
    let body = "";
    if (m.kind === "analysis") body = renderAnalysis(m, isLast);
    else if (m.kind === "reply") body = `<div class="reply-text">${rich(m.data.text)}</div>${isLast ? followupChips() : ""}`;
    else if (m.kind === "word") body = renderWord(m);
    else if (m.kind === "picker") body = renderPicker(m);
    else if (m.kind === "lesson") body = `<div class="lesson-stack">${renderLesson(m)}${renderQuiz(m)}</div>`;
    else if (m.kind === "quiz") body = renderQuiz(m);
    else if (m.kind === "error")
      body = `<div class="error-text"><span>${escapeHtml(m.data.message)}</span>${
        m.data.retry && isLast ? `<button class="chip" data-action="retry" data-id="${m.id}">${ICON.retry} Tekrar dene</button>` : ""
      }</div>`;
    else if (m.kind === "loading")
      body = `<div class="typing"><span class="typing-dots"><i></i><i></i><i></i></span><span class="typing-label">${escapeHtml(m.label || "Düşünüyor…")}</span></div>`;
    return `<div class="msg msg-ai${fresh(m)}" data-mid="${m.id || ""}">${AVATAR}<div class="msg-body">${body}</div></div>`;
  }

  const AVATAR =
    `<img class="avatar logo-dark" src="${window.CV_ASSETS.logoDark}" alt="" />` +
    `<img class="avatar logo-light" src="${window.CV_ASSETS.logoLight}" alt="" />`;

  // Animasyonu sadece ilk kez çizilen mesajlara uygula
  const seen = new Set();
  const fresh = (m) => (!m.id || seen.has(m.id) ? "" : " msg-new");

  function renderMessages() {
    const chat = currentChat();
    const msgs = chat ? [...chat.messages] : [];
    if (state.busy) msgs.push({ role: "assistant", kind: "loading", label: state.busyLabel, id: "loading-" + uid() });
    ui.messages.innerHTML = msgs.map((m, i) => renderMessage(m, i === msgs.length - 1)).join("");
    msgs.forEach((m) => m.id && seen.add(m.id));
    ui.app.classList.toggle("is-empty", msgs.length === 0);
    ui.title.textContent = chat ? chat.title : "Yeni sohbet";
    document.title = chat ? `${chat.title} · CodeVocab` : "CodeVocab";
    const target = !state.busy && state.scrollToId;
    if (target) state.scrollToId = null;
    requestAnimationFrame(() => {
      const node = target && ui.messages.querySelector(`[data-mid="${target}"]`);
      ui.thread.scrollTop = node ? node.offsetTop - 12 : ui.thread.scrollHeight;
    });
  }

  function renderAll() {
    renderSidebar();
    renderMessages();
    updateComposer();
  }

  function renderSuggestions() {
    ui.suggestions.innerHTML = currentSuggestions()
      .map(
        (s, i) => `
        <button class="suggestion" data-action="suggest" data-i="${i}">
          <span class="suggestion-icon">${ICON[s.icon] || ""}</span>
          <span class="suggestion-text"><b>${escapeHtml(s.title)}</b><span>${escapeHtml(s.sub)}</span></span>
        </button>`,
      )
      .join("");
  }

  const currentSuggestions = () => (state.mode === "topic" ? topicSuggestions() : SUGGESTIONS[state.mode]);

  function updateHero() {
    document.querySelectorAll(".hero-mode").forEach((h) => (h.hidden = h.dataset.for !== state.mode));
    $("#hero-sub").innerHTML = HERO_SUB[state.mode];
    renderSuggestions();
  }

  function moveModeIndicator() {
    const active = document.querySelector(".mode-btn.active");
    const ind = $("#mode-indicator");
    if (!active || !ind) return;
    ind.style.width = active.offsetWidth + "px";
    ind.style.transform = `translateX(${active.offsetLeft - 3}px)`;
  }

  function updateLearnedCount() {
    ui.learnedCount.textContent = knownWords().length + Object.keys(studiedTopics()).length;
  }

  // ───────────────────────── composer ─────────────────────────

  const PLACEHOLDER = {
    analyze: "İngilizce bir cümle yaz ya da bir şey sor…",
    word: "Bir İngilizce kelime yaz ya da Rastgele'ye bas…",
    topic: "Bir konu yaz: present perfect, articles, used to…",
  };
  const MAX_TOPIC = 80;

  function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll(".mode-btn").forEach((b) => {
      const on = b.dataset.mode === mode;
      b.classList.toggle("active", on);
      b.setAttribute("aria-selected", on);
    });
    ui.random.hidden = mode !== "word";
    ui.input.placeholder = PLACEHOLDER[mode];
    ui.input.maxLength = mode === "word" ? 40 : mode === "topic" ? MAX_TOPIC : MAX_LEN;
    moveModeIndicator();
    updateHero();
    updateComposer();
  }

  function autosize() {
    ui.input.style.height = "auto";
    ui.input.style.height = Math.min(ui.input.scrollHeight, 220) + "px";
  }

  function updateComposer() {
    const len = ui.input.value.trim().length;
    ui.send.disabled = state.busy || len === 0;
    ui.charCount.textContent = state.mode === "analyze" && len > MAX_LEN * 0.8 ? `${len}/${MAX_LEN}` : "";
    ui.charCount.classList.toggle("over", len > MAX_LEN);
  }

  // ───────────────────────── actions ─────────────────────────

  async function withBusy(fn, label) {
    if (state.busy) return;
    state.busy = true;
    state.busyLabel = label;
    renderMessages();
    updateComposer();
    try {
      await fn();
    } finally {
      state.busy = false;
      renderAll();
    }
  }

  function pushError(err, retry) {
    pushMessage({ role: "assistant", kind: "error", data: { message: err.message || "Bir hata oluştu.", retry } });
  }

  function runAnalyze(text) {
    return withBusy(async () => {
      const chat = currentChat();
      const history = historyForApi(chat).slice(0, -1); // son mesaj zaten `text`
      try {
        const res = await api("/api/analyze", { method: "POST", body: JSON.stringify({ text, history }) });
        if (res.type === "reply") {
          pushMessage({ role: "assistant", kind: "reply", data: res.data, provider: res.provider });
        } else {
          pushMessage({ role: "assistant", kind: "analysis", data: { ...res.data, original: text }, provider: res.provider });
        }
      } catch (err) {
        pushError(err, { type: "analyze", text });
      }
    }, "Düşünüyor…");
  }

  function runWord(word) {
    return withBusy(async () => {
      try {
        const data = await api(`/api/word_details?word=${encodeURIComponent(word)}`, { method: "GET" });
        pushMessage({ role: "assistant", kind: "word", data, provider: data.provider });
      } catch (err) {
        pushError(err, { type: "word", word });
      }
    }, "Kelime kartı hazırlanıyor…");
  }

  function runRandom() {
    return withBusy(async () => {
      try {
        const words = await api("/api/get_random_words", {
          method: "POST",
          body: JSON.stringify({ known_words: knownWords(), count: 5 }),
        });
        pushMessage({ role: "assistant", kind: "picker", data: { words } });
      } catch (err) {
        pushError(err, { type: "random" });
      }
    }, "Kelimeler seçiliyor…");
  }

  function prepQuiz(quiz) {
    return quiz.map((q) => ({ ...q, user: null, ok: null }));
  }

  function runTopic(topic) {
    return withBusy(async () => {
      try {
        const res = await api("/api/topic", { method: "POST", body: JSON.stringify({ topic }) });
        const chat = currentChat();
        // Sohbet başlığını normalize edilmiş konu adıyla güncelle
        if (chat && chat.messages.filter((m) => m.role === "user").length <= 1) chat.title = `Konu: ${res.lesson.topic}`;
        const msg = { id: uid(), role: "assistant", kind: "lesson", data: { lesson: res.lesson, quiz: prepQuiz(res.quiz) }, provider: res.provider };
        state.scrollToId = msg.id; // ders uzun: en alta değil dersin başına kaydır
        pushMessage(msg);
        // Dersten sonra aynı sohbette soru sorabilsin diye analiz moduna geç
        setMode("analyze");
        ui.input.placeholder = `"${res.lesson.topic}" hakkında soru sor ya da bu kalıpla bir cümle kur…`;
      } catch (err) {
        pushError(err, { type: "topic", topic });
      }
    }, "Ders hazırlanıyor ve denetleniyor… (10-15 sn)");
  }

  function runTopicQuiz(topic, previous) {
    return withBusy(async () => {
      try {
        const res = await api("/api/topic_quiz", { method: "POST", body: JSON.stringify({ topic, previous }) });
        const msg = { id: uid(), role: "assistant", kind: "quiz", data: { topic, quiz: prepQuiz(res.quiz) }, provider: res.provider };
        state.scrollToId = msg.id;
        pushMessage(msg);
      } catch (err) {
        pushError(err, { type: "topicQuiz", topic, previous });
      }
    }, "Yeni sorular hazırlanıyor ve denetleniyor…");
  }

  function findMessage(mid) {
    return currentChat()?.messages.find((m) => m.id === mid) || null;
  }

  /** Bir quiz sorusunu cevapla; sadece o soruyu ve alt bilgiyi yeniden çiz (diğer kutulardaki yazılar kaybolmasın). */
  function answerQuestion(mid, qi, value) {
    const m = findMessage(mid);
    const q = m?.data.quiz[qi];
    if (!q || q.user != null) return;
    q.user = value;
    q.ok = q.type === "choice" ? value === q.answer : isFillCorrect(q, value);
    saveChats();

    const qNode = document.querySelector(`[data-qid="${mid}-${qi}"]`);
    if (qNode) qNode.outerHTML = renderQuestion(m, qi);
    const foot = document.querySelector(`[data-foot="${mid}"]`);
    if (foot) foot.outerHTML = renderQuizFoot(m);

    if (quizDone(m.data.quiz) && !m.data.recorded) {
      m.data.recorded = true;
      const lesson = m.kind === "lesson" ? m.data.lesson : { topic: m.data.topic };
      const known = studiedTopics()[lesson.topic.toLowerCase()];
      saveTopicResult({ ...known, ...lesson, topic: lesson.topic, topic_tr: lesson.topic_tr || known?.name_tr }, quizScore(m.data.quiz), m.data.quiz.length);
      saveChats();
      requestAnimationFrame(() => document.querySelector(`[data-foot="${mid}"]`)?.scrollIntoView({ behavior: "smooth", block: "nearest" }));
    } else {
      // Sıradaki cevaplanmamış boşluk doldurma kutusuna odaklan
      const next = document.querySelector(`[data-qid="${mid}-${qi + 1}"] input`);
      if (next && q.type === "fill") next.focus({ preventScroll: true });
    }
  }

  function submit(text) {
    text = (text ?? ui.input.value).trim();
    if (!text || state.busy) return;
    if (state.mode === "analyze" && text.length > MAX_LEN) return toast(`En fazla ${MAX_LEN} karakter yazabilirsin.`);

    if (state.mode === "topic") {
      if (text.length > MAX_TOPIC) return toast(`Konu adı en fazla ${MAX_TOPIC} karakter olabilir.`);
      ensureChat(`Konu: ${text}`);
      pushMessage({ role: "user", text: `📘 ${text}` });
      ui.input.value = "";
      autosize();
      return runTopic(text);
    }

    if (state.mode === "word") {
      const word = text.toLowerCase();
      if (!/^[a-z][a-z'\- ]{0,39}$/.test(word)) return toast("Sadece İngilizce bir kelime yaz (ör. awkward).");
      ensureChat(`Kelime: ${word}`);
      pushMessage({ role: "user", text: word });
      ui.input.value = "";
      autosize();
      return runWord(word);
    }

    ensureChat(text);
    pushMessage({ role: "user", text });
    ui.input.value = "";
    ui.input.placeholder = PLACEHOLDER.analyze;
    autosize();
    runAnalyze(text);
  }

  function requestRandom() {
    if (state.busy) return;
    ensureChat("Kelime avı");
    pushMessage({ role: "user", text: "🎲 Rastgele kelimeler" });
    runRandom();
  }

  function newChat({ focus = true } = {}) {
    state.currentId = null;
    ui.input.value = "";
    setMode("analyze");
    autosize();
    closeSidebar();
    renderAll();
    if (focus) ui.input.focus();
  }

  function openChat(id) {
    if (state.busy) return;
    state.currentId = id;
    const last = [...(currentChat()?.messages || [])].reverse().find((m) => m.role === "assistant");
    setMode(last && (last.kind === "word" || last.kind === "picker") ? "word" : "analyze");
    closeSidebar();
    renderAll();
  }

  function deleteChat(id) {
    const chat = state.chats.find((c) => c.id === id);
    if (!chat || !confirm(`"${chat.title}" sohbeti silinsin mi?`)) return;
    state.chats = state.chats.filter((c) => c.id !== id);
    if (state.currentId === id) state.currentId = null;
    saveChats();
    renderAll();
  }

  function openSidebar() {
    ui.app.classList.add("sidebar-open");
  }
  function closeSidebar() {
    ui.app.classList.remove("sidebar-open");
  }

  function openLearned() {
    const words = knownWords();
    const topics = Object.values(studiedTopics()).sort((a, b) => b.updatedAt - a.updatedAt);

    const topicHtml = topics.length
      ? `<div class="learned-section">
          <p class="label">Çalışılan konular · ${topics.length}</p>
          <div class="topic-list">${topics
            .map((t) => {
              const color = t.best === 100 ? "var(--good)" : t.best >= 60 ? "var(--info)" : "var(--warn)";
              return `<button class="topic-row" data-action="learned-topic" data-topic="${escapeHtml(t.name)}">
                  <span class="topic-row-main">
                    <b>${escapeHtml(t.name)}</b>
                    <span>${escapeHtml([t.level, t.name_tr].filter(Boolean).join(" · "))}</span>
                  </span>
                  <span class="topic-row-score" style="--c:${color}">
                    <b>%${t.best}</b><span>${t.attempts} deneme</span>
                  </span>
                </button>`;
            })
            .join("")}</div>
        </div>`
      : "";

    const wordHtml = words.length
      ? `<div class="learned-section">
          <p class="label">Öğrenilen kelimeler · ${words.length}</p>
          <div class="learned-grid">${[...words]
            .reverse()
            .map(
              (w) => `<span class="learned-tag">
                <button class="open-word" data-action="learned-open" data-word="${escapeHtml(w)}">${escapeHtml(w)}</button>
                <button data-action="learned-remove" data-word="${escapeHtml(w)}" aria-label="${escapeHtml(w)} kelimesini listeden çıkar">
                  <svg viewBox="0 0 24 24" width="12" height="12"><path d="M18 6 6 18M6 6l12 12"/></svg>
                </button></span>`,
            )
            .join("")}</div>
        </div>`
      : "";

    const total = words.length + topics.length;
    ui.learnedBody.innerHTML = total
      ? `<div class="learned-stat"><b>${total}</b><span>${words.length} kelime · ${topics.length} konu</span></div>${topicHtml}${wordHtml}`
      : `<p class="empty-note">Henüz bir şey yok.<br/>Kelime modunda "Biliyorum" de ya da Konu modunda bir quiz bitir.</p>`;
    if (!ui.learnedModal.open) ui.learnedModal.showModal();
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    ui.themeLabel.textContent = theme === "dark" ? "Açık tema" : "Koyu tema";
    document.querySelector('meta[name="theme-color"]').content = theme === "dark" ? "#000000" : "#fafafa";
  }

  async function copyText(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
      if (btn) {
        const prev = btn.innerHTML;
        btn.innerHTML = ICON.check;
        setTimeout(() => (btn.innerHTML = prev), 1200);
      }
    } catch {
      toast("Kopyalanamadı.");
    }
  }

  // ───────────────────────── events ─────────────────────────

  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-action]");
    if (!t) return;
    const a = t.dataset.action;

    switch (a) {
      case "new-chat":
        return newChat();
      case "open-chat":
        return openChat(t.dataset.id);
      case "delete-chat":
        return deleteChat(t.dataset.id);
      case "open-sidebar":
        return openSidebar();
      case "close-sidebar":
        return closeSidebar();
      case "random-words":
        setMode("word");
        return requestRandom();
      case "pick-word": {
        if (state.busy) return;
        const w = t.dataset.word;
        pushMessage({ role: "user", text: w });
        return runWord(w);
      }
      case "toggle-known": {
        const w = t.dataset.word;
        const now = !isKnown(w);
        setKnown(w, now);
        if (now) toast(`"${w}" öğrenilenlere eklendi.`);
        return renderMessages();
      }
      case "practice":
        setMode("analyze");
        ui.input.value = "";
        ui.input.placeholder = `"${t.dataset.word}" kelimesiyle bir cümle kur…`;
        return ui.input.focus();
      case "followup":
        if (state.busy) return;
        setMode("analyze");
        pushMessage({ role: "user", text: t.dataset.text });
        return runAnalyze(t.dataset.text);
      case "retry": {
        const chat = currentChat();
        const msg = chat?.messages.find((m) => m.id === t.dataset.id);
        if (!msg?.data?.retry) return;
        removeMessage(msg.id);
        const r = msg.data.retry;
        if (r.type === "analyze") return runAnalyze(r.text);
        if (r.type === "word") return runWord(r.word);
        if (r.type === "topic") return runTopic(r.topic);
        if (r.type === "topicQuiz") return runTopicQuiz(r.topic, r.previous);
        return runRandom();
      }
      case "quiz-choice": {
        const m = findMessage(t.dataset.mid);
        const q = m?.data.quiz[+t.dataset.qi];
        if (q) answerQuestion(m.id, +t.dataset.qi, q.options[+t.dataset.oi]);
        return;
      }
      case "quiz-dispute": {
        if (state.busy) return;
        const m = findMessage(t.dataset.mid);
        const q = m?.data.quiz[+t.dataset.qi];
        if (!q) return;
        const how = q.type === "choice" ? `"${q.user}" şıkkını seçtim` : `boşluğa "${q.user}" yazdım`;
        const text = `Quizde "${q.q}" sorusunda ${how}, doğrusu "${q.answer}" dendi. Benim cevabım da doğru kabul edilebilir mi?`;
        setMode("analyze");
        pushMessage({ role: "user", text });
        return runAnalyze(text);
      }
      case "quiz-more": {
        if (state.busy) return;
        const chat = currentChat();
        const m = findMessage(t.dataset.mid);
        if (!m) return;
        const topic = quizTopic(m);
        // Bu konuda şimdiye kadar sorulan tüm sorular tekrar edilmesin
        const previous = chat.messages
          .filter((x) => (x.kind === "lesson" || x.kind === "quiz") && quizTopic(x) === topic)
          .flatMap((x) => x.data.quiz.map((q) => q.q));
        pushMessage({ role: "user", text: "🔁 Yeni sorular" });
        return runTopicQuiz(topic, previous);
      }
      case "topic-ask":
        setMode("analyze");
        ui.input.value = "";
        ui.input.placeholder = `"${t.dataset.topic}" hakkında soru sor ya da bu kalıpla bir cümle kur…`;
        return ui.input.focus();
      case "topic-new":
        newChat({ focus: false });
        setMode("topic");
        return ui.input.focus();
      case "learned-topic":
        ui.learnedModal.close();
        newChat({ focus: false });
        setMode("topic");
        return submit(t.dataset.topic);
      case "speak":
        return speak(t.dataset.text, t);
      case "copy":
        return copyText(t.dataset.text, t);
      case "suggest": {
        const s = currentSuggestions()[+t.dataset.i];
        if (s.mode) setMode(s.mode);
        if (s.random) return requestRandom();
        return submit(s.topic || s.title);
      }
      case "open-learned":
        closeSidebar();
        return openLearned();
      case "close-modal":
        return ui.learnedModal.close();
      case "learned-remove":
        setKnown(t.dataset.word, false);
        openLearned();
        return renderMessages();
      case "learned-open":
        ui.learnedModal.close();
        newChat({ focus: false });
        setMode("word");
        return submit(t.dataset.word);
      case "collapse-sidebar": {
        const collapsed = !ui.app.classList.contains("sidebar-collapsed");
        setCollapsed(collapsed);
        try {
          localStorage.setItem(STORE_COLLAPSED, collapsed ? "1" : "0");
        } catch {}
        return;
      }
      case "toggle-theme": {
        const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        try {
          localStorage.setItem(STORE_THEME, next);
        } catch {}
        return applyTheme(next);
      }
    }
  });

  document.querySelectorAll(".mode-btn").forEach((b) =>
    b.addEventListener("click", () => {
      setMode(b.dataset.mode);
      ui.input.focus();
    }),
  );

  $("#composer").addEventListener("submit", (e) => {
    e.preventDefault();
    submit();
  });

  // Quiz boşluk doldurma formları (mesajların içinde, dinamik)
  ui.messages.addEventListener("submit", (e) => {
    const form = e.target.closest(".quiz-fill");
    if (!form) return;
    e.preventDefault();
    const value = form.elements.answer.value.trim();
    if (!value) return form.elements.answer.focus();
    answerQuestion(form.dataset.mid, +form.dataset.qi, value);
  });

  ui.input.addEventListener("input", () => {
    autosize();
    updateComposer();
  });

  ui.input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      submit();
    }
  });

  $("#chat-search").addEventListener("input", (e) => {
    state.search = e.target.value;
    renderSidebar();
  });

  ui.learnedModal.addEventListener("click", (e) => {
    if (e.target === ui.learnedModal) ui.learnedModal.close();
  });

  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      newChat();
    } else if (e.key === "Escape") {
      closeSidebar();
    }
  });

  // ───────────────────────── boot ─────────────────────────

  function setCollapsed(collapsed) {
    ui.app.classList.toggle("sidebar-collapsed", collapsed);
    $("#expand-btn").hidden = !collapsed;
  }

  ui.thread.addEventListener("scroll", () => ui.app.classList.toggle("is-scrolled", ui.thread.scrollTop > 4), { passive: true });
  window.addEventListener("resize", moveModeIndicator);
  document.fonts?.ready.then(moveModeIndicator);

  try {
    setCollapsed(localStorage.getItem(STORE_COLLAPSED) === "1");
  } catch {}
  applyTheme(document.documentElement.dataset.theme || "dark");
  updateLearnedCount();
  setMode("analyze");
  renderAll();

  // Bağlantıdan gelenler: /app?q=cümle (hemen analiz), /app?mode=vocab|chat|topic
  const params = new URLSearchParams(location.search);
  const legacy = params.get("mode");
  const prefill = (params.get("q") || "").trim().slice(0, MAX_LEN);
  if (prefill) {
    // Tanıtım sayfasındaki kutudan gelen cümle: yeni sohbette hemen analiz et.
    history.replaceState(null, "", location.pathname);
    submit(prefill);
  } else if (legacy) {
    history.replaceState(null, "", location.pathname);
    if (legacy === "vocab") {
      setMode("word");
      requestRandom();
    } else if (legacy === "topic") {
      setMode("topic");
      ui.input.focus();
    } else {
      ui.input.focus();
    }
  } else if (matchMedia("(min-width: 861px)").matches) {
    ui.input.focus();
  }

  api("/api/health")
    .then((h) => {
      if (!h.providers?.length) toast("Sunucuda AI anahtarı tanımlı değil (.env).");
    })
    .catch(() => {});
})();
