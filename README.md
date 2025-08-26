Bu proje, bir temel hizmet bulma uygulamasının Backend'ini sağlar.
Kullanıcı kayıt, kimlik doğrulama, oturum yönetimi ve şifre sıfırlama gibi temel işlevleri sunar.


### Kullanılan Teknolojiler

Bu proje aşağıdaki temel teknolojiler ve kütüphaneler kullanılarak geliştirilmiştir:

  * **Backend Framework:** FastAPI
  * **Programlama Dili:** Python
  * **Veritabanı:** PostgreSQL (Üretim Ortamı), SQLite (Geliştirme Ortamı)
  * **ORM (Object-Relational Mapper):** SQLAlchemy
  * **Veri Doğrulama ve Serileştirme:** Pydantic
  * **Şifreleme ve Güvenlik:** Passlib (bcrypt algoritması ile), Cryptography
  * **E-posta Hizmeti:** Postmark
  * **Hosting ve Dağıtım:** Render.com
  * **Veritabanı Sürücüleri:** Psycopg2-binary (PostgreSQL için)
  * **Web Sunucusu:** Uvicorn
  * **Test Çerçevesi:** Pytest, HTTpx (API testleri için)

### Kurulum ve Çalıştırma

Projeyi yerel ortamınızda kurmak ve çalıştırmak için aşağıdaki adımları izleyin:

1.  **Depoyu Klonlayın:**

    ```bash
    git clone https://github.com/sprlptr48/OyunBackend.git
    cd oyunbackend
    ```


2.  **Sanal Ortam Oluşturun ve Aktive Edin:**
    Projeye özel bir sanal ortam oluşturunuz.

    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```

3.  **Bağımlılıkları Yükleyin:**
    `requirements.txt` dosyasında listelenen tüm gerekli kütüphaneleri yükleyin.

    ```bash
    pip install -r requirements.txt
    ```
    Ayrıca konuma bağlı özellikler için `PostGIS`, string aramaları için de
    `pg_trgm` eklentilerini PostgreSQL üzerine yüklemeniz gerekli.
    ```postgresql
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    ```
4.  **Ortam Değişkenlerini Ayarlayın:**
    Proje, hassas bilgileri ve yapılandırma ayarlarını `.env` dosyası aracılığıyla yönetir. Proje kök dizininde `.env` adında bir dosya oluşturun ve aşağıdaki değişkenleri kendi değerlerinizle doldurun:

    ```env
    DB_URL="postgresql://user:password@host:port/database_name" # Üretim için PostgreSQL, geliştirme için SQLite bağlantı dizesi
    SECRET_KEY="sizin_cok_gizli_anahtarınız" # Her zaman benzersiz ve karmaşık bir anahtar kullanın
    MAIL_FROM="gonderen@eposta.com" # Postmark gönderen e-postası
    POSTMARK_API_KEY="sizin_postmark_api_anahtarınız"
    ```

    *Geliştirme ortamında kolaylık sağlaması için `DB_URL`'yi `sqlite:///./sql_app.db` olarak ayarlayabilirsiniz. Üretim ortamında ise bir PostgreSQL veritabanı bağlantı dizesi kullanmalısınız.*

5.  **Uygulamayı Çalıştırın:**
    Uvicorn kullanarak FastAPI uygulamasını başlatın.

    ```bash
    uvicorn main:app --reload
    ```

    Uygulama varsayılan olarak `http://127.0.0.1:8000` adresinde çalışacaktır. API belgelerine, uygulama çalıştıktan sonra `http://127.0.0.1:8000/docs` veya `http://127.00.1:8000/redoc` adreslerinden erişebilirsiniz.

### Testler

Proje, API endpoint'lerinin ve iş mantığının doğru çalıştığından emin olmak için Pytest kullanılarak test edilmiştir.

Testleri çalıştırmak için:

```bash
# Sanal ortamın aktif olduğundan emin olun
pytest
```
