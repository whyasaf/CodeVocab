/* CodeVocab — English UI strings.
   Loaded only when the interface language is English. Turkish source text is the key,
   so a missing entry simply falls back to Turkish instead of breaking. */
window.CV_EN = {
  strings: {
    // misc / helpers
    "Tarayıcı depolama alanı dolu ya da kapalı.": "Browser storage is full or disabled.",
    "Sunucuya ulaşılamadı. İnternet bağlantını kontrol et.": "Couldn't reach the server. Check your internet connection.",
    "Sunucu hatası ({status}).": "Server error ({status}).",
    "Tarayıcın sesli okumayı desteklemiyor.": "Your browser doesn't support text-to-speech.",
    "Yeni sohbet": "New chat",
    "Bugün": "Today",
    "Dün": "Yesterday",
    "Son 7 gün": "Last 7 days",
    "Son 30 gün": "Last 30 days",
    "Daha eski": "Older",
    "Sonuç bulunamadı.": "No results.",
    "Henüz sohbet yok. İlk cümleni yaz!": "No chats yet. Write your first sentence!",
    "Sohbet adı": "Chat name",
    "(yeniden adlandırmak için çift tıkla)": "(double-click to rename)",
    "Sohbeti yeniden adlandır": "Rename chat",
    "Yeniden adlandır": "Rename",
    "Sohbeti sil": "Delete chat",
    "Sil": "Delete",
    '"{title}" sohbeti silinsin mi?': 'Delete the chat "{title}"?',
    "Yeniden adlandırmak için tıkla": "Click to rename",
    "CodeVocab yüklendi. Ana ekranından açabilirsin.": "CodeVocab is installed. Open it from your home screen.",
    'Safari\'de Paylaş simgesine dokun, sonra "Ana Ekrana Ekle"yi seç.': 'In Safari, tap the Share icon, then choose "Add to Home Screen".',
    "Açık tema": "Light theme",
    "Koyu tema": "Dark theme",
    "Kopyalanamadı.": "Couldn't copy.",
    "Kopyalandı.": "Copied.",
    "Bir hata oluştu.": "Something went wrong.",
    "Tekrar dene": "Try again",
    "Sunucuda AI anahtarı tanımlı değil (.env).": "No AI key is configured on the server (.env).",

    // analysis card
    "Mükemmel": "Excellent",
    "Native speaker böyle yazar.": "A native speaker would write it this way.",
    "Gayet iyi": "Very good",
    "Küçük bir dokunuş yeterli.": "Just a small touch needed.",
    "Geliştirilebilir": "Needs work",
    "Önemli bir hata var.": "There's an important mistake.",
    "Cümlenin yapısı bozulmuş.": "The sentence structure is broken.",
    "Cümlen": "Your sentence",
    "Doğrusu": "Correct version",
    "Mentor notu": "Mentor's note",
    "Dinle": "Listen",
    "Kopyala": "Copy",

    // word card
    "Telaffuzu dinle": "Listen to pronunciation",
    "Öğrenildi": "Learned",
    "Biliyorum": "I know this",
    "Cümle kur": "Make a sentence",
    "İpucu": "Tip",
    "Örnek cümleler": "Example sentences",
    '"{w}" öğrenilenlere eklendi.': '"{w}" was added to Learned.',
    '"{w}" kelimesiyle bir cümle kur…': 'Make a sentence with "{w}"…',

    // lesson card
    "Formül": "Formula",
    "Ne zaman kullanılır?": "When is it used?",
    "Türkçe ile karşılaştır": "Compared with Turkish",
    "Türklerin düştüğü tuzaklar": "Common traps for Turkish speakers",
    "{w} ile farkı": "Difference from {w}",
    "Sinyal kelimeler": "Signal words",
    "Mini quiz": "Mini quiz",
    "{n} soru": "{n} questions",

    // quiz
    "Boşluğa ne gelmeli?": "What goes in the blank?",
    "Cevap": "Answer",
    "Kontrol et": "Check",
    "Doğru!": "Correct!",
    "Doğrusu: {a}": "Correct answer: {a}",
    "Benim cevabım da doğru olabilir mi? Mentora sor →": "Could my answer be right too? Ask the mentor →",
    "Doğru seçeneği bul": "Pick the right option",
    "Boşluğu doldur": "Fill in the blank",
    "{n}/{total} cevaplandı": "{n}/{total} answered",
    "Kusursuz! Bu kalıp artık senin. 🎯": "Perfect! This pattern is yours now. 🎯",
    "İyi gidiyor, yanlışlara bir kez daha göz at. 💪": "Going well — take another look at the mistakes. 💪",
    "Dersi bir kez daha oku, sonra yeni sorularla dene. 📚": "Read the lesson once more, then try new questions. 📚",
    "{score}/{total} doğru": "{score}/{total} correct",
    "Yeni sorular": "New questions",
    "Soru sor": "Ask a question",
    "Başka konu": "Another topic",
    'Quizde "{q}" sorusunda "{u}" şıkkını seçtim, doğrusu "{a}" dendi. Benim cevabım da doğru kabul edilebilir mi?':
      'In the quiz question "{q}" I chose "{u}", but the answer was "{a}". Could my answer also be correct?',
    'Quizde "{q}" sorusunda boşluğa "{u}" yazdım, doğrusu "{a}" dendi. Benim cevabım da doğru kabul edilebilir mi?':
      'In the quiz question "{q}" I wrote "{u}", but the answer was "{a}". Could my answer also be correct?',

    // word picker
    "Tebrikler, havuzdaki tüm kelimeleri öğrenmişsin! 🎉": "Congrats, you've learned every word in the pool! 🎉",
    "Birini seç, kartını hazırlayayım:": "Pick one and I'll make its card:",

    // loading labels
    "Düşünüyor…": "Thinking…",
    "Kelime kartı hazırlanıyor…": "Preparing the word card…",
    "Kelimeler seçiliyor…": "Picking words…",
    "Ders hazırlanıyor ve denetleniyor… (10-15 sn)": "Writing and checking the lesson… (10–15 s)",
    "Yeni sorular hazırlanıyor ve denetleniyor…": "Writing and checking new questions…",

    // composer
    '"{topic}" hakkında soru sor ya da bu kalıpla bir cümle kur…': 'Ask about "{topic}" or make a sentence with this pattern…',
    "Konu adı en fazla {n} karakter olabilir.": "A topic name can be at most {n} characters.",
    "En fazla {n} karakter yazabilirsin.": "You can write at most {n} characters.",
    "Sadece İngilizce bir kelime yaz (ör. awkward).": "Type a single English word (e.g. awkward).",
    "Kelime avı": "Word hunt",
    "Konu: {topic}": "Topic: {topic}",
    "Kelime: {w}": "Word: {w}",

    // learned modal
    "Çalışılan konular · {n}": "Studied topics · {n}",
    "Öğrenilen kelimeler · {n}": "Learned words · {n}",
    "{w} kelimesini listeden çıkar": "Remove {w} from the list",
    'Henüz bir şey yok.<br/>Kelime modunda "Biliyorum" de ya da Konu modunda bir quiz bitir.':
      'Nothing here yet.<br/>Tap "I know this" in Word mode or finish a quiz in Topic mode.',
    "en iyi %{p} · {n} deneme": "best {p}% · {n} attempts",
  },

  suggestions: {
    analyze: [
      { icon: "clock", title: "I have seen this movie two days ago", sub: "Is there a tense mistake?" },
      { icon: "flag", title: "We should discuss about the plan", sub: "A classic preposition trap" },
      { icon: "chat", title: "When do we use the present perfect?", sub: "Ask the mentor" },
      { icon: "dice", title: "Give me 5 random words", sub: "Start a word hunt", mode: "word", random: true },
    ],
    word: [
      { icon: "dice", title: "5 random words", sub: "A surprise pick from the pool", random: true },
      { icon: "book", title: "although", sub: "A common conjunction" },
      { icon: "book", title: "awkward", sub: "An everyday favourite" },
      { icon: "book", title: "nevertheless", sub: "A formal connector" },
    ],
  },

  heroSub: {
    analyze: "Write an English sentence and get it corrected like a mentor would.<br />Ask about anything, learn by chatting.",
    word: "Type a word or ask for a random pick.<br />Meaning, pronunciation and examples at three levels.",
    topic: "Type a grammar topic or pattern and I'll prepare a lesson card.<br />Then test yourself with a 5-question mini quiz.",
  },

  placeholder: {
    analyze: "Write an English sentence or ask something…",
    word: "Type an English word or press Random…",
    topic: "Type a topic: present perfect, articles, used to…",
  },

  followups: ["Why is that?", "How do I say it more formally?", "Give me a similar example"],

  dailyLabel: "Pattern of the day: {name}",

  // TOPICS[].tr açıklamalarının İngilizcesi (konu adına göre)
  topicDesc: {
    "Present Simple vs Present Continuous": "Habit or right now?",
    "Present Perfect": "Past action, present result",
    "Present Perfect vs Past Simple": "Never 'have' with 'ago'",
    "Present Perfect Continuous": "Ongoing with since / for",
    "Past Continuous": "What was happening at that moment?",
    "will vs going to": "Plan or quick decision?",
    "Present Continuous for future plans": "We're meeting on Friday",
    "should / must / have to": "Obligation and advice",
    "could / would / might for politeness": "Polite requests and suggestions",
    "First Conditional": "If + present, will",
    "Second Conditional": "Imaginary situations",
    "Third Conditional": "Regrets about the past",
    "Passive Voice": "The bug was fixed",
    "Relative Clauses: who / which / that": "Linking sentences",
    "Articles: a / an / the": "Tricky: Turkish has none",
    "Countable vs Uncountable nouns": "much / many, information, feedback",
    "Prepositions of time: in / on / at": "Time, day, month",
    "Prepositions after verbs": "depend on, discuss (no preposition!)",
    "Gerund vs Infinitive": "enjoy doing / want to do",
    "used to / be used to / get used to": "Old habit or getting used to?",
    "since vs for": "Starting point or duration?",
    "already / yet / still": "Already, yet, still",
    "however / although / despite": "Contrast connectors",
    "wish / if only": "Wishes and regrets",
    "Causative: have / get something done": "Getting something done",
    "Modal verbs of deduction: must / might / can't": "Guessing and deduction",
  },
};
