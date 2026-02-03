import customtkinter as ctk
import sqlite3
import threading
import api_handler
from analyzer_engine import GrammarChecker
from tkinter import messagebox


ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


PRIMARY_COLOR = "#E91E63"  
SECONDARY_COLOR = "#F5F5F5"
TEXT_COLOR = "#333333"
FONT_FAMILY = "Helvetica"

class StartPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="white")
        self.controller = controller
        self.logo_frame = ctk.CTkFrame(self, width=200, height=100, fg_color=SECONDARY_COLOR)
        self.logo_frame.pack(pady=(100, 50))
        self.logo_label = ctk.CTkLabel(self.logo_frame, text="LOGO HERE", font=(FONT_FAMILY, 20))
        self.logo_label.place(relx=0.5, rely=0.5, anchor="center")

        self.start_btn = ctk.CTkButton(self, text="BAŞLA", 
                                       font=(FONT_FAMILY, 24, "bold"),
                                       height=60, width=200, corner_radius=30,
                                       fg_color=PRIMARY_COLOR, hover_color="#C2185B",
                                       command=self.show_modes)
        self.start_btn.pack(pady=20)
        self.mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.vocab_btn = ctk.CTkButton(self.mode_frame, text="Kelime Avcısı", 
                                       font=(FONT_FAMILY, 18),
                                       height=50, width=200, corner_radius=25,
                                       fg_color=PRIMARY_COLOR, hover_color="#C2185B",
                                       command=lambda: controller.show_frame("VocabPage"))
        self.vocab_btn.pack(pady=10)

        self.chat_btn = ctk.CTkButton(self.mode_frame, text="Cümle Analizi", 
                                      font=(FONT_FAMILY, 18),
                                      height=50, width=200, corner_radius=25,
                                      fg_color=PRIMARY_COLOR, hover_color="#C2185B",
                                      command=lambda: controller.show_frame("ChatPage"))
        self.chat_btn.pack(pady=10)

    def show_modes(self):
        self.start_btn.pack_forget()
        self.mode_frame.pack(pady=20)


class VocabPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="white")
        self.controller = controller
        
        self.header = ctk.CTkFrame(self, height=50, fg_color="white")
        self.header.pack(fill="x", padx=20, pady=10)
        self.back_btn = ctk.CTkButton(self.header, text="← Geri", width=80, fg_color="transparent", text_color="black", hover=False,
                                      command=lambda: controller.show_frame("StartPage"))
        self.back_btn.pack(side="left")

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.current_word = None

    def show_cards(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        words = self.fetch_random_words(3)
        if not words:
            ctk.CTkLabel(self.content_frame, text="No new words found!", font=(FONT_FAMILY, 20)).pack(pady=50)
            return

        lbl = ctk.CTkLabel(self.content_frame, text="Bir kelime seç:", font=(FONT_FAMILY, 24, "bold"))
        lbl.pack(pady=(20, 40))

        for word in words:
            btn = ctk.CTkButton(self.content_frame, text=word, 
                                font=(FONT_FAMILY, 20),
                                height=80, width=400, 
                                fg_color=SECONDARY_COLOR, 
                                text_color=PRIMARY_COLOR,
                                hover_color="#E0E0E0",
                                command=lambda w=word: self.on_card_click(w))
            btn.pack(pady=10)

    def fetch_random_words(self, limit):
        conn = self.controller.db_conn
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT word FROM words WHERE status='new' ORDER BY RANDOM() LIMIT ?", (limit,))
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"DB Error: {e}")
            return []

    def on_card_click(self, word):
        self.current_word = word
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        loading_lbl = ctk.CTkLabel(self.content_frame, text="Yükleniyor...", font=(FONT_FAMILY, 20))
        loading_lbl.pack(pady=100)
        
        threading.Thread(target=self.load_api_details, args=(word,), daemon=True).start()

    def load_api_details(self, word):
        details = api_handler.get_word_details(word)
        self.after(0, self.update_details, details)

    def update_details(self, details):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if not details:
            ctk.CTkLabel(self.content_frame, text="Hata: Kelime bulunamadı.", font=(FONT_FAMILY, 18)).pack(pady=50)
            ctk.CTkButton(self.content_frame, text="Geri Dön", command=self.show_cards, fg_color=PRIMARY_COLOR).pack()
            return

        header_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        word_lbl = ctk.CTkLabel(header_frame, text=details['word'], font=(FONT_FAMILY, 40, "bold"), text_color="black")
        word_lbl.pack()
        
        phonetic_lbl = ctk.CTkLabel(header_frame, text=details.get('phonetic', ''), font=(FONT_FAMILY, 16), text_color="gray")
        phonetic_lbl.pack()

        meaning_frame = ctk.CTkFrame(self.content_frame, fg_color=PRIMARY_COLOR, corner_radius=10)
        meaning_frame.pack(fill="x", padx=50, pady=10)
        
        meaning_lbl = ctk.CTkLabel(meaning_frame, text=details.get('meaning_tr', 'Çeviri yok'), 
                                   font=(FONT_FAMILY, 18, "bold"), text_color="white", wraplength=500)
        meaning_lbl.pack(padx=20, pady=15)

        sentences = details.get('sentences', {})
        levels = ['A1', 'B1', 'C1']
        
        for lvl in levels:
            sent_text = sentences.get(lvl, "Cümle yok.")
            row = ctk.CTkFrame(self.content_frame, fg_color=SECONDARY_COLOR, corner_radius=8)
            row.pack(fill="x", padx=50, pady=5)
            
            lvl_lbl = ctk.CTkLabel(row, text=f"{lvl} Seviye", font=(FONT_FAMILY, 12, "bold"), text_color=PRIMARY_COLOR, width=80)
            lvl_lbl.pack(side="left", padx=10, pady=10)
            
            txt_lbl = ctk.CTkLabel(row, text=sent_text, font=(FONT_FAMILY, 14), text_color="#333", wraplength=450, justify="left")
            txt_lbl.pack(side="left", fill="x", expand=True, padx=10)

        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(pady=30)

        know_btn = ctk.CTkButton(btn_frame, text="Biliyorum", 
                                 fg_color="green", hover_color="darkgreen",
                                 width=140, height=40,
                                 command=self.mark_known)
        know_btn.pack(side="left", padx=10)

        next_btn = ctk.CTkButton(btn_frame, text="Sonraki", 
                                 fg_color="gray", hover_color="darkgray",
                                 width=140, height=40,
                                 command=self.show_cards)
        next_btn.pack(side="left", padx=10)

    def mark_known(self):
        if self.current_word:
            conn = self.controller.db_conn
            try:
                conn.execute("UPDATE words SET status='learned' WHERE word=?", (self.current_word,))
                conn.commit()
            except Exception as e:
                print(e)
        self.show_cards()


class ChatPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="white")
        self.controller = controller
        

        self.header = ctk.CTkFrame(self, height=50, fg_color="white")
        self.header.pack(fill="x", padx=20, pady=10)
        self.back_btn = ctk.CTkButton(self.header, text="← Geri", width=80, fg_color="transparent", text_color="black", hover=False,
                                      command=lambda: controller.show_frame("StartPage"))
        self.back_btn.pack(side="left")


        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=SECONDARY_COLOR)
        self.scroll_frame.pack(expand=True, fill="both", padx=20, pady=10)

        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=20, pady=20)

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="İngilizce bir cümle yazın...", height=40, font=(FONT_FAMILY, 14))
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.start_analysis())

        self.send_btn = ctk.CTkButton(self.input_frame, text="Analiz Et", 
                                      fg_color=PRIMARY_COLOR, hover_color="#C2185B",
                                      height=40, width=100,
                                      command=self.start_analysis)
        self.send_btn.pack(side="right")
        
        self.checker = GrammarChecker() 

    def start_analysis(self):
        msg = self.entry.get()
        if not msg.strip(): return
        
        self.add_bubble(msg, is_user=True)
        self.entry.delete(0, "end")
        

        self.loading_bubble = self.add_bubble("Analiz ediliyor...", is_user=False, color="#BDBDBD") 
        
        threading.Thread(target=self.run_check, args=(msg,), daemon=True).start()

    def run_check(self, text):
        result = self.checker.check_text(text)
        self.after(0, self.show_result, result)

    def show_result(self, result):

        if hasattr(self, 'loading_bubble') and self.loading_bubble:
            self.loading_bubble.destroy()
            self.loading_bubble = None

        if result['status'] == 'error':
            self.add_bubble(result['corrected'], is_user=False, color="#F44336") 
        elif not result['matches']:
             self.add_bubble("Harika! Hata yok. ✅", is_user=False, color="#4CAF50") 
        else:
             self.add_bubble(f"Düzeltme: {result['corrected']}", is_user=False, color="#4CAF50") 

    def add_bubble(self, text, is_user, color=None):
        if color:
            bg_color = color
            text_color = "white"
        else:
            bg_color = PRIMARY_COLOR if is_user else "white"
            text_color = "white" if is_user else "black"
            
        anchor = "e" if is_user else "w"
        
        bubble = ctk.CTkLabel(self.scroll_frame, text=text, 
                              fg_color=bg_color, text_color=text_color,
                              corner_radius=15, padx=15, pady=10, justify="left", wraplength=400,
                              font=(FONT_FAMILY, 14))
        bubble.pack(anchor=anchor, pady=5, padx=10)
        return bubble


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CodeVocab")
        
       
        width = 1600
        height = 900
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        self.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
        self.db_conn = None
        self.connect_db()

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (StartPage, VocabPage, ChatPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def connect_db(self):
        try:
            self.db_conn = sqlite3.connect("vocab.db", check_same_thread=False)
        except sqlite3.Error as e:
            messagebox.showerror("Init Error", f"DB Connection failed: {e}")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if page_name == "VocabPage":
            frame.show_cards()

    def on_closing(self):
        if self.db_conn:
            self.db_conn.close()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
