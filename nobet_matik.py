# -- coding: utf-8 --

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
from datetime import date, timedelta
from collections import defaultdict
import pandas as pd
from tkcalendar import DateEntry
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import platform

class NobetUygulamasi:
    def __init__(self, root):
        self.root = root
        self.root.title("Okul Nöbet Yönetim Sistemi")
        self.root.geometry("1200x850")

        self.style = ttk.Style(self.root)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        
        self.icon_font = ("Arial", 12)

        self.db_baglantisi_kur()
        self.tablolari_olustur()

        self.ana_arayuzu_olustur()
        
        self.personel_listesini_yenile()
        self.nobet_yerlerini_yenile()
        self.nobet_cizelgesini_yenile()

        # Filtre haritalamaları için
        self.personel_ad_id_map = {}
        self.yer_ad_id_map = {}
        self.filtre_verilerini_yukle() 
        
        self.ayarlari_yukle()


    def db_baglantisi_kur(self):
        self.conn = sqlite3.connect("nobet_sistemi.db")
        self.cursor = self.conn.cursor()

    def tablolari_olustur(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS personel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT NOT NULL,
                soyad TEXT NOT NULL,
                brans TEXT,
                gunler TEXT,
                tur TEXT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS nobet_yerleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                yer_adi TEXT NOT NULL UNIQUE
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS nobet_cizelgesi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih TEXT NOT NULL,
                personel_id INTEGER,
                yer_id INTEGER,
                FOREIGN KEY(personel_id) REFERENCES personel(id) ON DELETE CASCADE,
                FOREIGN KEY(yer_id) REFERENCES nobet_yerleri(id) ON DELETE CASCADE
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ayarlar (
                anahtar TEXT PRIMARY KEY,
                deger TEXT
            )
        """)
        self.conn.commit()

    def ana_arayuzu_olustur(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=(10, 5))

        self.modul1 = ttk.Frame(self.notebook)
        self.notebook.add(self.modul1, text=" Personel ve Yer Yönetimi ")
        self.modul1_arayuz_olustur()

        self.modul2 = ttk.Frame(self.notebook)
        self.notebook.add(self.modul2, text=" Nöbet Dağıtımı ")
        self.modul2_arayuz_olustur()

        self.modul3 = ttk.Frame(self.notebook)
        self.notebook.add(self.modul3, text=" Raporlama ")
        self.modul3_arayuz_olustur()

        gunun_nobetci_frame = ttk.LabelFrame(self.root, text="Bugünün Nöbetçileri", padding=10)
        gunun_nobetci_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.gunun_nobetci_tree = ttk.Treeview(gunun_nobetci_frame, columns=("personel", "yer"), show="headings", height=3)
        self.gunun_nobetci_tree.heading("personel", text="Görevli Personel")
        self.gunun_nobetci_tree.heading("yer", text="Nöbet Yeri")
        self.gunun_nobetci_tree.pack(side="left", fill="x", expand=True)
        
        gunun_scrollbar = ttk.Scrollbar(gunun_nobetci_frame, orient="vertical", command=self.gunun_nobetci_tree.yview)
        self.gunun_nobetci_tree.configure(yscrollcommand=gunun_scrollbar.set)
        gunun_scrollbar.pack(side="right", fill="y")

    def modul1_arayuz_olustur(self):
        sol_frame = ttk.Frame(self.modul1)
        sol_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        personel_frame = ttk.LabelFrame(sol_frame, text="Personel Yönetimi", padding=10)
        personel_frame.pack(fill="both", expand=True)

        yer_frame = ttk.LabelFrame(self.modul1, text="Nöbet Yeri Yönetimi", padding=10)
        yer_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        form_frame = ttk.Frame(personel_frame)
        form_frame.pack(fill="x", pady=5)

        ttk.Label(form_frame, text="Ad:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.p_ad = ttk.Entry(form_frame)
        self.p_ad.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        ttk.Label(form_frame, text="Soyad:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.p_soyad = ttk.Entry(form_frame)
        self.p_soyad.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(form_frame, text="Branş:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.p_brans = ttk.Entry(form_frame)
        self.p_brans.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        
        ttk.Label(form_frame, text="Tür:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.p_tur = ttk.Combobox(form_frame, values=["Öğretmen", "Müdür Yardımcısı"], state="readonly")
        self.p_tur.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        self.p_tur.set("Öğretmen")

        gunler_frame = ttk.LabelFrame(form_frame, text="Nöbet Tutabileceği Günler")
        gunler_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        self.gun_vars = {}
        gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        for i, gun in enumerate(gunler):
            self.gun_vars[gun] = tk.BooleanVar()
            cb = ttk.Checkbutton(gunler_frame, text=gun, variable=self.gun_vars[gun])
            cb.pack(side="left", padx=5)

        buton_frame = ttk.Frame(form_frame)
        buton_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(buton_frame, text="➕ Ekle", command=self.personel_ekle).pack(side="left", padx=5)
        ttk.Button(buton_frame, text="🔄 Güncelle", command=self.personel_guncelle).pack(side="left", padx=5)
        ttk.Button(buton_frame, text="🗑 Sil", command=self.personel_sil).pack(side="left", padx=5)
        ttk.Button(buton_frame, text="📋 Formu Temizle", command=self.personel_formu_temizle).pack(side="left", padx=5)

        paned_window = ttk.PanedWindow(sol_frame, orient=tk.VERTICAL)
        paned_window.pack(fill="both", expand=True)

        personel_list_frame = ttk.Frame(paned_window)
        paned_window.add(personel_list_frame, weight=3)

        tree_frame = ttk.Frame(personel_list_frame)
        tree_frame.pack(expand=True, fill="both", pady=5)
        self.personel_tree = ttk.Treeview(tree_frame, columns=("id", "ad", "soyad", "brans", "tur", "gunler"), show="headings")
        self.personel_tree.heading("id", text="ID")
        self.personel_tree.heading("ad", text="Ad")
        self.personel_tree.heading("soyad", text="Soyad")
        self.personel_tree.heading("brans", text="Branş")
        self.personel_tree.heading("tur", text="Tür")
        self.personel_tree.heading("gunler", text="Uygun Günler")
        self.personel_tree.column("id", width=30)
        self.personel_tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.personel_tree.yview)
        self.personel_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.personel_tree.bind("<<TreeviewSelect>>", self.personel_secildi)

        personel_nobet_frame = ttk.LabelFrame(paned_window, text="Seçili Personelin Nöbetleri", padding=10)
        paned_window.add(personel_nobet_frame, weight=2)

        self.secili_personel_nobet_tree = ttk.Treeview(personel_nobet_frame, columns=("tarih", "gun", "yer"), show="headings")
        self.secili_personel_nobet_tree.heading("tarih", text="Tarih")
        self.secili_personel_nobet_tree.heading("gun", text="Gün")
        self.secili_personel_nobet_tree.heading("yer", text="Nöbet Yeri")
        self.secili_personel_nobet_tree.column("tarih", width=120)
        self.secili_personel_nobet_tree.column("gun", width=120)
        self.secili_personel_nobet_tree.pack(side="left", fill="both", expand=True)
        
        personel_nobet_scrollbar = ttk.Scrollbar(personel_nobet_frame, orient="vertical", command=self.secili_personel_nobet_tree.yview)
        self.secili_personel_nobet_tree.configure(yscrollcommand=personel_nobet_scrollbar.set)
        personel_nobet_scrollbar.pack(side="right", fill="y")

        yer_form_frame = ttk.Frame(yer_frame)
        yer_form_frame.pack(fill="x", pady=5)
        ttk.Label(yer_form_frame, text="Nöbet Yeri Adı:").pack(side="left", padx=5)
        self.yer_adi_entry = ttk.Entry(yer_form_frame)
        self.yer_adi_entry.pack(side="left", expand=True, fill="x", padx=5)
        
        yer_buton_frame = ttk.Frame(yer_frame)
        yer_buton_frame.pack(fill="x", pady=10)
        ttk.Button(yer_buton_frame, text="➕ Ekle", command=self.nobet_yeri_ekle).pack(side="left", padx=5)
        ttk.Button(yer_buton_frame, text="🗑 Sil", command=self.nobet_yeri_sil).pack(side="left", padx=5)

        self.nobet_yeri_listbox = tk.Listbox(yer_frame)
        self.nobet_yeri_listbox.pack(expand=True, fill="both", pady=5)

    def personel_formu_temizle(self):
        self.p_ad.delete(0, 'end')
        self.p_soyad.delete(0, 'end')
        self.p_brans.delete(0, 'end')
        self.p_tur.set("Öğretmen")
        for var in self.gun_vars.values():
            var.set(False)
        if self.personel_tree.selection():
            self.personel_tree.selection_remove(self.personel_tree.selection())
        for i in self.secili_personel_nobet_tree.get_children():
            self.secili_personel_nobet_tree.delete(i)

    def personel_ekle(self):
        ad = self.p_ad.get().strip()
        soyad = self.p_soyad.get().strip()
        brans = self.p_brans.get().strip()
        tur = self.p_tur.get()
        gunler = [gun for gun, var in self.gun_vars.items() if var.get()]
        gunler_str = ",".join(gunler)

        if not ad or not soyad or not tur:
            messagebox.showerror("Hata", "Ad, Soyad ve Tür alanları boş bırakılamaz.")
            return

        try:
            self.cursor.execute("INSERT INTO personel (ad, soyad, brans, gunler, tur) VALUES (?, ?, ?, ?, ?)",
                                (ad, soyad, brans, gunler_str, tur))
            self.conn.commit()
            messagebox.showinfo("Başarılı", f"{ad} {soyad} başarıyla eklendi.")
            self.personel_formu_temizle()
            self.personel_listesini_yenile()
        except Exception as e:
            messagebox.showerror("Veritabanı Hatası", f"Bir hata oluştu: {e}")

    def personel_guncelle(self):
        selected_item = self.personel_tree.selection()
        if not selected_item:
            messagebox.showerror("Hata", "Lütfen güncellenecek bir personel seçin.")
            return
        
        personel_id = self.personel_tree.item(selected_item[0])['values'][0]
        ad = self.p_ad.get().strip()
        soyad = self.p_soyad.get().strip()
        brans = self.p_brans.get().strip()
        tur = self.p_tur.get()
        gunler = [gun for gun, var in self.gun_vars.items() if var.get()]
        gunler_str = ",".join(gunler)

        if not ad or not soyad or not tur:
            messagebox.showerror("Hata", "Ad, Soyad ve Tür alanları boş bırakılamaz.")
            return

        try:
            self.cursor.execute("""
                UPDATE personel SET ad=?, soyad=?, brans=?, gunler=?, tur=? WHERE id=?
            """, (ad, soyad, brans, gunler_str, tur, personel_id))
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Personel bilgileri güncellendi.")
            self.personel_formu_temizle()
            self.personel_listesini_yenile()
        except Exception as e:
            messagebox.showerror("Veritabanı Hatası", f"Bir hata oluştu: {e}")

    def personel_sil(self):
        selected_item = self.personel_tree.selection()
        if not selected_item:
            messagebox.showerror("Hata", "Lütfen silinecek bir personel seçin.")
            return
        
        personel_id = self.personel_tree.item(selected_item[0])['values'][0]
        ad_soyad = f"{self.personel_tree.item(selected_item[0])['values'][1]} {self.personel_tree.item(selected_item[0])['values'][2]}"
        
        if messagebox.askyesno("Onay", f"{ad_soyad} adlı kişiyi silmek istediğinize emin misiniz? Bu işlem personelin tüm nöbet kayıtlarını da silecektir."):
            try:
                self.cursor.execute("DELETE FROM personel WHERE id=?", (personel_id,))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Personel başarıyla silindi.")
                self.personel_formu_temizle()
                self.personel_listesini_yenile()
                self.nobet_cizelgesini_yenile()
            except Exception as e:
                messagebox.showerror("Veritabanı Hatası", f"Bir hata oluştu: {e}")

    def personel_listesini_yenile(self):
        for i in self.personel_tree.get_children():
            self.personel_tree.delete(i)
        self.cursor.execute("SELECT id, ad, soyad, brans, tur, gunler FROM personel ORDER BY ad, soyad")
        for row in self.cursor.fetchall():
            self.personel_tree.insert("", "end", values=row)
        if hasattr(self, 'filtre_personel_combo'): # Program ilk açılırken hata vermemesi için
            self.filtre_verilerini_yukle() 

    def personel_secildi(self, event):
        selected_item = self.personel_tree.selection()
        if not selected_item:
            return

        self.p_ad.delete(0, 'end')
        self.p_soyad.delete(0, 'end')
        self.p_brans.delete(0, 'end')
        self.p_tur.set("Öğretmen")
        for var in self.gun_vars.values():
            var.set(False)
        for i in self.secili_personel_nobet_tree.get_children():
            self.secili_personel_nobet_tree.delete(i)
            
        item = self.personel_tree.item(selected_item[0])['values']
        personel_id, ad, soyad, brans, tur, gunler_str = item
        
        self.p_ad.insert(0, ad)
        self.p_soyad.insert(0, soyad)
        self.p_brans.insert(0, brans)
        self.p_tur.set(tur)
        
        if gunler_str:
            gunler = gunler_str.split(',')
            for gun in gunler:
                if gun in self.gun_vars:
                    self.gun_vars[gun].set(True)

        query = """
            SELECT nc.tarih, ny.yer_adi
            FROM nobet_cizelgesi nc
            JOIN nobet_yerleri ny ON nc.yer_id = ny.id
            WHERE nc.personel_id = ?
            ORDER BY nc.tarih DESC
        """
        self.cursor.execute(query, (personel_id,))
        gunler_map = {0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar"}
        
        for tarih_str, yer_adi in self.cursor.fetchall():
            try:
                tarih_obj = date.fromisoformat(tarih_str)
                gun_adi = gunler_map.get(tarih_obj.weekday(), "Bilinmiyor")
                self.secili_personel_nobet_tree.insert("", "end", values=(tarih_obj.strftime("%d.%m.%Y"), gun_adi, yer_adi))
            except (ValueError, KeyError):
                continue

    def nobet_yeri_ekle(self):
        yer_adi = self.yer_adi_entry.get().strip()
        if not yer_adi:
            messagebox.showerror("Hata", "Nöbet yeri adı boş bırakılamaz.")
            return
        try:
            self.cursor.execute("INSERT INTO nobet_yerleri (yer_adi) VALUES (?)", (yer_adi,))
            self.conn.commit()
            self.yer_adi_entry.delete(0, 'end')
            self.nobet_yerlerini_yenile()
        except sqlite3.IntegrityError:
            messagebox.showerror("Hata", "Bu nöbet yeri zaten mevcut.")
        except Exception as e:
            messagebox.showerror("Veritabanı Hatası", f"Bir hata oluştu: {e}")

    def nobet_yeri_sil(self):
        selected_index = self.nobet_yeri_listbox.curselection()
        if not selected_index:
            messagebox.showerror("Hata", "Lütfen silinecek bir nöbet yeri seçin.")
            return
            
        yer_adi = self.nobet_yeri_listbox.get(selected_index)
        if messagebox.askyesno("Onay", f"'{yer_adi}' adlı nöbet yerini silmek istediğinize emin misiniz?"):
            try:
                self.cursor.execute("DELETE FROM nobet_yerleri WHERE yer_adi=?", (yer_adi,))
                self.conn.commit()
                self.nobet_yerlerini_yenile()
                self.nobet_cizelgesini_yenile()
            except Exception as e:
                messagebox.showerror("Veritabanı Hatası", f"Bir hata oluştu: {e}")

    def nobet_yerlerini_yenile(self):
        self.nobet_yeri_listbox.delete(0, 'end')
        self.cursor.execute("SELECT yer_adi FROM nobet_yerleri ORDER BY yer_adi")
        for row in self.cursor.fetchall():
            self.nobet_yeri_listbox.insert('end', row[0])
        if hasattr(self, 'filtre_yer_combo'): # Program ilk açılırken hata vermemesi için
            self.filtre_verilerini_yukle()

    def modul2_arayuz_olustur(self):
        ust_frame = ttk.LabelFrame(self.modul2, text="Nöbet İşlemleri", padding=10)
        ust_frame.pack(fill="x", padx=5, pady=5)
        
        otomatik_frame = ttk.Frame(ust_frame)
        otomatik_frame.pack(side="left", padx=10)
        ttk.Label(otomatik_frame, text="Başlangıç Tarihi:").grid(row=0, column=0, pady=2)
        self.bas_tarih_entry = DateEntry(otomatik_frame, date_pattern='dd.mm.yyyy')
        self.bas_tarih_entry.grid(row=0, column=1, pady=2)
        
        ttk.Label(otomatik_frame, text="Bitiş Tarihi:").grid(row=1, column=0, pady=2)
        self.bit_tarih_entry = DateEntry(otomatik_frame, date_pattern='dd.mm.yyyy')
        self.bit_tarih_entry.grid(row=1, column=1, pady=2)

        ttk.Button(otomatik_frame, text="🤖 Otomatik Nöbet Dağıt", command=self.otomatik_nobet_dagit).grid(row=2, column=0, columnspan=2, pady=10)
        
        manuel_frame = ttk.Frame(ust_frame)
        manuel_frame.pack(side="left", padx=20)
        ttk.Label(manuel_frame, text="Seçili Nöbeti:").grid(row=0, column=0, columnspan=2)
        self.sil_tekli_buton = ttk.Button(manuel_frame, text="🗑 Sil", command=self.secili_nobeti_sil)
        self.sil_tekli_buton.grid(row=1, column=0, pady=5)
        self.devret_buton = ttk.Button(manuel_frame, text="🔄 Devret", command=self.nobet_devret_penceresi)
        self.devret_buton.grid(row=1, column=1, pady=5, padx=5)

        aralik_sil_frame = ttk.Frame(ust_frame)
        aralik_sil_frame.pack(side="left", padx=20)
        ttk.Label(aralik_sil_frame, text="Tarih Aralığındaki Nöbetleri Sil:").grid(row=0, column=0, columnspan=2, pady=2)
        self.sil_bas_tarih = DateEntry(aralik_sil_frame, date_pattern='dd.mm.yyyy')
        self.sil_bas_tarih.grid(row=1, column=0, pady=2, padx=2)
        self.sil_bit_tarih = DateEntry(aralik_sil_frame, date_pattern='dd.mm.yyyy')
        self.sil_bit_tarih.grid(row=1, column=1, pady=2, padx=2)
        ttk.Button(aralik_sil_frame, text="💥 Aralığı Sil", command=self.araliktaki_nobetleri_sil).grid(row=2, column=0, columnspan=2, pady=5)
        
        # --- YENİ FİLTRELEME ÇERÇEVESİ ---
        filtre_frame = ttk.LabelFrame(self.modul2, text="Filtrele", padding=10)
        filtre_frame.pack(fill="x", padx=5, pady=(0, 5))

        ttk.Label(filtre_frame, text="Tarih Aralığı:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.filtre_bas_tarih = DateEntry(filtre_frame, date_pattern='dd.mm.yyyy', width=12)
        self.filtre_bas_tarih.grid(row=0, column=1, padx=2, pady=5)
        self.filtre_bas_tarih.set_date(None) # Başlangıçta boş olması için
        ttk.Label(filtre_frame, text="-").grid(row=0, column=2, padx=2)
        self.filtre_bit_tarih = DateEntry(filtre_frame, date_pattern='dd.mm.yyyy', width=12)
        self.filtre_bit_tarih.grid(row=0, column=3, padx=(2,10), pady=5)
        self.filtre_bit_tarih.set_date(None) # Başlangıçta boş olması için

        ttk.Label(filtre_frame, text="Nöbet Yeri:").grid(row=0, column=4, padx=(10, 5), pady=5, sticky="w")
        self.filtre_yer_combo = ttk.Combobox(filtre_frame, state="readonly", width=25)
        self.filtre_yer_combo.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(filtre_frame, text="Personel:").grid(row=0, column=6, padx=(10, 5), pady=5, sticky="w")
        self.filtre_personel_combo = ttk.Combobox(filtre_frame, state="readonly", width=25)
        self.filtre_personel_combo.grid(row=0, column=7, padx=5, pady=5)
        
        buton_filtre_frame = ttk.Frame(filtre_frame)
        buton_filtre_frame.grid(row=0, column=8, padx=20)
        ttk.Button(buton_filtre_frame, text="🔍 Filtrele", command=self.nobet_cizelgesini_yenile).pack(side="left", padx=5)
        ttk.Button(buton_filtre_frame, text="🔄 Temizle", command=self.filtreleri_temizle).pack(side="left")
        # --- FİLTRELEME ÇERÇEVESİ SONU ---

        cizelge_frame = ttk.Frame(self.modul2)
        cizelge_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        sol_cizelge_frame = ttk.LabelFrame(cizelge_frame, text="Haftalık Nöbet Çizelgesi", padding=10)
        sol_cizelge_frame.pack(side="left", fill="both", expand=True)

        sag_istatistik_frame = ttk.LabelFrame(cizelge_frame, text="Nöbet İstatistikleri", padding=10)
        sag_istatistik_frame.pack(side="right", fill="y")
        
        self.nobet_tree = ttk.Treeview(sol_cizelge_frame, columns=("id", "tarih", "gun", "yer", "personel", "brans"), show="headings")
        self.nobet_tree.heading("id", text="ID")
        self.nobet_tree.heading("tarih", text="Tarih")
        self.nobet_tree.heading("gun", text="Gün")
        self.nobet_tree.heading("yer", text="Nöbet Yeri")
        self.nobet_tree.heading("personel", text="Görevli Personel")
        self.nobet_tree.heading("brans", text="Branşı")
        self.nobet_tree.column("id", width=30)
        self.nobet_tree.column("tarih", width=100)
        self.nobet_tree.column("gun", width=100)
        self.nobet_tree.pack(side="left", fill="both", expand=True)
        
        cizelge_scrollbar = ttk.Scrollbar(sol_cizelge_frame, orient="vertical", command=self.nobet_tree.yview)
        self.nobet_tree.configure(yscrollcommand=cizelge_scrollbar.set)
        cizelge_scrollbar.pack(side="right", fill="y")
        
        self.istatistik_tree = ttk.Treeview(sag_istatistik_frame, columns=("personel", "toplam"), show="headings")
        self.istatistik_tree.heading("personel", text="Personel")
        self.istatistik_tree.heading("toplam", text="Toplam Nöbet")
        self.istatistik_tree.column("toplam", width=100, anchor="center")
        self.istatistik_tree.pack(fill="both", expand=True)
    
    def filtre_verilerini_yukle(self):
        """Filtreleme combobox'larını veritabanından gelen verilerle doldurur."""
        # Personel
        self.cursor.execute("SELECT id, ad, soyad FROM personel ORDER BY ad, soyad")
        personeller = self.cursor.fetchall()
        self.personel_ad_id_map = {f"{ad} {soyad}": p_id for p_id, ad, soyad in personeller}
        
        personel_listesi = ["Tümü"] + list(self.personel_ad_id_map.keys())
        self.filtre_personel_combo['values'] = personel_listesi
        self.filtre_personel_combo.set("Tümü")

        # Nöbet Yerleri
        self.cursor.execute("SELECT id, yer_adi FROM nobet_yerleri ORDER BY yer_adi")
        yerler = self.cursor.fetchall()
        self.yer_ad_id_map = {yer_adi: yer_id for yer_id, yer_adi in yerler}

        yer_listesi = ["Tümü"] + list(self.yer_ad_id_map.keys())
        self.filtre_yer_combo['values'] = yer_listesi
        self.filtre_yer_combo.set("Tümü")

    def filtreleri_temizle(self):
        """Tüm filtre widget'larını varsayılan durumuna getirir ve listeyi yeniler."""
        self.filtre_bas_tarih.set_date(None)
        self.filtre_bit_tarih.set_date(None)
        self.filtre_yer_combo.set("Tümü")
        self.filtre_personel_combo.set("Tümü")
        self.nobet_cizelgesini_yenile()

    def nobet_cizelgesini_yenile(self):
        for i in self.nobet_tree.get_children():
            self.nobet_tree.delete(i)

        # --- FİLTRELEME MANTIĞI ---
        base_query = """
            SELECT nc.id, nc.tarih, p.ad, p.soyad, ny.yer_adi, p.brans
            FROM nobet_cizelgesi nc
            JOIN personel p ON nc.personel_id = p.id
            JOIN nobet_yerleri ny ON nc.yer_id = ny.id
        """
        
        where_clauses = []
        params = []

        # Tarih filtresi
        try:
            bas_tarih = self.filtre_bas_tarih.get_date()
            bit_tarih = self.filtre_bit_tarih.get_date()
            if bas_tarih and bit_tarih:
                if bas_tarih > bit_tarih:
                    messagebox.showwarning("Uyarı", "Başlangıç tarihi bitiş tarihinden sonra olamaz. Tarih filtresi uygulanmayacak.")
                else:
                    where_clauses.append("nc.tarih BETWEEN ? AND ?")
                    params.extend([bas_tarih.isoformat(), bit_tarih.isoformat()])
        except (TypeError, ValueError):
            # Tarih seçilmemişse veya geçersizse görmezden gel
            pass

        # Nöbet yeri filtresi
        secili_yer = self.filtre_yer_combo.get()
        if secili_yer and secili_yer != "Tümü":
            yer_id = self.yer_ad_id_map.get(secili_yer)
            if yer_id:
                where_clauses.append("nc.yer_id = ?")
                params.append(yer_id)

        # Personel filtresi
        secili_personel = self.filtre_personel_combo.get()
        if secili_personel and secili_personel != "Tümü":
            personel_id = self.personel_ad_id_map.get(secili_personel)
            if personel_id:
                where_clauses.append("nc.personel_id = ?")
                params.append(personel_id)

        # Sorguyu birleştir
        if where_clauses:
            query = base_query + " WHERE " + " AND ".join(where_clauses)
        else:
            query = base_query
            
        query += " ORDER BY nc.tarih, ny.yer_adi"
        # --- FİLTRELEME MANTIĞI SONU ---

        self.cursor.execute(query, params)
        gunler_map = {0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar"}
        
        for row in self.cursor.fetchall():
            nobet_id, tarih_str, ad, soyad, yer, brans = row
            try:
                tarih_obj = date.fromisoformat(tarih_str)
                gun_adi = gunler_map.get(tarih_obj.weekday(), "Bilinmiyor")
                self.nobet_tree.insert("", "end", values=(nobet_id, tarih_obj.strftime("%d.%m.%Y"), gun_adi, yer, f"{ad} {soyad}", brans))
            except (ValueError, KeyError):
                continue
        
        self.nobet_istatistiklerini_yenile()
        self.bugunun_nobetlerini_guncelle()
        
    def nobet_istatistiklerini_yenile(self):
        for i in self.istatistik_tree.get_children():
            self.istatistik_tree.delete(i)
        
        query = """
            SELECT p.ad, p.soyad, COUNT(nc.id)
            FROM personel p
            LEFT JOIN nobet_cizelgesi nc ON p.id = nc.personel_id
            GROUP BY p.id
            ORDER BY COUNT(nc.id) DESC, p.ad, p.soyad
        """
        self.cursor.execute(query)
        for row in self.cursor.fetchall():
            ad, soyad, sayi = row
            self.istatistik_tree.insert("", "end", values=(f"{ad} {soyad}", sayi))

    def bugunun_nobetlerini_guncelle(self):
        for i in self.gunun_nobetci_tree.get_children():
            self.gunun_nobetci_tree.delete(i)
        
        bugun_tarih = date.today().isoformat()
        query = """
            SELECT p.ad, p.soyad, ny.yer_adi
            FROM nobet_cizelgesi nc
            JOIN personel p ON nc.personel_id = p.id
            JOIN nobet_yerleri ny ON nc.yer_id = ny.id
            WHERE nc.tarih = ?
            ORDER BY ny.yer_adi
        """
        self.cursor.execute(query, (bugun_tarih,))
        
        rows = self.cursor.fetchall()
        if not rows:
            self.gunun_nobetci_tree.insert("", "end", values=("Bugün nöbetçi personel bulunmamaktadır.", ""))
        else:
            for ad, soyad, yer_adi in rows:
                self.gunun_nobetci_tree.insert("", "end", values=(f"{ad} {soyad}", yer_adi))

    def otomatik_nobet_dagit(self):
        bas_tarih = self.bas_tarih_entry.get_date()
        bit_tarih = self.bit_tarih_entry.get_date()

        if bas_tarih > bit_tarih:
            messagebox.showerror("Hata", "Başlangıç tarihi bitiş tarihinden sonra olamaz.")
            return

        # 1. Gerekli verileri veritabanından çek
        self.cursor.execute("SELECT id, gunler FROM personel")
        # Güncelleme: Personel verisi çekilirken boş gün listeleri boş liste olarak tutulur.
        personel_data = {row[0]: {'gunler': row[1].split(',') if row[1] else []} for row in self.cursor.fetchall()}
        
        self.cursor.execute("SELECT id, yer_adi FROM nobet_yerleri")
        nobet_yerleri_ids = [row[0] for row in self.cursor.fetchall()]
        
        personel_sayisi = len(personel_data)
        yer_sayisi = len(nobet_yerleri_ids)

        if not personel_data or not nobet_yerleri_ids:
            messagebox.showerror("Hata", "Dağıtım için en az bir personel ve bir nöbet yeri olmalıdır.")
            return
            
        # Nöbet yerlerinin toplam slot sayısı (Pazartesi-Cuma)
        haftalik_toplam_slot = yer_sayisi * 5
        
        if personel_sayisi == 0:
             messagebox.showerror("Hata", "Personel sayısı sıfır olduğu için dağıtım yapılamıyor.")
             return
             
        # Her bir personele düşen ortalama haftalık nöbet sayısı
        ortalama_haftalik_nobet = haftalik_toplam_slot / personel_sayisi

        # Personel başına haftalık minimum ve ekstra nöbet sayısı
        min_nobet = int(ortalama_haftalik_nobet) 
        ekstra_nobet_sayisi = haftalik_toplam_slot % personel_sayisi


        # Onay istemek, çünkü bu aralıktaki eski nöbetler silinip yeniden yazılacak.
        emin_misiniz = messagebox.askyesno("Onay", 
            f"{bas_tarih.strftime('%d.%m.%Y')} - {bit_tarih.strftime('%d.%m.%Y')} tarih aralığındaki mevcut nöbetler silinip, "
            "yeni adil dağıtım kurallarına göre yeniden oluşturulacaktır.\n\nDevam etmek istiyor musunuz?")
        if not emin_misiniz:
            return

        # 2. Dağıtım başlangıcından ÖNCEKİ mevcut nöbet sayılarını hesapla (genel adalet için)
        nobet_sayilari = defaultdict(int)
        son_nobet_tarihleri = defaultdict(lambda: date.min)
        yer_gorev_sayilari = defaultdict(lambda: defaultdict(int))
        
        self.cursor.execute("SELECT personel_id, tarih, yer_id FROM nobet_cizelgesi WHERE tarih < ?", (bas_tarih.isoformat(),))
        for p_id, tarih_str, yer_id in self.cursor.fetchall():
            if p_id in personel_data:
                nobet_sayilari[p_id] += 1
                yer_gorev_sayilari[p_id][yer_id] += 1
                try:
                    tarih_obj = date.fromisoformat(tarih_str)
                    if tarih_obj > son_nobet_tarihleri[p_id]:
                        son_nobet_tarihleri[p_id] = tarih_obj
                except ValueError:
                    continue

        # 3. Hafta bazında yeni dağıtım algoritması
        gunler_map = {0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma"}
        yeni_nobetler = []
        mevcut_tarih = bas_tarih

        personel_id_listesi = list(personel_data.keys())
        
        while mevcut_tarih <= bit_tarih:
            # Sadece hafta içi (Pazartesi-Cuma) için dağıtım yap
            if mevcut_tarih.weekday() >= 5: # Cumartesi veya Pazar
                mevcut_tarih += timedelta(days=1)
                continue

            # Haftanın başlangıcını (Pazartesi) bul
            hafta_basi = mevcut_tarih - timedelta(days=mevcut_tarih.weekday())
            hafta_sonu = hafta_basi + timedelta(days=4) # Cuma

            # Eğer haftanın başlangıcı verilen aralığın dışındaysa, aralığın başından başlat
            if hafta_basi < bas_tarih:
                hafta_basi = bas_tarih
            if hafta_sonu > bit_tarih:
                hafta_sonu = bit_tarih

            # Bu hafta içindeki doldurulacak görevleri (slotları) belirle
            haftalik_gorev_slotlari = []
            gecici_tarih = hafta_basi
            while gecici_tarih <= hafta_sonu:
                if gecici_tarih.weekday() in gunler_map: # Sadece hafta içi
                    for yer_id in nobet_yerleri_ids:
                        haftalik_gorev_slotlari.append({'tarih': gecici_tarih, 'yer_id': yer_id, 'personel_id': None})
                gecici_tarih += timedelta(days=1)
            
            if not haftalik_gorev_slotlari:
                mevcut_tarih = hafta_sonu + timedelta(days=3) # Sonraki Pazartesi'ye geç
                continue
            
            # Bu hafta kimin kaç görev aldığını ve hangi gün dolu olduğunu takip et
            bu_hafta_gorev_sayisi = defaultdict(int)
            gunluk_gorevliler = defaultdict(list)

            # --- Hafta Başı Ekstra Nöbet Ataması için Personel Sıralaması ---
            personel_id_listesi.sort(key=lambda p_id: nobet_sayilari[p_id])
            ekstra_nobet_personel_ids = personel_id_listesi[:ekstra_nobet_sayisi]
            max_nobet_haftalik = {
                p_id: min_nobet + 1 if p_id in ekstra_nobet_personel_ids else min_nobet
                for p_id in personel_id_listesi
            }
            
            # --- Dağıtım Döngüsü: Gün ve Yer Bazında Atama ---
            import random
            
            # Görev slotlarını tarihe göre sıralı, yerlere göre rastgele karıştırarak adalet ve günlük dolumu sağla
            karistirilmis_gorevler = []
            gorevler_gunluk = defaultdict(list)
            for gorev in haftalik_gorev_slotlari:
                gorevler_gunluk[gorev['tarih']].append(gorev)
            
            for tarih, gorevler in gorevler_gunluk.items():
                random.shuffle(gorevler) # Aynı gün içindeki yerleri karıştır
                karistirilmis_gorevler.extend(gorevler)
            
            # Aşama 1: Normal Atama (Kota Kısıtlamasına Uyarak)
            for gorev in karistirilmis_gorevler:
                tarih, yer_id = gorev['tarih'], gorev['yer_id']
                gun_adi = gunler_map.get(tarih.weekday())

                # Uygun personel: O gün nöbet tutabilir (kısıtlama yoksa tüm günler), 
                # bu hafta maksimum nöbet sayısına ulaşmamış ve o gün başka bir göreve atanmamış.
                uygun_personeller_normal = [
                    p_id for p_id, p_info in personel_data.items()
                    # DÜZELTME: Eğer personel kısıtlı gün belirtmemişse (liste boşsa), her gün müsait sayılır.
                    if (not p_info['gunler'] or gun_adi in p_info['gunler']) 
                    and bu_hafta_gorev_sayisi[p_id] < max_nobet_haftalik.get(p_id, 0)
                    and p_id not in gunluk_gorevliler[tarih]
                ]

                if not uygun_personeller_normal:
                    continue # Bir sonraki slota geç

                # En adil personeli seç
                uygun_personeller_normal.sort(key=lambda p_id: (
                    bu_hafta_gorev_sayisi[p_id], 
                    nobet_sayilari[p_id],
                    yer_gorev_sayilari[p_id][yer_id], 
                    son_nobet_tarihleri[p_id]
                ))
                secilen_personel_id = uygun_personeller_normal[0]

                # Görevi ata ve sayaçları güncelle
                gorev['personel_id'] = secilen_personel_id
                bu_hafta_gorev_sayisi[secilen_personel_id] += 1
                gunluk_gorevliler[tarih].append(secilen_personel_id)
            
            # Aşama 2: Esnek Atama (Tüm Slotları Doldurmak İçin - Günlük Nöbetçi Zorunluluğu)
            for gorev in karistirilmis_gorevler:
                if gorev['personel_id'] is None: # Henüz atanmamış slot
                    tarih, yer_id = gorev['tarih'], gorev['yer_id']
                    gun_adi = gunler_map.get(tarih.weekday())

                    # Daha esnek uygun personel listesi: O gün nöbet tutabilir ve o gün başka bir göreve atanmamış.
                    # Hafta kotası kısıtlamasını (max_nobet_haftalik) esnetiyoruz.
                    uygun_personeller_esnek = [
                        p_id for p_id, p_info in personel_data.items()
                        if (not p_info['gunler'] or gun_adi in p_info['gunler']) # DÜZELTME: Gün uygunluğu kontrolü
                        and p_id not in gunluk_gorevliler[tarih]
                    ]
                    
                    # Eğer personel yoksa, bu slot boş kalmak zorundadır.
                    if not uygun_personeller_esnek:
                        continue 

                    # En adil personeli seç (Kota dolmuş olsa bile)
                    uygun_personeller_esnek.sort(key=lambda p_id: (
                        bu_hafta_gorev_sayisi[p_id], # En az kota aşımı yapacak kişi
                        nobet_sayilari[p_id],
                        yer_gorev_sayilari[p_id][yer_id], 
                        son_nobet_tarihleri[p_id]
                    ))
                    secilen_personel_id = uygun_personeller_esnek[0]

                    # Görevi ata ve sayaçları güncelle
                    gorev['personel_id'] = secilen_personel_id
                    bu_hafta_gorev_sayisi[secilen_personel_id] += 1
                    gunluk_gorevliler[tarih].append(secilen_personel_id)

            # Bu haftanın atamalarını ana listeye ekle ve genel sayaçları güncelle
            for gorev in karistirilmis_gorevler:
                if gorev['personel_id']:
                    p_id = gorev['personel_id']
                    yeni_nobetler.append((gorev['tarih'].isoformat(), p_id, gorev['yer_id']))
                    
                    # Genel sayaçları burada güncelle ki bir sonraki hafta döngüsü doğru hesaplansın
                    nobet_sayilari[p_id] += 1
                    yer_gorev_sayilari[p_id][gorev['yer_id']] += 1
                    son_nobet_tarihleri[p_id] = gorev['tarih']

            # Sonraki haftanın Pazartesi'sine geç
            mevcut_tarih = hafta_sonu + timedelta(days=3)

        # 4. Veritabanını güncelle
        if yeni_nobetler:
            try:
                # Önce belirtilen aralıktaki tüm eski nöbetleri temizle
                self.cursor.execute("DELETE FROM nobet_cizelgesi WHERE tarih BETWEEN ? AND ?", (bas_tarih.isoformat(), bit_tarih.isoformat()))
                # Sonra yeni oluşturulan nöbetleri ekle
                self.cursor.executemany("INSERT INTO nobet_cizelgesi (tarih, personel_id, yer_id) VALUES (?, ?, ?)", yeni_nobetler)
                self.conn.commit()
                messagebox.showinfo("Başarılı", f"{len(yeni_nobetler)} adet yeni nöbet görevi adil dağıtım kurallarına göre başarıyla oluşturuldu. Günlük nöbet zorunluluğu sağlandı.")
                self.nobet_cizelgesini_yenile()
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Veritabanı Hatası", f"Nöbetler eklenirken bir hata oluştu: {e}")
        else:
            messagebox.showinfo("Bilgi", "Belirtilen tarih aralığında ve koşullarda atanacak yeni nöbet bulunamadı.")

    def secili_nobeti_sil(self):
        selected_item = self.nobet_tree.selection()
        if not selected_item:
            messagebox.showerror("Hata", "Lütfen silinecek bir nöbet görevi seçin.")
            return
            
        nobet_id = self.nobet_tree.item(selected_item[0])['values'][0]
        if messagebox.askyesno("Onay", "Seçili nöbet görevini silmek istediğinize emin misiniz?"):
            try:
                self.cursor.execute("DELETE FROM nobet_cizelgesi WHERE id=?", (nobet_id,))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Nöbet görevi silindi.")
                self.nobet_cizelgesini_yenile()
            except Exception as e:
                messagebox.showerror("Veritabanı Hatası", f"Bir hata oluştu: {e}")

    def araliktaki_nobetleri_sil(self):
        bas_tarih = self.sil_bas_tarih.get_date().isoformat()
        bit_tarih = self.sil_bit_tarih.get_date().isoformat()

        if bas_tarih > bit_tarih:
            messagebox.showerror("Hata", "Başlangıç tarihi bitiş tarihinden sonra olamaz.")
            return
        
        if messagebox.askyesno("Onay", f"{bas_tarih} ve {bit_tarih} tarihleri arasındaki tüm nöbetleri silmek istediğinize emin misiniz? Bu işlem geri alınamaz."):
            try:
                self.cursor.execute("DELETE FROM nobet_cizelgesi WHERE tarih BETWEEN ? AND ?", (bas_tarih, bit_tarih))
                self.conn.commit()
                messagebox.showinfo("Başarılı", f"{self.cursor.rowcount} nöbet görevi silindi.")
                self.nobet_cizelgesini_yenile()
            except Exception as e:
                messagebox.showerror("Veritabanı Hatası", f"Bir hata oluştu: {e}")

    def nobet_devret_penceresi(self):
        selected_item = self.nobet_tree.selection()
        if not selected_item:
            messagebox.showerror("Hata", "Lütfen devredilecek bir nöbet görevi seçin.")
            return
            
        item_values = self.nobet_tree.item(selected_item[0])['values']
        nobet_id, tarih_str_dmy, gun_adi, _, mevcut_personel_ad_soyad, _ = item_values

        try:
            tarih_obj = date(int(tarih_str_dmy[6:]), int(tarih_str_dmy[3:5]), int(tarih_str_dmy[0:2]))
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz tarih formatı.")
            return

        self.cursor.execute("SELECT id, ad, soyad, gunler FROM personel")
        all_personel = self.cursor.fetchall()
        
        uygun_personeller = {}
        for p_id, ad, soyad, gunler_str in all_personel:
            gun_listesi = gunler_str.split(',') if gunler_str else []
            # Herkesin devralabileceği varsayımı için gün kontrolünü esnetebiliriz veya aktif bırakabiliriz.
            # Şimdilik gün uygunluğu kontrolü kalsın:
            # if (f"{ad} {soyad}" != mevcut_personel_ad_soyad) and (not gun_listesi or gun_adi in gun_listesi):
            if f"{ad} {soyad}" != mevcut_personel_ad_soyad: # Herkes herkese devredebilsin
                 self.cursor.execute("SELECT id FROM nobet_cizelgesi WHERE tarih=? AND personel_id=?", (tarih_obj.isoformat(), p_id))
                 if not self.cursor.fetchone():
                     uygun_personeller[f"{ad} {soyad}"] = p_id
        
        if not uygun_personeller:
            messagebox.showinfo("Bilgi", "Bu nöbeti devralabilecek (o gün başka nöbeti olmayan) uygun personel bulunamadı.")
            return

        devir_win = tk.Toplevel(self.root)
        devir_win.title("Nöbet Devret")
        devir_win.geometry("350x150")
        
        ttk.Label(devir_win, text=f"{tarih_str_dmy} tarihindeki nöbeti devret:").pack(pady=10)
        ttk.Label(devir_win, text=f"Mevcut Görevli: {mevcut_personel_ad_soyad}").pack()
        
        yeni_personel_combo = ttk.Combobox(devir_win, values=list(uygun_personeller.keys()), state="readonly", width=30)
        yeni_personel_combo.pack(pady=10)
        if uygun_personeller:
            yeni_personel_combo.set(list(uygun_personeller.keys())[0])
        
        def onayla():
            secilen_ad_soyad = yeni_personel_combo.get()
            if not secilen_ad_soyad:
                messagebox.showerror("Hata", "Lütfen yeni bir görevli seçin.", parent=devir_win)
                return
            
            yeni_personel_id = uygun_personeller[secilen_ad_soyad]
            try:
                self.cursor.execute("UPDATE nobet_cizelgesi SET personel_id=? WHERE id=?", (yeni_personel_id, nobet_id))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Nöbet başarıyla devredildi.")
                self.nobet_cizelgesini_yenile()
                devir_win.destroy()
            except Exception as e:
                 messagebox.showerror("Veritabanı Hatası", f"Bir hata oluştu: {e}", parent=devir_win)

        ttk.Button(devir_win, text="Devretmeyi Onayla", command=onayla).pack(pady=5)
    
    def modul3_arayuz_olustur(self):
        ayar_frame = ttk.LabelFrame(self.modul3, text="Rapor Ayarları", padding=10)
        ayar_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(ayar_frame, text="Okul Adı:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.okul_adi_entry = ttk.Entry(ayar_frame, width=50)
        self.okul_adi_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(ayar_frame, text="Okul Müdürü:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.mudur_adi_entry = ttk.Entry(ayar_frame, width=50)
        self.mudur_adi_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Button(ayar_frame, text="💾 Ayarları Kaydet", command=self.ayarlari_kaydet).grid(row=2, column=1, padx=5, pady=10, sticky="e")

        rapor_frame = ttk.LabelFrame(self.modul3, text="Rapor Oluştur", padding=10)
        rapor_frame.pack(fill="x", padx=5, pady=10)
        
        ttk.Label(rapor_frame, text="Rapor Tarih Aralığı:").grid(row=0, column=0, pady=5)
        self.rapor_bas_tarih = DateEntry(rapor_frame, date_pattern='dd.mm.yyyy')
        self.rapor_bas_tarih.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(rapor_frame, text="-").grid(row=0, column=2)
        self.rapor_bit_tarih = DateEntry(rapor_frame, date_pattern='dd.mm.yyyy')
        self.rapor_bit_tarih.grid(row=0, column=3, padx=5, pady=5)

        # ---------- DÜZELTME 1: 'excel' -> 'xlsx' ----------
        ttk.Button(rapor_frame, text="📄 Excel Raporu Oluştur", command=lambda: self.rapor_olustur('xlsx')).grid(row=1, column=1, pady=10)
        ttk.Button(rapor_frame, text="📕 PDF Raporu Oluştur", command=lambda: self.rapor_olustur('pdf')).grid(row=1, column=3, pady=10, padx=5)

    def ayarlari_kaydet(self):
        okul_adi = self.okul_adi_entry.get().strip()
        mudur_adi = self.mudur_adi_entry.get().strip()
        try:
            self.cursor.execute("INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)", ('okul_adi', okul_adi))
            self.cursor.execute("INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)", ('mudur_adi', mudur_adi))
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Ayarlar kaydedilirken bir hata oluştu: {e}")

    def ayarlari_yukle(self):
        try:
            self.cursor.execute("SELECT deger FROM ayarlar WHERE anahtar='okul_adi'")
            res = self.cursor.fetchone()
            if res: self.okul_adi_entry.insert(0, res[0])

            self.cursor.execute("SELECT deger FROM ayarlar WHERE anahtar='mudur_adi'")
            res = self.cursor.fetchone()
            if res: self.mudur_adi_entry.insert(0, res[0])
        except Exception as e:
            print(f"Ayarlar yüklenemedi: {e}")

    def rapor_olustur(self, format):
        bas_tarih = self.rapor_bas_tarih.get_date()
        bit_tarih = self.rapor_bit_tarih.get_date()
        okul_adi = self.okul_adi_entry.get().strip()
        mudur_adi = self.mudur_adi_entry.get().strip()

        if bas_tarih > bit_tarih:
            messagebox.showerror("Hata", "Başlangıç tarihi bitiş tarihinden sonra olamaz.")
            return

        query = f"""
            SELECT nc.tarih AS 'Tarih',
                   CASE strftime('%w', nc.tarih)
                       WHEN '0' THEN 'Pazar'
                       WHEN '1' THEN 'Pazartesi'
                       WHEN '2' THEN 'Salı'
                       WHEN '3' THEN 'Çarşamba'
                       WHEN '4' THEN 'Perşembe'
                       WHEN '5' THEN 'Cuma'
                       WHEN '6' THEN 'Cumartesi'
                   END AS 'Gün',
                   ny.yer_adi AS 'Nöbet Yeri',
                   p.ad || ' ' || p.soyad AS 'Görevli Personel',
                   p.brans AS 'Branşı'
            FROM nobet_cizelgesi nc
            JOIN personel p ON nc.personel_id = p.id
            JOIN nobet_yerleri ny ON nc.yer_id = ny.id
            WHERE nc.tarih BETWEEN '{bas_tarih.isoformat()}' AND '{bit_tarih.isoformat()}'
            ORDER BY nc.tarih, ny.yer_adi
        """
        try:
            df = pd.read_sql_query(query, self.conn)
            if df.empty:
                messagebox.showinfo("Bilgi", "Seçilen tarih aralığında raporlanacak nöbet bulunamadı.")
                return
        except Exception as e:
            messagebox.showerror("Veritabanı Hatası", f"Rapor verisi alınırken hata: {e}")
            return
            
        df['Tarih'] = pd.to_datetime(df['Tarih']).dt.strftime('%d.%m.%Y')

        dosya_adi = f"nobet_raporu_{bas_tarih.strftime('%Y%m%d')}_{bit_tarih.strftime('%Y%m%d')}"
        save_path = filedialog.asksaveasfilename(
            initialfile=dosya_adi,
            defaultextension=f".{format}",
            filetypes=[(f"{format.upper()} Dosyası", f"*.{format}"), ("Tüm Dosyalar", "*.*")]
        )
        if not save_path:
            return

        try:
            # ---------- DÜZELTME 2: 'excel' -> 'xlsx' ----------
            if format == 'xlsx':
                # 'pd.ExcelWriter' bir context manager (with bloğu) içinde kullanılmalı.
                with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                    
                    header_df = pd.DataFrame({
                        " ": [okul_adi, f"{bas_tarih.strftime('%d.%m.%Y')} - {bit_tarih.strftime('%d.%m.%Y')} Nöbet Çizelgesi", ""]
                    })
                    header_df.to_excel(writer, sheet_name='Nöbet Raporu', index=False, header=False)

                    df.to_excel(writer, sheet_name='Nöbet Raporu', startrow=4, index=False)

                    footer_df = pd.DataFrame({
                        " ": ["", "", f"Rapor Tarihi: {date.today().strftime('%d.%m.%Y')}", mudur_adi, "Okul Müdürü"]
                    })
                    footer_df.to_excel(writer, sheet_name='Nöbet Raporu', startrow=len(df)+6, index=False, header=False)
                    
                    worksheet = writer.sheets['Nöbet Raporu']
                    for i, col in enumerate(df.columns):
                        width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.column_dimensions[chr(65+i)].width = width
                
            elif format == 'pdf':
                self.pdf_raporu_olustur(save_path, df, okul_adi, mudur_adi, bas_tarih, bit_tarih)

            messagebox.showinfo("Başarılı", f"Rapor başarıyla oluşturuldu:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulurken bir hata meydana geldi:\n{e}")

    def pdf_raporu_olustur(self, path, df, okul_adi, mudur_adi, bas_tarih, bit_tarih):
        font_path = self.get_font_path()
        if font_path and os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
            font_name = 'DejaVuSans'
        else:
            print("Uyarı: Font dosyası bulunamadı. Türkçe karakterler düzgün görüntülenmeyebilir.")
            font_name = 'Helvetica'
        
        doc = SimpleDocTemplate(path, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        styles['Title'].fontName = font_name
        styles['Normal'].fontName = font_name
        
        elements.append(Paragraph(okul_adi, styles['Title']))
        elements.append(Paragraph(f"{bas_tarih.strftime('%d.%m.%Y')} - {bit_tarih.strftime('%d.%m.%Y')} NÖBET ÇİZELGESİ", styles['h2']))
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
        
        data = [df.columns.to_list()] + df.values.tolist()
        
        table = Table(data)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0D0E47")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#D4EFF6")),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)
        elements.append(table)
        elements.append(Paragraph("<br/><br/><br/>", styles['Normal']))

        alt_bilgi = f"""
        <br/><br/>
        Rapor Tarihi: {date.today().strftime('%d.%m.%Y')}
        <br/><br/><br/><br/>
        {mudur_adi}
        <br/>
        Okul Müdürü
        """
        p = Paragraph(alt_bilgi, styles['Normal'])
        p.hAlign = 'RIGHT'
        elements.append(p)
        
        doc.build(elements)

    def get_font_path(self):
        system = platform.system()
        if system == "Windows":
            return "C:/Windows/Fonts/Arial.ttf"
        elif system == "Linux":
            common_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf"
            ]
            for path in common_paths:
                if os.path.exists(path):
                    return path
        elif system == "Darwin": # MacOS
             return "/System/Library/Fonts/Supplemental/Arial.ttf"
        return None

if __name__ == "__main__":
    root = tk.Tk()
    app = NobetUygulamasi(root)
    root.mainloop()