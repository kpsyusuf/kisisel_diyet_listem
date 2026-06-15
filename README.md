# Kişisel Diyet Takip Sistemi

Kullanıcının yaş, kilo, boy, cinsiyet, sağlık durumu (diyabet) ve alerji bilgilerine göre kişiselleştirilmiş günlük kalori ihtiyacını hesaplayan ve buna uygun öğün/besin planlaması yapan Flask tabanlı web uygulaması. Microsoft SQL Server ile ilişkisel veri yönetimi sağlar ve Azure App Service üzerinde yayınlanır.

## Özellikler

- **Kullanıcı yönetimi:** Kayıt ve giriş; parolalar `werkzeug.security` ile hash'lenerek saklanır.
- **Kişiselleştirilmiş kalori hesabı:** Yaş, kilo, boy ve cinsiyete göre BMR tabanlı günlük kalori ihtiyacı; diyabet durumunda otomatik düzeltme.
- **Profil yönetimi:** Kullanıcı bilgilerini ve alerjilerini görüntüleme/güncelleme.
- **Alerji yönetimi:** Kayıt sırasında ve sonrasında alerjik besin ekleme/çıkarma; bu besinler önerilerden hariç tutulur.
- **Besin arama ve seçimi:** Hedef kaloriye göre besin seçimi ve öğün listesi oluşturma.
- **Sağlık kontrolü:** Dağıtım izleme için `/health` endpoint'i.

## Teknolojiler

`Python` · `Flask 3.1` · `pyodbc` · `Microsoft SQL Server` · `Werkzeug` · `HTML/CSS` · `Azure App Service` · `GitHub Actions (CI/CD)`

## Mimari

```
Tarayıcı (HTML/CSS şablonları)
        │
        ▼
   Flask uygulaması (app.py)
   ├── /giris, /kayit            → kimlik doğrulama (hash'li parola)
   ├── /profil, /profil-guncelle → profil + kalori ihtiyacı
   ├── /gida-arama, /besin_sec   → besin arama / seçim
   └── /alerji-sil               → alerji yönetimi
        │
        ▼
   db.py (pyodbc) ──► Microsoft SQL Server (Azure SQL)
```

Dağıtım, `.github/workflows/` altındaki GitHub Actions iş akışı ile Azure App Service'e otomatik yapılır.

## Kurulum

```bash
git clone https://github.com/kpsyusuf/<repo-adi>.git
cd <repo-adi>/kisiseldiyetlistem

pip install -r requirements.txt
```

### Yapılandırma

Proje, veritabanı bilgilerini ortam değişkenlerinden okur. Depoda **gerçek bilgiler bulunmaz**; kök dizinde aşağıdaki gibi bir `.env` dosyası oluşturun (bu dosya `.gitignore` içindedir, repoya gönderilmez):

```env
DB_SERVER=<sunucu-adresiniz>
DB_NAME=<veritabani-adi>
DB_USER=<kullanici>
DB_PASSWORD=<parola>
SQLALCHEMY_DATABASE_URI=<baglanti-dizesi>
SECRET_KEY=<flask-gizli-anahtari>
```

> ⚠️ Veritabanı bilgilerini ve gizli anahtarı asla depoya göndermeyin. Yanlışlıkla gönderdiyseniz parolayı yenileyin.

### Çalıştırma

```bash
flask run
# veya
python app.py
```

Uygulama varsayılan olarak `http://127.0.0.1:5000` adresinde çalışır.

## Proje Yapısı

```
kisiseldiyetlistem/
├── app.py                # Flask uygulaması ve route'lar
├── db.py                 # MS SQL Server bağlantısı (pyodbc)
├── requirements.txt
├── templates/            # giris, kayit, profil, besin_sec, ogun_liste
├── static/images/
└── .github/workflows/    # Azure App Service otomatik dağıtım
```

## Gereksinimler

- Python 3.12
- Microsoft SQL Server (veya Azure SQL) ve uygun ODBC sürücüsü (pyodbc için)

## Yazar

**Yusuf Kasap** — kspyusuf.00@gmail.com · [github.com/kpsyusuf](https://github.com/kpsyusuf)
# kisisel_diyet_listem
