# 🏫 Okul Nöbet Yönetim Sistemi

Okul idarecileri için geliştirilmiş, öğretmen nöbet dağıtımını adil ve otomatik bir şekilde gerçekleştiren, raporlama özelliklerine sahip masaüstü uygulamasıdır.

## ✨ Özellikler

* **Personel Yönetimi:** Öğretmen ve idareci ekleme, branş belirleme ve nöbet tutabileceği günleri seçme.
* **Nöbet Yeri Yönetimi:** Okulun farklı alanlarını (Bahçe, Katlar, Yemekhane vb.) dinamik olarak tanımlama.
* **🤖 Otomatik Nöbet Dağıtımı:** * Belirlenen tarih aralığına göre otomatik dağıtım.
    * **Adalet Algoritması:** Personelin geçmiş nöbet sayılarını ve nöbet yerlerini kontrol ederek dengeli dağıtım yapar.
    * Haftalık bazda minimum ve maksimum nöbet kısıtlamalarını gözetir.
* **Manuel Müdahale:** Mevcut nöbetleri silme veya başka bir personele devretme.
* **Gelişmiş Filtreleme:** Tarih, yer ve personel bazlı dinamik arama ve görüntüleme.
* **📄 Raporlama:** * Excel (.xlsx) formatında çıktı alma.
    * PDF formatında, Türkçe karakter destekli ve imzaya hazır çıktı alma.
* **Veritabanı:** SQLite ile yerel veri saklama (kurulum gerektirmez).

## 🚀 Kurulum

1.  Repoyu bilgisayarınıza indirin:
    ```bash
    git clone [https://github.com/kullaniciadi/nobet-sistemi.git](https://github.com/kullaniciadi/nobet-sistemi.git)
    ```
2.  Gerekli kütüphaneleri yükleyin:
    ```bash
    pip install -r requirements.txt
    ```
3.  Uygulamayı başlatın:
    ```bash
    python nbt.py
    ```

## 🛠 Kullanılan Teknolojiler

* **Dil:** Python 3.x
* **Arayüz:** Tkinter (ttk)
* **Veritabanı:** SQLite3
* **Raporlama:** ReportLab (PDF), Pandas & OpenPyxl (Excel)
* **Takvim:** Tkcalendar

## 📸 Ekran Görüntüleri
*(Buraya uygulamanın ekran görüntülerini ekleyebilirsiniz)*
<img width="1920" height="1080" alt="Screenshot_1" src="https://github.com/user-attachments/assets/2ae0a456-6810-44da-8af0-2f61af3b6dda" />
<img width="1920" height="1080" alt="Screenshot_2" src="https://github.com/user-attachments/assets/e8e1274e-1ee8-423b-9fff-b34aeb080653" />
<img width="1920" height="1080" alt="Screenshot_3" src="https://github.com/user-attachments/assets/c386f84a-8071-4b90-b8df-b19bb75a5730" />

---
*Geliştirici: [EMRULLAH ALKAÇ]*
