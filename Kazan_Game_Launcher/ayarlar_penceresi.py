import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import tarayici
import config


class AyarlarPenceresi(tk.Toplevel):
    """
    Tarama yapar, kullanıcının hangi oyunları başlatıcıda görmek istediğini
    işaretlemesini sağlar ve sonucu ana uygulamaya geri bildirir.
    """

    def __init__(self, master, ayarlar, kaydet_callback):
        super().__init__(master)
        self.title("Oyun Başlatıcı 2.2.0 - Ayarlar")
        self.geometry("550x640")
        self.minsize(500, 520)
        self.ayarlar = ayarlar
        self.kaydet_callback = kaydet_callback

        # id -> (oyun_sozlugu, BooleanVar)
        self.satirlar = {}

        self._arayuzu_kur()
        self._mevcut_ayarlari_yukle()

    # ------------------------------------------------------------------
    def _arayuzu_kur(self):
        ust_cerceve = ttk.Frame(self, padding=10)
        ust_cerceve.pack(fill="x")

        ttk.Button(ust_cerceve, text="Steam oyunlarını tara",
                   command=self._steam_tara).grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        ttk.Button(ust_cerceve, text="Epic oyunlarını tara",
                   command=self._epic_tara).grid(row=0, column=1, sticky="ew", padx=3, pady=3)
        ttk.Button(ust_cerceve, text="Klasör ekle / tara",
                   command=self._klasor_ekle).grid(row=1, column=0, sticky="ew", padx=3, pady=3)
        ttk.Button(ust_cerceve, text="Tek dosya ekle (.exe/.lnk/.url)",
                   command=self._manuel_dosya_ekle).grid(row=1, column=1, sticky="ew", padx=3, pady=3)
        ust_cerceve.columnconfigure((0, 1), weight=1)

        genel_cerceve = ttk.Frame(self, padding=(10, 0, 10, 6))
        genel_cerceve.pack(fill="x")

        self.oled_var = tk.BooleanVar(value=self.ayarlar.get("oled_koruma", False))
        ttk.Checkbutton(
            genel_cerceve, variable=self.oled_var,
            text="OLED koruması: fare üzerinde değilken simgeyi gizle"
        ).pack(side="left")

        self.otomatik_guncelleme_var = tk.BooleanVar(
            value=self.ayarlar.get("otomatik_guncelleme", True)
        )
        ttk.Checkbutton(
            genel_cerceve, variable=self.otomatik_guncelleme_var,
            text="Güncellemeleri otomatik indir ve uygula"
        ).pack(side="left", padx=(15, 0))

        hiz_cerceve = ttk.Frame(self, padding=(10, 0, 10, 6))
        hiz_cerceve.pack(fill="x")
        ttk.Label(hiz_cerceve, text="Üzerinde bekleme (ms):").pack(side="left")
        self.hover_var = tk.StringVar(value=str(config.hover_suresi(self.ayarlar)))
        ttk.Spinbox(hiz_cerceve, from_=50, to=1000, increment=25, width=6,
                    textvariable=self.hover_var).pack(side="left", padx=6)
        ttk.Label(hiz_cerceve, text="150 ms = 0,15 saniye").pack(side="left")

        simge_cerceve = ttk.Frame(self, padding=(10, 0, 10, 6))
        simge_cerceve.pack(fill="x")
        ttk.Label(simge_cerceve, text="Masaüstü simgesi:").pack(side="left")
        ttk.Button(simge_cerceve, text="Simgeyi Değiştir",
                   command=self._simge_degistir).pack(side="left", padx=5)
        ttk.Button(simge_cerceve, text="Varsayılana Döndür",
                   command=self._simge_varsayilana_dondur).pack(side="left")

        bilgi = ttk.Label(
            self,
            text="Başlatıcıda görünmesini istediğin oyunları işaretle. "
                 "Taramalar sadece bulur, hiçbir şeyi silmez.",
            wraplength=440, justify="left"
        )
        bilgi.pack(fill="x", padx=10, pady=(0, 5))

        # kaydırılabilir liste alanı
        kapsayici = ttk.Frame(self)
        kapsayici.pack(fill="both", expand=True, padx=10)

        self.canvas = tk.Canvas(kapsayici, highlightthickness=0)
        scrollbar = ttk.Scrollbar(kapsayici, orient="vertical", command=self.canvas.yview)
        self.liste_cercevesi = ttk.Frame(self.canvas)

        self.liste_cercevesi.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        ic_pencere = self.canvas.create_window((0, 0), window=self.liste_cercevesi, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(ic_pencere, width=e.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 120), "units"))

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # alt buton satırı
        alt_cerceve = ttk.Frame(self, padding=10)
        alt_cerceve.pack(fill="x")
        ttk.Button(alt_cerceve, text="Tümünü Seç", command=self._tumunu_sec).pack(side="left")
        ttk.Button(alt_cerceve, text="Tümünü Kaldır", command=self._tumunu_kaldir).pack(side="left", padx=5)
        ttk.Button(alt_cerceve, text="Kaydet ve Kapat", command=self._kaydet_ve_kapat).pack(side="right")

    # ------------------------------------------------------------------
    def _satir_ekle(self, oyun):
        """oyun listeye zaten yoksa yeni bir satır (checkbox) ekler."""
        if oyun["id"] in self.satirlar:
            self.satirlar[oyun["id"]][0].update(oyun)
            return
        var = tk.BooleanVar(value=True)
        satir = ttk.Frame(self.liste_cercevesi)
        satir.pack(fill="x", pady=1)
        ttk.Checkbutton(satir, variable=var).pack(side="left")
        etiket = f'{oyun["ad"]}   [{oyun["tur"]}]'
        ttk.Label(satir, text=etiket).pack(side="left", padx=4)
        self.satirlar[oyun["id"]] = (oyun, var)

    def _mevcut_ayarlari_yukle(self):
        for oyun in self.ayarlar.get("oyunlar", []):
            self._satir_ekle(oyun)
            if oyun["id"] in self.satirlar:
                self.satirlar[oyun["id"]][1].set(oyun.get("aktif", True))

    # ------------------------------------------------------------------
    def _steam_tara(self):
        bulunanlar = tarayici.steam_oyunlarini_bul()
        if not bulunanlar:
            messagebox.showinfo("Steam", "Steam kurulumu veya oyun bulunamadı.")
            return
        for oyun in bulunanlar:
            self._satir_ekle(oyun)
        messagebox.showinfo("Steam", f"{len(bulunanlar)} Steam oyunu bulundu.")

    def _epic_tara(self):
        bulunanlar = tarayici.epic_oyunlarini_bul()
        if not bulunanlar:
            messagebox.showinfo("Epic Games", "Epic Games kurulumu veya oyun bulunamadı.")
            return
        for oyun in bulunanlar:
            self._satir_ekle(oyun)
        messagebox.showinfo("Epic Games", f"{len(bulunanlar)} Epic oyunu bulundu.")

    def _klasor_ekle(self):
        klasor = filedialog.askdirectory(title="Oyunların bulunduğu klasörü seç")
        if not klasor:
            return
        ozel_klasorler = self.ayarlar.setdefault("ozel_klasorler", [])
        if klasor not in ozel_klasorler:
            ozel_klasorler.append(klasor)
        bulunanlar = tarayici.klasor_tara(klasor)
        for oyun in bulunanlar:
            self._satir_ekle(oyun)
        messagebox.showinfo("Klasör Tarama", f"{len(bulunanlar)} çalıştırılabilir dosya bulundu.")

    def _manuel_dosya_ekle(self):
        dosya = filedialog.askopenfilename(
            title="Oyun exe veya kısayolunu seç",
            filetypes=[("Çalıştırılabilir / Kısayol", "*.exe *.lnk *.url")]
        )
        if not dosya:
            return
        ad = os.path.splitext(os.path.basename(dosya))[0]
        import tarayici as t
        oyun = {
            "id": f"ozel_{t._id_uret(dosya)}",
            "ad": ad,
            "tur": "ozel",
            "komut": dosya,
        }
        self._satir_ekle(oyun)

    # ------------------------------------------------------------------
    def _simge_degistir(self):
        dosya = filedialog.askopenfilename(
            title="Masaüstü simgesi olarak kullanılacak görseli seç",
            filetypes=[("Resim dosyaları", "*.png *.jpg *.jpeg *.bmp *.ico")]
        )
        if not dosya:
            return
        self.ayarlar["ozel_simge_yolu"] = dosya
        messagebox.showinfo("Simge", "Yeni simge seçildi, 'Kaydet ve Kapat' ile uygulanacak.")

    def _simge_varsayilana_dondur(self):
        self.ayarlar["ozel_simge_yolu"] = None
        messagebox.showinfo("Simge", "Varsayılan oyun kolu simgesine dönülecek.")

    # ------------------------------------------------------------------
    def _tumunu_sec(self):
        for _, var in self.satirlar.values():
            var.set(True)

    def _tumunu_kaldir(self):
        for _, var in self.satirlar.values():
            var.set(False)

    def _kaydet_ve_kapat(self):
        try:
            hover_ms = int(self.hover_var.get())
            if not 50 <= hover_ms <= 1000:
                raise ValueError
        except ValueError:
            messagebox.showerror("Bekleme süresi", "50 ile 1000 arasında bir sayı gir.", parent=self)
            return
        yeni_liste = []
        for oyun, var in self.satirlar.values():
            oyun_kopya = dict(oyun)
            oyun_kopya["aktif"] = var.get()
            yeni_liste.append(oyun_kopya)
        self.ayarlar["oyunlar"] = yeni_liste
        self.ayarlar["oled_koruma"] = self.oled_var.get()
        self.ayarlar["otomatik_guncelleme"] = self.otomatik_guncelleme_var.get()
        self.ayarlar["hover_bekleme_ms"] = hover_ms
        self.kaydet_callback(self.ayarlar)
        self.destroy()
