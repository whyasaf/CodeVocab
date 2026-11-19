"""
Dil desteği (tr / en).

- Dil önce `cv_lang` çerezinden, yoksa tarayıcının sistem dilinden (Accept-Language) seçilir.
  Türkçe sistemde Türkçe, diğer her dilde İngilizce açılır.
- Şablonlarda ve sunucu mesajlarında Türkçe metin anahtardır: t("Gizlilik") → "Privacy".
  Çevirisi olmayan metin olduğu gibi döner, yani hiçbir şey kırılmaz.
- Uzun içerik sayfaları (tanıtım, rehber, hakkında, gizlilik, koşullar) için ayrı *_en.html
  şablonları vardır; bkz. app.render_page.
"""

from flask import g, request
from markupsafe import Markup

SUPPORTED = ("tr", "en")
LANG_COOKIE = "cv_lang"


def get_lang():
    if "lang" not in g:
        lang = request.cookies.get(LANG_COOKIE)
        if lang not in SUPPORTED:
            lang = request.accept_languages.best_match(SUPPORTED) or "en"
        g.lang = lang
    return g.lang


def t(text, **kwargs):
    """Türkçe metni aktif dile çevirir. Şablonlardaki <b>/<br> korunur (metinler bizim sabitlerimiz)."""
    if get_lang() == "en":
        text = EN.get(text, text)
    if kwargs:
        text = text.format(**kwargs)
    return Markup(text)


def tp(text, **kwargs):
    """Düz metin sürümü (JSON yanıtları için)."""
    return str(t(text, **kwargs))


