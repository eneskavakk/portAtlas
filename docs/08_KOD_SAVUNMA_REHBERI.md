# PortAtlas — Genel Kod ve Kod Savunması Rehberi

**İncelenen sürüm:** çalışma klasöründeki mevcut kod, 4 Kasım 2026.  
**Amaç:** Bir ekranın kodunu bulmak, butondan veritabanına kadar işlemi takip etmek ve teknik tercihleri kendi cümlelerinle açıklayabilmek.

> Rehber mevcut uygulamayı anlatır. Planlanan özellikler, çalışan özellikmiş gibi sunulmamalıdır. Satır numaraları yeni yorumlar veya geliştirmelerle değişebileceği için dosya adının yanında aranacak fonksiyon ve işlem anahtarları da verilmiştir.

## İçindekiler

1. [Projeyi bir dakikada anlat](#1-projeyi-bir-dakikada-anlat)
2. [Klasör ve dosya haritası](#2-klasör-ve-dosya-haritası)
3. [Bir istek nasıl ilerliyor?](#3-bir-istek-nasıl-ilerliyor)
4. [Hangi ekranın kodu nerede?](#4-hangi-ekranın-kodu-nerede)
5. [Formlar ve butonlar nerede?](#5-formlar-ve-butonlar-nerede)
6. [Frontend kodunu okuma rehberi](#6-frontend-kodunu-okuma-rehberi)
7. [Backend kodunu okuma rehberi](#7-backend-kodunu-okuma-rehberi)
8. [Veritabanı ve ilişkiler](#8-veritabanı-ve-ilişkiler)
9. [Dört önemli uçtan uca senaryo](#9-dört-önemli-uçtan-uca-senaryo)
10. [Güvenlik kontrollerini savunma](#10-güvenlik-kontrollerini-savunma)
11. [OT kavramlarını kodla eşleştirme](#11-ot-kavramlarını-kodla-eşleştirme)
12. [Dil, tasarım, logo ve raporlar](#12-dil-tasarım-logo-ve-raporlar)
13. [Çalıştırma ve testler](#13-çalıştırma-ve-testler)
14. [Hocanın sorabileceği sorular](#14-hocanın-sorabileceği-sorular)
15. [Beş dakikalık kod gösterim sırası](#15-beş-dakikalık-kod-gösterim-sırası)
16. [Hızlı bulma ve hata ayıklama kartı](#16-hızlı-bulma-ve-hata-ayıklama-kartı)
17. [Mevcut sınırlar ve geliştirme alanları](#17-mevcut-sınırlar-ve-geliştirme-alanları)

## 1. Projeyi bir dakikada anlat

Savunmada kullanabileceğin giriş:

> “PortAtlas, endüstriyel cihazların hangi arayüzden, hangi kabloyla, hangi switch portuna bağlı olduğunu kayıt altına alan bir web uygulaması. Bağlantı değişikliklerinin geçmişini, saha doğrulamalarını ve arızaları takip ediyoruz. OT modülünde sistem kapsamı, güvenlik bölgeleri, bu bölgeler arasındaki iletişim, mevcut ve hedef güvenlik değerlendirmeleri ile iyileştirme aksiyonlarını yönetiyoruz. Arayüz vanilla JavaScript, sunucu Python/FastAPI ve veritabanı SQLite. Uygulama kayıt ve iş akışı yönetiyor; canlı ağ taraması yapmıyor.”

| Teknoloji | Projedeki görevi | Kodda nerede? |
| --- | --- | --- |
| HTML | Sayfanın temel kabuğu ve yüklenen dosyalar | `frontend/index.html` |
| CSS | Ekran yerleşimi, renkler, mobil ve baskı görünümü | `frontend/css/` |
| Vanilla JavaScript | Ekran üretme, olaylar, formlar ve API çağrıları | `frontend/js/` |
| Chart.js | Kayıtlı verilerin grafik gösterimi | `frontend/vendor/`, `app.js → chart()` |
| Python / FastAPI | HTTP uçları, oturum, yetki ve işlem kuralları | `backend/` |
| Pydantic | API’ye gelen verinin tür ve alan doğrulaması | `schemas.py`, `ot_schemas.py` |
| Python `sqlite3` | SQL çalıştırma ve transaction yönetimi | `backend/db/database.py` |
| SQLite | Kalıcı ilişkisel veri | `data/portatlas.db` |
| Pytest / Node testleri | İş kuralları, arayüz sözleşmesi ve dil desteği | `tests/` |

**Mimariyi doğru adlandır:** Aynı FastAPI uygulamasının hem statik frontend dosyalarını hem JSON API’yi sunduğu, modüllere ayrılmış tek uygulama. Backend’de API, servis ve veritabanı yardımcıları ayrılmıştır; bazı iş kuralları halen route fonksiyonlarının içindedir.

## 2. Klasör ve dosya haritası

```text
portAtlas/
├── backend/
│   ├── main.py                 Uygulama başlangıcı, hata yönetimi, statik dosyalar
│   ├── security.py             Parola ve oturum belirteci özetleri
│   ├── errors.py               Ortak iş kuralı hatası ve require()
│   ├── schemas.py              Çekirdek API istek modelleri
│   ├── ot_schemas.py           OT istek modelleri ve doğrulayıcılar
│   ├── api/
│   │   ├── routes.py           Oturum, envanter, bağlantı, arıza ve göstergeler
│   │   └── ot_routes.py        SUC, zone/conduit, SL, kontroller ve bulgular
│   ├── services/
│   │   ├── connections.py      Atomik bağlantı değişimi
│   │   ├── queries.py          Birleşik okuma sorguları
│   │   └── ot.py               OT bağlamı, güncellik ve FR farkı
│   └── db/
│       ├── database.py         Bağlantı, göçler ve transaction
│       └── migrations/
│           ├── 001_core.sql    Çekirdek tablolar ve kısıtlar
│           ├── 002_ot_security.sql
│           └── 003_finding_target_links.sql
├── frontend/
│   ├── index.html              Tek HTML giriş dosyası
│   ├── assets/                 Şeffaf logo ve favicon PNG dosyaları
│   ├── css/
│   │   ├── tokens.css          Ortak renk ve font değişkenleri
│   │   ├── app.css             Çekirdek ekranlar ve ortak bileşenler
│   │   └── ot.css              OT ekranlarına özgü stiller
│   ├── js/
│   │   ├── app.js              Ana uygulama, çekirdek ekranlar ve işlemler
│   │   ├── ot.js               OT ekranları ve işlemleri
│   │   ├── ui.js               Ortak form, tablo ve güvenli metin yardımcıları
│   │   ├── api.js              Ortak fetch, oturum ve hata işleme
│   │   ├── i18n.js             Dil seçimi ve çeviri mekanizması
│   │   └── translations.js     Türkçe → İngilizce metin sözlüğü
│   └── vendor/                 Yerel Chart.js dosyası ve lisansı
├── scripts/
│   ├── manage.py               Kurulum, demo, yönetici oluşturma, yedek
│   └── seed_ot.py              İsteğe bağlı temsili OT kapsamları
├── tests/                      Otomatik kontroller
├── data/portatlas.db            Varsayılan veritabanı
├── docs/                       Proje kararları ve bu rehber
├── output/                     Sunum, inceleme çıktıları ve yardımcı üretim dosyaları
├── run.sh                      Yerel çalıştırma komutu
├── requirements*.txt           Python bağımlılık listeleri
├── pyproject.toml              Pytest ayarları
└── README.md                   Kurulum ve kullanım özeti
```

`__init__.py` dosyaları Python paket sınırlarını belirtir. `__pycache__` otomatik oluşan derleme önbelleğidir. `.venv` Python sanal ortamıdır. Bunlar ekran kodunun yazıldığı yerler değildir. Kök klasördeki eski sunum ve tasarım belgeleri de uygulamanın çalışma anında yüklediği frontend dosyaları değildir.

## 3. Bir istek nasıl ilerliyor?

**Örnek:** Kullanıcı “Cihaz ekle” düğmesine basıyor.

```text
app.js: deviceForm()
    ↓ kullanıcı formu doldurur
ui.js: modal() → FormData
    ↓
api.js: api('/devices', {method: 'POST', body})
    ↓ HTTP POST /api/devices
main.py: ortak middleware ve hata yönetimi
    ↓
schemas.py: DeviceInput
routes.py: create_device() + manager() + database()
    ↓
database.py: transaction() → SQLite INSERT
    ↓
JSON yanıt → app.js: toast() ve render()
```

Bu sıralama mantıksal akışı gösterir. Pydantic doğrulaması ve FastAPI bağımlılıkları, uç fonksiyonu çalıştırılmadan önce framework tarafından işlenir.

**Savunma cümlesi:** “Tarayıcı veritabanına doğrudan bağlanmıyor. JSON isteği API’ye gidiyor; tür, yetki ve iş kuralı kontrollerinden sonra SQL çalışıyor.”

## 4. Hangi ekranın kodu nerede?

### 4.1. Çekirdek ekranlar

Aşağıdaki frontend dosyalarının yolu `frontend/js/`, API dosyasının yolu `backend/api/` altındadır. `GET /api/...` veri okumayı belirtir; oluşturma ve güncelleme uçları sonraki bölümdedir.

| Arayüz | Tarayıcı adresi | Frontend’de bul | Backend / okuma ucu | Başlıca veriler |
| --- | --- | --- | --- | --- |
| Giriş | Oturum yokken `/` | `app.js → login()` | `routes.py → login()`, `POST /api/auth/login` | `users`, `sessions`, `login_attempts` |
| Yan menü / üst menü | Bütün oturumlu ekranlar | `app.js → shell()`, `navItems` | `GET /api/auth/me` | Kullanıcı, rol, demo bilgisi |
| Genel bakış | `#dashboard` | `app.js → render()`, `key==='dashboard'` | `routes.py → dashboard()`, `GET /api/dashboard` | Cihaz, bağlantı, arıza sayıları |
| Cihazlar | `#devices` | `render()`, `key==='devices'` | `list_devices()`, `GET /api/devices` | `devices`, `locations` |
| Switch listesi | `#switches` | Cihaz listesiyle ortak `render()` dalı | `GET /api/devices?device_type=switch...` | Switch türündeki cihazlar |
| Cihaz pasaportu | `#device/1` | `render()`, `key.startsWith('device/')` | `passport()`, `GET /api/devices/{id}/passport` | Arayüzler, bağlantılar, geçmiş, arızalar |
| Switch port paneli | `#switch/5` | `render()`, `portDetail()` | `ports()`, `GET /api/switches/{id}/ports` | `switch_ports`, aktif bağlantılar |
| Kablo ve arayüzler | `#inventory` | `render()`, `key==='inventory'` | `GET /api/cables`, `GET /api/interfaces` | `cables`, `network_interfaces` |
| Bağlantılar | `#connections` | `render()`, `connectionRows()` | `connections()`, `GET /api/connections` | Aktif uç eşleşmeleri |
| Değişiklik geçmişi | `#history` | `render()`, geçmiş tablosu | `changes()`, `GET /api/changes` | `connection_changes`, eski/yeni bağlantılar |
| Arıza listesi | `#incidents` | `render()`, `incidentRows()` | `list_incidents()`, `GET /api/incidents` | Arıza ve atama kayıtları |
| Arıza ayrıntısı | `#incident/1` | `render()`, `key.startsWith('incident/')` | `incident_detail()`, `GET /api/incidents/{id}` | Müdahaleler, olaylar, ilgili değişimler |
| Konumlar | `#locations` | `render()`, konum ağacı | `list_locations()`, `GET /api/locations` | `locations`, `path`, `depth` |
| Kullanıcılar | `#users` | `render()`, yönetici kontrolü | `users()`, `GET /api/users` | Parola özeti içermeyen hesap listesi |
| Raporlar | `#reports` | `render()`, `actions.export`, `actions.print` | `GET /api/connections`, `GET /api/incidents` | CSV, grafik ve baskı için kayıtlar |

Adreslerdeki `1` ve `5` yalnızca örnek kimliklerdir; gerçek kaydın kimliği kullanılır.

**Önemli ayrıntı:** Kullanıcı yönetimi menüsü yöneticiye görünür; fakat `GET /api/users` oturumlu kullanıcılara açıktır çünkü OT atama formları da aktif kullanıcı listesini kullanır. **Hesap oluşturma** işlemi `POST /api/users` ile yöneticiye sınırlandırılmıştır.

### 4.2. OT ekranları

Bütün bu ekranların ana frontend dosyası **`frontend/js/ot.js`**, ana API dosyası **`backend/api/ot_routes.py`** dosyasıdır. `app.js → render()` OT adresini fark ettiğinde işi `renderOt(key)` fonksiyonuna devreder. `renderOt()` her yüklemede önce `GET /api/ot/overview` üzerinden ortak veriyi alır.

| Arayüz | Adres | Frontend’de bul | Ek backend işlevi / veri | Başlıca tablolar |
| --- | --- | --- | --- | --- |
| OT genel görünüm | `#ot` | `renderOt()`, `key==='ot'` | `overview()` | OT tablolarının birleşik özeti |
| Sistem ve zone listesi | `#ot/zones` | `key==='ot/zones'`, `zonesTable()` | Genel görünüm verisi | `security_systems`, `security_zones` |
| Zone ayrıntısı | `#ot/zone/1` | `path[1]==='zone'`, `levelPanel()` | `services/ot.py → profiles()` | Üyeler, profiller, bulgular |
| Conduit listesi | `#ot/conduits` | `conduitTable()` | Genel görünüm verisi | `security_conduits` |
| Conduit ayrıntısı | `#ot/conduit/1` | `path[1]==='conduit'`, `levelPanel()` | `profiles(..., conduit_id=...)` | İletişim ve profil kayıtları |
| Cihaz güvenlik listesi | `#ot/devices` | `deviceTable()` | Genel görünüm verisi | `device_security`, üyelikler |
| Cihaz güvenlik ayrıntısı | `#ot/device/1` | `path[1]==='device'` | `device_security()`, `GET /api/ot/devices/{id}` | Kontroller ve bulgular |
| Kontrol listesi | `#ot/assessments` | `assessmentTable()` | Genel görünüm verisi | `ot_assessments` |
| Kontrol ayrıntısı | `#ot/assessment/1` | `path[1]==='assessment'` | `get_assessment()`, `GET /api/ot/assessments/{id}` | Şablon ve sonuç kopyası |
| Bulgu listesi | `#ot/findings` | `findingsTable()` | Genel görünüm verisi | `security_findings` |
| Bulgu ayrıntısı | `#ot/finding/1` | `path[1]==='finding'` | `finding_detail()`, `GET /api/ot/findings/{id}` | Bulgu, aksiyonlar, denetim |
| OT geçmişi | `#ot/history` | `key==='ot/history'` | `ot_history()`, `GET /api/ot/history` | `audit_events` |

**SL-A/SL-T formu ayrı bir sayfa değildir.** Zone veya conduit ayrıntısında açılan ortak modal formdur; kodu `otActions['ot-level']` içindedir.

## 5. Formlar ve butonlar nerede?

### 5.1. Çekirdek işlemler

| İşlem | Frontend’de aranacak ad | HTTP isteği | Backend’de karşılığı |
| --- | --- | --- | --- |
| Cihaz ekle/düzenle | `deviceForm()` | `POST /api/devices`, `PATCH /api/devices/{id}` | `create_device()`, `update_device()` |
| Bağlantı kur/taşı/değiştir/sonlandır | `connectionForm()` | `POST /api/connection-changes` | `change()` → `change_connection()` |
| Port uygunluğunu değiştir | `actions['port-status']` | `PATCH /api/ports/{id}` | `update_port()` |
| Sahada doğrula | `actions.verify` | `POST /api/connections/{id}/verifications` | `verify()` |
| Arıza aç | `incidentForm()` | `POST /api/incidents` | `create_incident()` |
| Sorumlu ata | `actions.assign` | `POST /api/incidents/{id}/assign` | `assign()` |
| Müdahale ekle | `actions.intervene` | `POST /api/incidents/{id}/interventions` | `intervention()` |
| Arıza durumu değiştir | `actions.transition` | `POST /api/incidents/{id}/transitions` | `transition()` |
| Kablo ekle | `actions['new-cable']` | `POST /api/cables` | `create_cable()` |
| Arayüz ekle | `actions['new-interface']` | `POST /api/interfaces` | `create_interface()` |
| Konum ekle | `actions['new-location']` | `POST /api/locations` | `create_location()` |
| Kullanıcı ekle | `actions['new-user']` | `POST /api/users` | `create_user()` |
| CSV indir / yazdır | `actions.export`, `actions.print` | Yeni bir yazma API’si çağırmaz | Mevcut yanıt tarayıcıda işlenir |

### 5.2. OT işlemleri

| İşlem | `ot.js` içinde aranacak ad | HTTP isteği | Backend’de karşılığı |
| --- | --- | --- | --- |
| SUC oluştur | `otActions['ot-system']` | `POST /api/ot/systems` | `create_system()` |
| Zone oluştur/düzenle | `zoneForm()` | `POST /api/ot/zones`, `PATCH /api/ot/zones/{id}` | `create_zone()`, `update_zone()` |
| Üyeleri düzenle | `otActions['ot-members']` | `PUT /api/ot/zones/{id}/members` | `set_members()` |
| Conduit oluştur/düzenle | `conduitForm()` | `POST /api/ot/conduits`, `PATCH /api/ot/conduits/{id}` | `create_conduit()`, `update_conduit()` |
| SL-A / SL-T kaydet | `otActions['ot-level']` | `POST /api/ot/levels` | `create_level()` |
| Kritiklik belirle | `otActions['ot-criticality']` | `PUT /api/ot/devices/{id}/criticality` | `set_criticality()` |
| Kontrol başlat / taslak düzenle | `assessmentForm()` | `POST /api/ot/assessments`, `PUT /api/ot/assessments/{id}` | `create_assessment()`, `update_assessment()` → `save_assessment()` |
| Uygulanamaz cevaplarını onayla | `otActions['ot-approve-applicability']` | `POST /api/ot/assessments/{id}/approve-applicability` | `approve_applicability()` |
| Bulgu aç | `otActions['ot-finding']` | `POST /api/ot/findings` | `create_finding()` |
| Aksiyon planla | `otActions['ot-plan']` | `PATCH /api/ot/findings/{id}/plan` | `plan_finding()` |
| Uygula / gönder / doğrula / geri döndür | `otActions['ot-finding-action']` | `POST /api/ot/findings/{id}/actions` | `action_finding()` |

## 6. Frontend kodunu okuma rehberi

### `index.html`: Neden bütün ekranlar burada görünmüyor?

Bu dosya yalnızca başlangıç kabuğudur. `#app` boş alanına JavaScript ekranları yerleştirir. Chart.js klasik script olarak, uygulama `type="module"` ile yüklenir. `.js?v=i18n-1` gibi sürüm ekleri tarayıcıda eski dosyanın kullanılmasını azaltmak içindir.

**Cevap:** “Her ekran için ayrı HTML dosyası yok. Tek sayfa kabuğunda hash tabanlı yönlendirme kullanıyoruz.”

### `app.js`: Ana uygulama

| Parça | Görevi |
| --- | --- |
| `navItems` | Menü adresi, çevirili ad ve sıra numarası |
| `shell()` | Yan menü, üst menü, arama ve kullanıcı alanı |
| `login()` | Giriş formu ve başarılı giriş sonrası başlangıç |
| `route()` / `params()` / `go()` | Hash adresi, URL filtreleri ve yönlendirme |
| `render()` | Ekran seçimi, API okumaları ve HTML’nin yerleştirilmesi |
| `charts` | Ekran değişiminde kapatılacak Chart.js örnekleri |
| `renderId` | Eski isteğin yanıtının yeni ekranı ezmesini engelleyen sayaç |
| `currentData` | Ekranın form işlemlerinde ihtiyaç duyduğu son veriler |
| `selectedPort` | Görsel port panelindeki seçim |
| `actions` | Düğme işlem anahtarlarıyla işlevleri eşleştiren nesne |

`renderId` isteği ağda iptal etmez; yanıt geldiğinde hâlâ aynı ekranın yüklemesi mi diye kontrol eder.

Düğmelerin çoğu şu modelle çalışır:

```text
<button data-action="new-device"> ... </button>
    ↓
document.addEventListener('click', ...)
    ↓
actions['new-device']
    ↓
deviceForm()
```

Buna **olay delegasyonu** denir. HTML yeniden oluşturulsa da belge üzerindeki ortak dinleyici işlem anahtarını okuyabilir. Form içindeki `change` ve `submit` olaylarının bazıları ise form açıldığında doğrudan bağlanır.

### `ui.js`: Tekrarlanan arayüz kodu

- `e(value)`: `<`, `>`, `&`, tırnak gibi karakterleri HTML’den kaçırır. Kullanıcı girdisini `innerHTML` şablonuna güvenli metin olarak yerleştirmek için önemlidir.
- `date(value)`: Tarihi seçili dilde ve İstanbul saat diliminde gösterir.
- `labels`: `open`, `manager`, `verified` gibi kodları görünen adlara çevirir.
- `heading()`, `button()`, `table()`, `badge()`: Ortak görünüm üretir.
- `input()`, `select()`, `textarea()`: Form alanlarını üretir. Seçenek değeri ile görünen etiketi ayırır.
- `modal()`: Ortak pencereyi açar, FormData okur, gönderimde düğmeyi kilitler, alan hatalarını gösterir ve kaydedilmemiş değişiklikleri izler.
- `toast()`: Kısa işlem bildirimini gösterir.

**Kaçırma örneği:** Kullanıcı cihaz adı olarak `<script>...</script>` girerse bu değerin HTML olarak çalıştırılmaması gerekir. `e()` bu yerleştirme noktasında metni kaçırır; veritabanını “temizleyen” bir fonksiyon değildir.

### `api.js`: Ağ katmanı

`api('/devices')`, `fetch('/api/devices')` çağrısına dönüşür. Yardımcı fonksiyon:

1. Gövdeyi JSON’a çevirir.
2. Aynı kaynak oturum çerezini gönderir.
3. Oturum varsa `X-CSRF-Token` başlığını ekler.
4. HTTP başarısızsa hata mesajı, alan hataları ve durumu bir hata nesnesine aktarır.
5. Oturumlu istekte `401` gelirse `session-expired` olayı yayınlar.

`session` değişkeni görünen kullanıcı ve CSRF bilgisini tutar. **HttpOnly oturum çerezi** JavaScript tarafından okunmaz. Dil tercihi `localStorage` içindedir; oturum belirteci burada saklanmaz.

### `ot.js`: OT’nin ayrı modülü

- `configureOt()`: Ana uygulamanın yönlendirme ve yenileme fonksiyonlarını alır.
- `renderOt()`: OT ekranını `{html, after}` sözleşmesiyle ana uygulamaya döndürür.
- `levelPanel()`: Mevcut/hedef profilleri, FR farklarını ve revizyonları gösterir.
- `zoneForm()`, `conduitForm()`, `assessmentForm()`: Büyük OT formları.
- `otActions`: Ana uygulama düğmeleriyle karışmaması için `ot-` önekli işlemler.

## 7. Backend kodunu okuma rehberi

### `main.py`: Sunucu nereden başlıyor?

Uvicorn, `backend.main:app` ifadesiyle `main.py` içindeki `app` nesnesini yükler. Bu nesne `create_app()` ile oluşturulur.

| Parça | Ne yapar? |
| --- | --- |
| `create_app(db_path=None)` | Uygulamayı ve veritabanı yolunu kurar; testler farklı DB verebilir |
| `lifespan()` | Açılışta `initialize()` çalıştırır |
| `headers()` | İstek kimliği ve güvenlik başlıkları ekler; API önbelleğini kapatır |
| `error()` | Ortak JSON hata biçimini üretir |
| İstisna işleyicileri | İş kuralı, alan doğrulama ve SQLite hatalarını HTTP yanıtına dönüştürür |
| `include_router(...)` | Çekirdek ve OT uçlarını ekler |
| `mount('/static', ...)` | `frontend/` klasörünü statik olarak sunar |
| `index()` | `/` adresinden `index.html` döndürür |
| `health()` | Sunucunun yanıt verdiğini gösterir; tam sistem sağlık testi değildir |

FastAPI’nin `/docs` sayfası API sözleşmesini gösterir. Savunmada yöntem, alan ve yanıt yapısını buradan inceleyebilirsin; değişiklik yapan denemeleri gerçek kayıtlar yerine test verisiyle yap.

### `routes.py`: İstek giriş noktaları

`@router.post('/devices')` gibi dekoratör, HTTP adresini altındaki fonksiyona bağlar. Çekirdek router’ın `/api`, OT router’ın `/api/ot` öneki vardır.

- `Depends(database)`: İstek için bağlantı sağlar ve sonunda kapatır.
- `Depends(authenticated)`: Oturumu kontrol eder; yazma isteğinde CSRF de denetlenir.
- `Depends(manager)`: Oturum kontrolüne ek yönetici rolü ister.
- `get_record()`: Bulunmayan kayda ortak 404 üretir.
- `audit()`: Önce/sonra değerleri ve yapan kişiyi kaydeder.

**Savunma cümlesi:** “Frontend’de düğmeyi gizlemek kullanım kolaylığı sağlıyor. Yetkisiz kullanıcı isteği elle gönderse de backend bağımlılığı işlemi reddediyor.”

### `schemas.py` ve `ot_schemas.py`: Doğrulama nerede?

Bunlar veritabanı tablolarının ORM modelleri değildir; **API istek modelleridir**.

- `Input`: Metin kenar boşluklarını temizler, beklenmeyen alanları `extra='forbid'` ile reddeder.
- `DeviceInput`, `ConnectionInput`, `IncidentInput`: Temel alan türleri ve sınırlar.
- `ScopeInput.exactly_one()`: Bir bulgu için cihaz/zone/conduit kapsamlarından tam biri seçilir.
- `LevelInput`: Yedi FR değeri; her belirlenmiş değer 0–4 arasında katı tamsayıdır. `True` seviye 1 kabul edilmez.
- `LevelInput.valid_profile()`: Onaylı kayıtta eksik seviye veya yetersiz uzunlukta referans olamaz.
- `FindingAction`: İzin verilen aksiyon adlarını sınırlar.

**Ayrım:** “Alan 0–4 mü?” model doğrulamasıdır. “Bu zone var mı, aynı sisteme mi ait?” veritabanı bilgisi gerektiren iş kuralıdır ve API/serviste kontrol edilir.

### `services/`: Tekrarlanan veya kritik iş mantığı

| Dosya | En önemli fonksiyon | Savunmada vurgula |
| --- | --- | --- |
| `connections.py` | `change_connection()` | Bağlantı değişimi tek transaction; geçmiş korunur; tekrar istek çift değişiklik üretmez |
| `queries.py` | `connections()`, `locations()`, `history()`, `incidents()` | Birleşik okuma sorguları; konum ağacı için recursive CTE |
| `ot.py` | `scope_context()`, `profiles()`, `assessment()` | Değerlendirmenin dayandığı bağlamı ve sonradan değişip değişmediğini izleme |

### `errors.py`: Neden `require()` kullanılıyor?

`require(koşul, mesaj, durum)` koşul sağlanmadığında `DomainError` fırlatır. `main.py` bunu tutarlı HTTP/JSON yanıtına çevirir. Böylece her uç fonksiyonu ayrı hata yanıtı üretmek zorunda kalmaz.

## 8. Veritabanı ve ilişkiler

### Çekirdek ilişkiyi ezberle

```text
Konum → Cihaz → Ağ arayüzü
                    ↓
                 Bağlantı → Kablo
                    ↓
               Switch portu → Switch cihazı
```

`connections` satırı, arayüz/port/kablo kimliklerini bir arada tutar. Switch de `devices` tablosunda bir cihazdır; türü `switch` olur. Makinenin birden fazla arayüzü, switch’in farklı sayıda portu olabilir.

### Tablo grupları

| Alan | Tablolar | Neden var? |
| --- | --- | --- |
| Oturum ve hesap | `users`, `sessions`, `login_attempts`, `settings` | Kimlik, yetki, süreli oturum ve demo ayarı |
| Fiziksel envanter | `locations`, `devices`, `network_interfaces`, `cables`, `switch_ports` | Cihaz ve bağlantı uçlarını tanımlamak |
| Fiziksel değişim | `connections`, `connection_changes`, `device_location_events` | Güncel durumu ve geçmiş uç/konum değişimlerini korumak |
| Saha kontrolü | `field_verifications` | Kayıt ile sahadaki bağlantının tutarlılığını ayrı değerlendirmek |
| Arıza | `incidents`, `interventions` | İşin yaşam döngüsünü ve saha notlarını izlemek |
| İzlenebilirlik | `audit_events`, `request_keys` | Değişiklik gerekçesi ve tekrar istek koruması |
| OT kapsamı | `security_systems`, `security_zones`, `zone_members`, `security_conduits` | SUC, güvenlik grupları ve iletişim kapsamı |
| OT değerlendirme | `security_level_profiles`, `device_security`, `ot_assessments` | Seviye revizyonları, kritiklik ve kontrol kanıtları |
| İyileştirme | `security_findings`, `security_finding_actions` | Plan, uygulama ve doğrulama |

`schema_migrations` tablosu SQL dosyası içinde değil, `database.py → initialize()` içinde hazırlanır. Uygulanan göçlerin adını ve zamanını tutar.

### `database.py`: Üç kritik kavram

**Yabancı anahtar:** `PRAGMA foreign_keys=ON` ilişkili kaydın varlığını veritabanı düzeyinde denetler.

**WAL:** Okuyucu ve yazıcının birlikte çalışmasını kolaylaştırır. SQLite’ın tek yazıcı sınırını kaldırmaz.

**Transaction:** `BEGIN IMMEDIATE` ile yazma işlemi başlatılır; başarılıysa commit, hatada rollback yapılır. Koddan gerçek örnek:

```python
@contextmanager
def transaction(db):
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
```

Bir bağlantının kapatılıp yenisinin açılamaması gibi yarım işlemler bu sınır içinde geri alınır.

### Aynı portun iki kez kullanılmasını ne engelliyor?

`001_core.sql` içindeki gerçek indeksler:

```sql
CREATE UNIQUE INDEX uq_active_interface ON connections(interface_id) WHERE ended_at IS NULL;
CREATE UNIQUE INDEX uq_active_port ON connections(port_id) WHERE ended_at IS NULL;
CREATE UNIQUE INDEX uq_active_cable ON connections(cable_id) WHERE ended_at IS NULL;
```

`WHERE ended_at IS NULL` yalnızca aktif kayıtları kapsar. Aynı arayüzün geçmişte birden fazla bağlantısı bulunabilir; aynı anda iki aktif bağlantısı olamaz. Bu kural yalnızca frontend seçeneğini gizlemeye bırakılmamıştır.

### Göçler neden ayrı dosyalarda?

- `001_core.sql`: Temel envanter, oturum ve arıza şeması.
- `002_ot_security.sql`: OT tabloları ve ilişkileri.
- `003_finding_target_links.sql`: Bulguyu FR ve hedef profil revizyonuna bağlayan alanlar.

Mevcut kayıtları silip DB’yi yeniden kurmak yerine uygulanmamış dosyalar sırayla çalışır. `version` sütunları kayıt düzenleme sürümüdür; `schema_migrations` ise veritabanı şema sürüm geçmişidir. İkisi farklı amaç taşır.

## 9. Dört önemli uçtan uca senaryo

### A. Oturum açma

1. `app.js → login()` kullanıcı adı ve parolayı formdan alır.
2. `api.js` `POST /api/auth/login` isteği gönderir.
3. Backend, istemci adresine göre son beş dakikadaki deneme sayısını kontrol eder.
4. `security.py → verify_password()` kayıtlı scrypt özetiyle karşılaştırır. Olmayan hesapta da benzer parola doğrulama işi yapılır.
5. Rastgele oturum ve CSRF belirteçleri üretilir. Oturumun özeti `sessions` tablosuna yazılır.
6. Tarayıcıya sekiz saatlik HttpOnly oturum çerezi gönderilir.
7. Frontend kullanıcı durumunu kurar; `shell()` ve `render()` ile çalışma alanını açar.

**Gösterilecek kod:** `routes.py → login()` ve `security.py → verify_password()`.

### B. CNC bağlantısını Port 05’ten Port 08’e taşıma

Bu örnekte kimlikler gerçek DB’den seçilir; port numarasıyla portun veritabanı kimliği aynı şey değildir.

1. Cihaz pasaportunda “Bağlantıyı değiştir” seçilir.
2. `connectionForm()` arayüz, kablo, cihaz, bağlantı ve arıza listelerini alır.
3. “Port taşıma” seçilince kablo sabit kalır; uygun hedef port seçilir.
4. İstek `kind='move'`, `expected_connection_id`, hedef `port_id`, aynı `cable_id`, gerekçe ve `request_key` taşır.
5. `routes.py → change()` isteği `services/connections.py → change_connection()` fonksiyonuna aktarır.
6. Servis tekrar istek kaydını, bağlantı güncelliğini, uçları ve işlem türünün kurallarını denetler.
7. Eski bağlantıya `ended_at` yazılır. Yeni bağlantı ayrı satır olarak oluşturulur.
8. `connection_changes` eski/yeni ilişkiyi tutar; sonuç `request_keys` içine yazılır.
9. Her şey aynı transaction içinde tamamlanır.
10. Yeni bağlantının kendi saha doğrulaması henüz yoktur; doğrulama **bekliyor** görünür.

**Üç korumayı ayır:**

| Koruma | Önlediği durum |
| --- | --- |
| `expected_connection_id` | Kullanıcının eski bağlantı üzerinden işlem yapması |
| `request_key` + içerik özeti | Ağ kesintisi sonrası aynı isteğin ikinci kez uygulanması |
| Aktif tekillik indeksleri | İki isteğin aynı aktif portu/kabloyu/arayüzü paylaşması |

### C. Zone için SL-A / SL-T kaydetme

1. `#ot/zone/{id}` içinde `levelPanel()` mevcut profilleri gösterir.
2. SL-A/SL-T düğmesi `otActions['ot-level']` formunu açar.
3. Yedi FR değeri, gerekçe, referans, durum ve formun bildiği kapsam/profil sürümü gönderilir.
4. `LevelInput` türleri ve onay için gerekli alanları kontrol eder.
5. `create_level()` yönetici yetkisini, kapsam sürümünü ve son profil kimliğini denetler.
6. Önceki kaydın üstüne yazmak yerine yeni revizyon eklenir; kayıt anındaki `scope_context()` saklanır.
7. Sonraki okumada `profiles()` bugünkü kapsamla saklanmış görüntüyü karşılaştırır.
8. Her iki profil onaylı ve güncelse FR bazında fark hesaplanır; arayüz bu farkı gösterir.

**Örnek:** FR5 mevcut 1, hedef 3 ise uygulama farkı 2 gösterir. Bu bir uyumluluk yüzdesi değildir. Seviye değerleri kontrol adedinden otomatik türetilmez.

### D. Güvenlik bulgusunu kapatma

```text
Açık → İşlemde → Doğrulama bekliyor → Kapalı
```

1. Kontrol sonucu veya hedef farkından bulgu açılır.
2. Yönetici `plan_finding()` üzerinden öncelik, sorumlu ve tarih belirler.
3. Yetkili kişi `work` aksiyonu ile uygulama kaydı ekler.
4. `submit` aksiyonu kanıt referansıyla doğrulamaya gönderir.
5. Yönetici `verify` ile doğrular ve kapatır; uygun bulmazsa `return` ile işleme döndürür.
6. Yüksek öncelikte uygulayan veya gönderimi yapan kişi doğrulayıcı olamaz.
7. Durum, aksiyon ve denetim kaydı aynı transaction içinde yazılır.

**Önemli:** Bulgunun kapanması SL-A’yı otomatik yükseltmez. Yeni kanıtla ayrıca değerlendirme ve gerekiyorsa profil revizyonu gerekir. Arızanın çözülmesi de güvenlik bulgusunu otomatik kapatmaz.

## 10. Güvenlik kontrollerini savunma

| Konu | Kodda nerede? | Doğru anlatım |
| --- | --- | --- |
| Parola saklama | `security.py → hash_password()` | Rastgele tuz + scrypt; düz parola saklanmaz |
| Parola karşılaştırma | `verify_password()` | `hmac.compare_digest` kullanılır |
| Oturum | `routes.py → authenticated()` | Süre, oturum özeti ve aktif kullanıcı birlikte kontrol edilir |
| CSRF | `api.js`, `authenticated()` | Yazma isteğinde oturum çerezine ek başlık doğrulaması |
| Rol yetkisi | `manager()`, `may_work()`, OT işlem kontrolleri | Backend karar verir; düğme görünürlüğü tek güvenlik katmanı değildir |
| SQL değerleri | `db.execute(sql, args)` | Kullanıcı değerleri parametre bağlanır; dinamik tablo adları sunucunun sabit seçimlerinden gelir |
| HTML yerleştirme | `ui.js → e()` | Dinamik kayıt değerleri HTML’den kaçırılır |
| Tarayıcı başlıkları | `main.py → headers()` | CSP, nosniff ve diğer ortak başlıklar |
| İzlenebilirlik | `audit()`, `connection_changes` | Kimin, neyi, ne zaman ve hangi gerekçeyle değiştirdiği |
| Hata yönetimi | `errors.py`, `main.py` | İş kuralı ve doğrulama hataları ortak JSON biçiminde |

Sadece bu kontrollerin bulunması “bütün güvenlik riskleri çözülmüş” demek değildir. HTTPS, işletim politikası ve pilot kabulü ayrıca gerekir.

## 11. OT kavramlarını kodla eşleştirme

| Kavram | Basit açıklama | Kod / veri |
| --- | --- | --- |
| SUC — System Under Consideration | Değerlendirilen sistem ve sınırı | `SystemInput`, `security_systems` |
| Zone | Ortak güvenlik ihtiyacıyla gruplanan varlıklar | `ZoneInput`, `security_zones`, `zone_members` |
| Conduit | Zone’lar arasındaki iletişim kapsamı | `ConduitInput`, `security_conduits` |
| FR — Foundational Requirement | Güvenliğin yedi temel gereksinim alanı | `services/ot.py → FRS` |
| SL-A — Achieved | Kayıtlı mevcut değerlendirme | `sl_type='achieved'` |
| SL-T — Target | Risk değerlendirmesine dayanan hedef | `sl_type='target'` |
| Kritiklik | Cihazın üretim/operasyon üzerindeki etkisi | `device_security` |
| Kanıt / referans | Değerlendirme dayanağına ilişkin kayıt | `reference`, `evidence`, `rationale` |
| Güncellik | Değerlendirme yapılan kapsamla bugünkü kapsamın ilişkisi | `scope_context()`, `stale`, `stale_items` |

`None` bilinmeyen değerdir; **0 ile aynı değildir**. FR1–FR7 sırası `FRS` listesinde ve vektörde korunur. Zone, fiziksel “konum” ile aynı kavram değildir. Mevcut sürümde cihazın tek bir birincil zone üyeliği vardır; bu proje modelidir.

**Standart hakkında doğru ifade:** “PortAtlas, IEC 62443’teki zone/conduit ve mevcut/hedef değerlendirme kavramlarını kayıt modelinde kullanıyor. Otomatik sertifikasyon veya tam standart uygunluk sonucu üretmiyor. Sekiz başlangıç sorusu PortAtlas’ın kendi kontrol listesidir.”

## 12. Dil, tasarım, logo ve raporlar

### Türkçe / İngilizce

- `translations.js`: Arayüze ait sabit Türkçe metinlerin İngilizce karşılıkları.
- `i18n.js → t()` / içe aktarılan adıyla `tr()`: Sabit metin çevirisi.
- `msg`: Şablonun sabit parçalarını çevirir; `${...}` ile eklenen kayıt değerlerini değiştirmez.
- `languageToggle()`: Giriş ve üst menüdeki TR/EN düğmesi.
- `initializeLanguage()`: Belge dili, başlık ve metaveriyi ayarlar; tercihi `portatlas.language` anahtarında saklar.

Dil değişiminde sayfa yeniden yüklenir; hash adresi ve sunucudaki oturum korunur. Kullanıcının girdiği cihaz adı, saha notu veya kanıt metni otomatik çevrilmez. Tarih biçimi TR/EN’e göre, saat dilimi İstanbul olacak şekilde gösterilir.

### Tasarım ve logo

| Değiştirmek istediğin şey | Açılacak yer |
| --- | --- |
| Renk, yazı tipi, kenarlık değişkeni | `frontend/css/tokens.css` |
| Yan menü, giriş, tablo, modal, üst çubuk | `frontend/css/app.css` |
| Zone, conduit, seviye ve OT kontrol paneli | `frontend/css/ot.css` |
| Mobil görünüm | Aynı CSS dosyalarındaki `@media` blokları |
| Yazdırma / PDF görünümü | `app.css → @media print` |
| Giriş ve menüdeki logo | `frontend/assets/portatlas-logo.png`, `app.js → login()/shell()` |
| Logo boyutu / koyu zeminde beyaz görünümü | `app.css → .brand-logo` |
| Tarayıcı sekmesi simgesi | `frontend/assets/portatlas-icon.png`, `index.html` |

PNG’nin arka planı şeffaftır. Koyu zemindeki beyaz görünüm CSS filtresinden gelir; kökteki özgün `logo.png` çalışma anında doğrudan çağrılan dosya değildir.

### Grafik ve raporlar

`chart()` yerel Chart.js dosyasını kullanır. Veri API’den gelir; grafik veriyi toplayan bir ağ izleyicisi değildir.

CSV, `app.js → actions.export` içinde tarayıcıda üretilir. Başlıklar seçili dile göre hazırlanır, kullanıcı kayıtları aynen kalır. Formül gibi yorumlanabilecek başlangıç karakterlerine karşı kaçış ve UTF-8 BOM kullanılır. PDF düğmesi özel bir sunucu PDF motoru çalıştırmaz; tarayıcının `window.print()` akışını açar.

## 13. Çalıştırma ve testler

Proje kökünde, mevcut kurulu ortamla:

```bash
./run.sh
```

Alternatif:

```bash
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

- Arayüz: `http://127.0.0.1:8000`
- API belgesi: `http://127.0.0.1:8000/docs`
- Basit sunucu kontrolü: `http://127.0.0.1:8000/health`
- Varsayılan DB: `data/portatlas.db`
- Farklı DB: başlangıçta `PORTATLAS_DB` değişkeni.
- `run.sh` için farklı port: `PORTATLAS_PORT` değişkeni.

Yeni kurulumda sanal ortam ve bağımlılık adımları için [README](../README.md) kullanılmalıdır. Frontend derleme adımı yoktur; Node normal çalıştırma için gerekli değildir, JavaScript testlerinde kullanılır.

### Testlerin yeri

| Dosya | Kontrol ettiği alan |
| --- | --- |
| `tests/test_core.py` | Oturum, CSRF, yetki, bağlantı işlemleri, rollback, eşzamanlı port kullanımı, arıza, yedek |
| `tests/test_ot.py` | Kapsam, üyelik, SL ayrımı, güncellik, kontroller, mükerrer bulgu, ayrı doğrulayıcı |
| `tests/ot_render.mjs` | Gerçek API fixture verisiyle Türkçe/İngilizce OT ekran sözleşmesi ve rol görünürlüğü |
| `tests/frontend_i18n.test.mjs` | Dil tercihi, çeviri, kullanıcı değerlerinin korunması ve depolama hatası varsayılanı |

```bash
.venv/bin/python -m pytest -q
node --test tests/frontend_i18n.test.mjs
```

Önceki doğrulama sonucunda **45 Pytest + 5 Node testi** geçmiştir. Rehber hazırlanırken uygulama davranışı değiştirilmemiştir; güncel sonucu savunma öncesi bu komutlarla yeniden alabilirsin. Testler geçici DB kullanır. `ot_render.mjs`, fixture dosyasını Python testinden alır; tek başına rastgele çalıştırmak yerine Pytest akışıyla kullanılır.

### Kurulum ve yedek komutları

- `python -m scripts.manage init`: Şemayı hazırlar.
- `python -m scripts.manage create-admin`: Yönetici hesabı oluşturur.
- `python -m scripts.manage demo`: Yalnızca boş DB’ye temsili çekirdek kayıtları ekler.
- `python -m scripts.manage ot-demo`: Demo DB’ye isteğe bağlı temsili OT kapsamları ekler; SL değerlendirmesi uydurmaz.
- `python -m scripts.manage backup --output output/yeni-yedek.db`: Yeni hedef dosyaya SQLite backup API ile tutarlı yedek alır.

## 14. Hocanın sorabileceği sorular

**Neden Python/FastAPI?**  
“Python proje tercihi. FastAPI ile HTTP uçlarını, tür doğrulamasını, bağımlılıklarla oturum/yetki kontrolünü ve otomatik API belgesini birlikte kurduk.”

**Neden vanilla JavaScript?**  
“Frontend framework kullanmadan ES modülleri, hash yönlendirme ve ortak yardımcılarla çalışıyoruz. Küçük ders demosunda derleme gereksinimini azaltıyor. Kod büyüdükçe ekranların daha küçük modüllere ayrılması gerekecek.”

**Neden SQLite?**  
“Yerel demo için tek dosyalı kurulum ve ilişkisel bütünlük avantajı var. Yabancı anahtar, indeks ve transaction kullanıyoruz. Büyük ölçek veya yoğun eşzamanlı yazma için ayrıca kapasite değerlendirmesi gerekir.”

**ORM var mı?**  
“Hayır. Python sqlite3 ile SQL sorguları çalıştırıyoruz. Pydantic sınıfları ORM tablosu değil, API istek modelleri.”

**Aynı portu iki kişi seçerse?**  
“Arayüz filtrelerine ek olarak aktif port tekilliği veritabanında zorunlu. Transaction ve benzersiz indeks nedeniyle iki işlem de aynı portta aktif kalamaz.”

**İşlemin yarısında hata olursa?**  
“Transaction rollback yapar. Örneğin eski bağlantının kapanması ve yeni bağlantının açılması birlikte tamamlanır; biri başarısızsa önceki durum korunur.”

**Sayfa beklerken bağlantıyı başka biri değiştirirse?**  
“Bağlantı isteği gördüğü expected_connection_id değerini gönderir. Sunucu güncel aktif kimlikle eşleşmiyorsa işlemi reddeder. Düzenleme kayıtlarında version kontrolleri de var.”

**İnternet kesildiğinde tekrar Kaydet’e basılırsa?**  
“Aynı içerik için request_key korunur. Sunucu anahtar ve içerik özetini görürse önceki sonucu döndürür; içerik değişmişse aynı anahtarın farklı iş için kullanılmasını reddeder.”

**Parola neden geri okunamıyor?**  
“Şifreleme yerine tuzlu scrypt özeti saklıyoruz. Girişte verilen parolanın özeti yeniden hesaplanıp karşılaştırılıyor.”

**Düğmeyi gizlemek yetki kontrolü mü?**  
“Hayır. Görünürlük frontend’de, izin denetimi backend’de. Yönetici işlemlerinde Depends(manager) veya ilgili rol kontrolü var.”

**Arıza çözülünce bağlantı doğrulanmış oluyor mu?**  
“Hayır. Arıza çözümüyle fiziksel bağlantı kontrolü ayrı kayıtlar. Yeni bağlantı için ayrıca saha doğrulaması gerekir.”

**SL-A ile SL-T aynı kayıt mı?**  
“Aynı tablo yapısında farklı sl_type değerleriyle ayrı revizyonlar. SL-A mevcut değerlendirme, SL-T hedef. Ayrı gerekçe ve dayanaklarla izleniyor.”

**Kontrolden kaç puan alınca SL yükseliyor?**  
“Böyle bir otomatik formül yok. Sekiz soruluk kontrol listesi gözlem ve kanıt üretir. SL profilleri ayrıca değerlendirilip girilir.”

**Bilinmeyen seviye neden 0 değil?**  
“0 bir seviye değeri, None ise değerlendirilmemiş bilgi. Eksik veriyi belirli bir güvenlik seviyesi gibi göstermiyoruz.”

**Bir profili düzenleyince eski değer siliniyor mu?**  
“Yeni SL revizyonu ekleniyor; eski revizyonlar history içinde kalıyor. Kapsam değiştiğinde eski profil inceleme gerektiriyor.”

**Yüksek öncelikli işi yapan yönetici kendi işini kapatabilir mi?**  
“Hayır. verify sırasında aynı kişinin work veya submit kaydı var mı bakılıyor; varsa doğrulama reddediliyor.”

**İngilizceye geçince veri İngilizceye mi dönüşüyor?**  
“Hayır. Sabit arayüz parçaları çevriliyor. Cihaz adı, gözlem ve kanıt gibi kayıt değerleri aynen korunuyor.”

**Proje gerçek ağdan cihazları buluyor mu?**  
“Hayır. Mevcut sürüm kayıtlı envanter ve saha işlemlerine dayanıyor; çevrimiçi cihaz durumu veya ağ trafiği izlemiyor.”

**IEC 62443 sertifikası veriyor mu?**  
“Hayır. İlgili kavramları dokümantasyon ve değerlendirme iş akışında kullanıyor; resmi uygunluk veya sertifikasyon kararı vermiyor.”

## 15. Beş dakikalık kod gösterim sırası

| Süre | Açılacak kod | Söylenecek ana fikir |
| --- | --- | --- |
| 0:00–0:40 | `backend/main.py → create_app()` | Aynı uygulama statik frontend ve JSON API’yi sunuyor |
| 0:40–1:20 | `frontend/js/app.js → render()` | Hash adresi hangi ekran dalının çalışacağını belirliyor |
| 1:20–1:55 | `frontend/js/api.js → api()` | Form verisi JSON’a dönüşüp oturum ve CSRF ile sunucuya gidiyor |
| 1:55–2:30 | `backend/schemas.py → ConnectionInput` | Alan doğrulaması ile iş kurallarının ayrımı |
| 2:30–3:30 | `backend/services/connections.py → change_connection()` | Geçmiş, transaction, tekrar istek ve eşzamanlılık |
| 3:30–4:30 | `backend/services/ot.py → profiles()` | Mevcut/hedef ayrımı, kapsam güncelliği ve FR farkı |
| 4:30–5:00 | `backend/api/ot_routes.py → action_finding()` | Kanıt ve ayrı doğrulayıcıyla kapanan aksiyon |

Süre kısaysa HTML’nin uzun şablonunu satır satır okumak yerine fonksiyonun girdisini, çağırdığı API’yi ve veritabanında ürettiği sonucu anlat.

## 16. Hızlı bulma ve hata ayıklama kartı

| Soru / sorun | Önce bakılacak yer |
| --- | --- |
| “Bu ekran hangi dosyada?” | Çekirdek: `app.js → render()`; OT: `ot.js → renderOt()` |
| “Bu düğme ne çağırıyor?” | `data-action` değeri → `actions` veya `otActions` |
| “Formun alanları nerede?” | İlgili `...Form()` veya aksiyon; ortak iskelet `ui.js → modal()` |
| “Alanı neden reddediyor?” | Network yanıtı → `field_errors`; sonra `schemas.py` / `ot_schemas.py` |
| “Yetki hatası nereden geliyor?” | `authenticated()`, `manager()`, `may_work()`, OT aksiyon kontrolleri |
| “Kaydet neden çakışma döndürüyor?” | `version`, `expected_connection_id`, `expected_profile_id`, tekillik kısıtları |
| “Seviye farkı neden yok?” | İki profil var mı, onaylı mı, güncel mi? `profiles()` ve `comparable` |
| “Bir tabloya hangi kayıt yazılıyor?” | İlgili route içinde `INSERT` / `UPDATE`; bağlantıda ayrıca servis |
| “Logo eski geliyor?” | `shell()` / `login()` img adresi, statik dosya ve HTML’deki sürümlü JS/CSS URL’leri |
| “Dil değişmiyor?” | `i18n.js`, depolama izni, `translations.js`, sürümlü modül adresleri |
| “Grafik görünmüyor?” | Yerel Chart.js yüklemesi, canvas kimliği, `chart()` ve API’den gelen sayılar |
| “Yeni API ekledim ama 404?” | Router öneki, `main.py` bağlantısı ve açık sunucunun yeniden başlatılması |

Editörde proje genelinde arama için **Ctrl+Shift+F**; macOS’ta **Cmd+Shift+F** kullanılabilir. Önce görünen düğmenin `data-action` anahtarını veya endpoint’in sabit bölümünü ara. Satır numarasına bağımlı kalmak yerine fonksiyon adını bul.

Tarayıcının Network sekmesinde yöntem, adres, Request Payload, HTTP durumu ve JSON yanıtını birlikte incele. `422` genellikle alan doğrulamasına, `401` oturuma, `403` yetki/CSRF’ye, `409` güncellik veya kayıt çakışmasına işaret eder; kesin neden JSON mesajındadır.

## 17. Mevcut sınırlar ve geliştirme alanları

Savunmada eksik sorulduğunda mevcut kapsamı doğru anlatmak önemlidir:

- Canlı ağ keşfi, trafik izleme veya otomatik firewall uygulaması yoktur.
- SL değerleri ve kanıt yeterliliği insan değerlendirmesine dayanır; referans alanının varlığını denetlemek belgenin içeriğini doğrulamak değildir.
- Dosya/kanıt yükleme altyapısı yerine metin notu ve belge referansları tutulur.
- Gelişmiş hesap pasifleştirme, parola yenileme ve görev devri akışları tamamlanmamıştır.
- Kontrollü toplu veri aktarımı ve daha kapsamlı raporlar geliştirme alanıdır.
- SQLite’ın yoğun yazma yükü ve gerçek pilot işletimi ayrıca değerlendirilmelidir.
- `app.js` ve `ot.js` büyüdükçe ekran bazlı daha küçük modüllere ayrılabilir; bazı route iş kuralları servis katmanına taşınabilir.
- Mevcut sürüm ve bağlam denetimleri bütün eşzamanlılık durumlarının çözüldüğü iddiası değildir. Örneğin SL formu açıkken bağlantı kapsamının değişmesi gibi yarış koşulları pilot öncesi ayrıca güçlendirilmelidir.
- Denetim günlüğü uygulama içi izlenebilirlik sağlar; harici, değiştirilemez ve imzalı bir günlük altyapısı olarak tasarlanmamıştır.

**Son hazırlık:** Her önemli özellik için “ekrandaki yer → JavaScript fonksiyonu → API ucu → iş kuralı → tablo → test” zincirini bir kez kendi bilgisayarında takip et. Kod savunmasında en güçlü açıklama bu zinciri çalışan bir örnek üzerinde gösterebilmektir.