# Türkçe → İngilizce. Ortak iskelet (nav, footer), uygulama kabuğu ve sunucu mesajları.
EN = {
    # ── Ortak iskelet ──
    "Sayfalar": "Pages",
    "Rehber": "Guide",
    "Hakkında": "About",
    "Gizlilik": "Privacy",
    "Temayı değiştir": "Toggle theme",
    "Uygulamayı aç": "Open app",
    "İngilizce öğrenen herkes için yapay zeka destekli cümle düzeltme ve İngilizce mentoru. Ücretsiz, reklamsız, kayıtsız.":
        "An AI-powered sentence checker and English mentor for every learner. Free, no ads, no sign-up.",
    "Alt menü": "Footer menu",
    "Uygulama": "App",
    "Cümle analizi": "Sentence check",
    "Kelime avcısı": "Word hunter",
    "Konu çalış": "Study a topic",
    "Nasıl kullanılır?": "How to use",
    "Proje": "Project",
    "Yasal": "Legal",
    "Kullanım koşulları": "Terms of use",
    "Bir": "A",
    "projesi": "project",
    "Başa dön": "Back to top",
    "Dil": "Language",
    "Yükleniyor…": "Loading…",

    # ── Uygulama kabuğu (index.html) ──
    "CodeVocab — Uygulama": "CodeVocab — App",
    "İngilizce cümleni yaz, bir mentor gibi düzeltelim. Kelime öğren, konu çalış, takıldığın yeri sor. Ücretsiz.":
        "Write an English sentence and get it corrected like a mentor would. Learn words, study topics, ask questions. Free.",
    "Sohbetler": "Chats",
    "CodeVocab tanıtım sayfası": "CodeVocab home page",
    "Kenar çubuğunu gizle": "Hide sidebar",
    "Kenar çubuğunu göster": "Show sidebar",
    "Menüyü kapat": "Close menu",
    "Menüyü aç": "Open menu",
    "Yeni sohbet": "New chat",
    "Sohbetlerde ara": "Search chats",
    "Geçmiş sohbetler": "Chat history",
    "Öğrenilenler": "Learned",
    "Uygulamayı yükle": "Install app",
    "Açık tema": "Light theme",
    "Koyu tema": "Dark theme",
    "Mod": "Mode",
    "Analiz": "Check",
    "Kelime": "Word",
    "Konu": "Topic",
    "Rastgele": "Random",
    "Gönder": "Send",
    "Mesaj": "Message",
    "İngilizce bir cümle yaz ya da bir şey sor…": "Write an English sentence or ask something…",
    "İngilizce cümleni yaz, bir mentor gibi düzeltelim.<br />Takıldığın yeri sor, sohbet ederek öğren.":
        "Write an English sentence and get it corrected like a mentor would.<br />Ask about anything, learn by chatting.",
    "CodeVocab hata yapabilir. Sohbetler yalnızca bu tarayıcıda saklanır.":
        "CodeVocab can make mistakes. Chats are stored only in this browser.",
    "Kapat": "Close",

    # ── Tanıtım sayfası (home.html) ──
    'Yapay zeka destekli İngilizce cümle düzeltme':
        'AI-powered English sentence correction',
    'İngilizce cümleni yaz; yapay zeka mentorun puanlasın, hatanı Türkçe açıklasın ve doğrusunu göstersin. Kelime öğren, her gün bir kalıp çalış. Ücretsiz, kayıtsız.':
        'Write an English sentence; your AI mentor scores it, explains the mistake and shows the correct version. Learn words, study one pattern a day. Free, no sign-up.',
    'İngilizceni yaz.':
        'Write your English.',
    'Mentorun düzeltsin.':
        'Your mentor fixes it.',
    'Cümleni yaz; puanını, hatanı ve doğrusunu saniyeler içinde Türkçe açıklamasıyla gör.\n      Takıldığın yeri sor, kelime öğren, her gün bir kalıp çalış.':
        'Write a sentence and see your score, your mistake and the correct version, explained in seconds.\n      Ask about anything, learn words, study one pattern a day.',
    'İngilizce bir cümle':
        'An English sentence',
    'Analiz et':
        'Check',
    'Düzelt':
        'Fix it',
    "Bir cümle yaz ve Enter'a bas, ya da":
        'Type a sentence and press Enter, or',
    'boş bir sohbet aç':
        'open an empty chat',
    'Örnek analiz':
        'Example check',
    'Türkçe kafayla İngilizce':
        'Thinking in Turkish, writing in English',
    'Bunları sen de yapıyor olabilirsin.':
        'You might be making these too.',
    'Ne yapar?':
        'What does it do?',
    'Üç mod. Tek sohbet.':
        'Three modes. One chat.',
    '01 · Analiz':
        '01 · Check',
    'Cümleni puanlar, nedenini anlatır.':
        'Scores your sentence, explains why.',
    '100 üzerinden puan, kelime kelime fark, Türkçe mentor notu. "Neden böyle?" diye sorup sohbete devam edebilirsin.':
        'A score out of 100, a word-by-word diff and a mentor\'s note. Ask "Why is that?" and keep the conversation going.',
    '"explain" iki nesneyi doğrudan almaz: <strong>explain something to someone</strong>.':
        '"explain" doesn\'t take the person directly: <strong>explain something to someone</strong>.',
    '02 · Kelime':
        '02 · Word',
    'Kelime kartları':
        'Word cards',
    'garip, tuhaf, rahatsız edici':
        'clumsy, uncomfortable, embarrassing',
    'Anlam, telaffuz, üç seviyede örnek cümle ve Türklerin sık yaptığı hata.':
        'Meaning, pronunciation, examples at three levels and the most common mistake.',
    '03 · Konu':
        '03 · Topic',
    'Her gün bir kalıp':
        'One pattern a day',
    'Kısa ders, Türkçe ile karşılaştırma ve 5 soruluk quiz. Skorun kaydedilir.':
        'A short lesson, common traps and a 5-question quiz. Your score is saved.',
    'Hesap yok. Her şey senin tarayıcında.':
        'No account. Everything stays in your browser.',
    'Sohbetlerin, öğrendiğin kelimeler ve skorların sunucuda değil, sadece kendi cihazında saklanır.':
        'Your chats, learned words and scores are stored only on your device, never on a server.',
    'Nasıl çalışır?':
        'How it works',
    'Yaz. Gör. Sor.':
        'Write. See. Ask.',
    'Yaz':
        'Write',
    'Aklına gelen bir İngilizce cümleyi yaz: mesaj, e-posta, ödev, ne olursa.':
        'Write any English sentence: a message, an email, homework, anything.',
    'Gör':
        'See',
    'Puanını, düzeltilmiş hâlini ve hatanın nedenini Türkçe açıklamayla gör.':
        'See your score, the corrected version and why it was wrong.',
    'Sor':
        'Ask',
    'Anlamadığın yeri sor, aynı kalıpla yeni bir cümle kur, tekrar dene.':
        "Ask what you didn't get, make a new sentence with the same pattern, try again.",
    'kelimelik havuz':
        'word pool',
    'hazır konu ve kalıp':
        'ready-made topics',
    'ücret':
        'cost',
    'kayıt formu':
        'sign-up forms',
    'Bugünün ilk cümlesini yaz.':
        "Write today's first sentence.",
    'Bir dakikanı al, bir cümle yaz. Gerisini mentorun halleder.':
        'Take a minute, write one sentence. Your mentor handles the rest.',
    'Hemen başla':
        'Get started',
    'Rehberi oku':
        'Read the guide',
    '<b>since</b> bir başlangıç noktası ister (since 2020). Süre için <b>for</b> kullanılır; hâlâ süren durum için <b>have been + -ing</b> gerekir.':
        '<b>since</b> needs a starting point (since 2020). Use <b>for</b> with a duration; an ongoing situation needs <b>have been + -ing</b>.',
    '<b>explain</b> kişiyi doğrudan nesne olarak almaz: <b>explain something to someone</b>.':
        "<b>explain</b> doesn't take the person as a direct object: <b>explain something to someone</b>.",
    'Kusursuz. Resmi e-postalar için ideal bir kapanış cümlesi.':
        'Perfect. An ideal closing line for formal emails.',
    'Mükemmel':
        'Excellent',
    'Gayet iyi':
        'Very good',
    'Geliştirilebilir':
        'Needs work',
    'Tekrar dene':
        'Try again',

    # ── Sunucu mesajları ──
    "Biraz hızlı gidiyorsun. Bir dakika bekleyip tekrar dene.":
        "You're going a bit fast. Wait a minute and try again.",
    "Bu saatlik istek sınırına ulaştın. Biraz ara verip sonra devam edebilirsin.":
        "You've reached this hour's request limit. Take a short break and continue later.",
    "Tüm ücretsiz AI kotaları şu an dolu. Bir dakika sonra tekrar dene.":
        "All free AI quotas are full right now. Try again in a minute.",
    "Sunucuda AI anahtarı tanımlı değil (.env dosyasını kontrol et).":
        "No AI key is configured on the server (check the .env file).",
    "AI şu an yanıt veremiyor. Biraz sonra tekrar dene.": "The AI can't respond right now. Try again shortly.",
    "Kelime listesi okunamadı.": "Couldn't read the word list.",
    "Geçerli bir İngilizce kelime gir.": "Enter a valid English word.",
    "Boş mesaj gönderilemez.": "You can't send an empty message.",
    "Mesaj çok uzun (en fazla {n} karakter).": "Message is too long (max {n} characters).",
    "Model boş yanıt döndürdü.": "The model returned an empty response.",
    "Model eksik yanıt döndürdü, tekrar dene.": "The model returned an incomplete response, try again.",
    "Model geçersiz puan döndürdü, tekrar dene.": "The model returned an invalid score, try again.",
    "Bir konu yaz (ör. present perfect).": "Type a topic (e.g. present perfect).",
    "Konu adı çok uzun (en fazla {n} karakter).": "Topic name is too long (max {n} characters).",
    "Bu bir İngilizce konusu gibi görünmüyor. Ör: present perfect, articles, conditionals.":
        "That doesn't look like an English topic. E.g. present perfect, articles, conditionals.",
    "Ders hazırlandı ama denetlenemedi (AI kotaları yoğun). Birkaç saniye sonra tekrar dene.":
        "The lesson was written but couldn't be checked (AI quotas are busy). Try again in a few seconds.",
    "Ders tam oluşturulamadı, tekrar dene.": "The lesson couldn't be completed, try again.",
    "Sorular hazırlandı ama denetlenemedi. Birkaç saniye sonra tekrar dene.":
        "The questions were written but couldn't be checked. Try again in a few seconds.",
    "Yeni sorular oluşturulamadı, tekrar dene.": "Couldn't create new questions, try again.",
}


# AI'a eklenen dil talimatı: prompt'lar Türkçe açıklama ister; İngilizce arayüzde bunu çevirir.
PROMPT_LANG_NOTE = {
    "en": """

═══════════════════════════════════════════════════════
LANGUAGE OVERRIDE (highest priority)
═══════════════════════════════════════════════════════
The learner's interface language is ENGLISH. Everywhere the instructions above ask for Turkish
text (explanations, notes, titles, tips, messages, motivation, "explain", "why", "text",
"summary", "turkish_link", "meaning_tr", "topic_tr", "tip"), write it in clear, simple ENGLISH
instead. The learner is still most likely a Turkish speaker, so keep the Turkish-specific
insights (comparisons with Turkish, typical Turkish mistakes) but explain them in English.
For "tr" translations of example sentences, write a short plain-English paraphrase.
For "meaning_tr", give a short English definition. For "part_of_speech", use one English word
(noun, verb, adjective, adverb, preposition, conjunction…). All other rules, fields and the
JSON format stay exactly the same.
""",
}


def prompt_for(system_prompt):
    return system_prompt + PROMPT_LANG_NOTE.get(get_lang(), "")
