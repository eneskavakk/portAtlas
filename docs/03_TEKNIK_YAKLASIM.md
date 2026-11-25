# PortAtlas teknik yaklaşım

Tarih: 31 Ekim 2026. Python, vanilla JavaScript ve SQLite kesin kullanıcı kararlarıdır. Aşağıdaki framework, paket ve şema ayrıntıları PM teknik önerisidir; henüz kurulmuş veya uygulanmış değildir.

## Önerilen uygulama yapısı

Tek Python uygulamasının REST/JSON API ve statik HTML/CSS/JS dosyalarını aynı origin üzerinden sunması önerilir. Backend için FastAPI; frontend için ES modules, Fetch API ve özel CSS yeterlidir. İlk kurulumda ayrı Node sunucusu, frontend framework, mikroservis veya mesaj kuyruğu gerekmemelidir.

FastAPI önerisinin nedeni tipli istek doğrulama ve otomatik API sözleşmesidir. Bu, ekipte backend ve frontend işlerinin aynı sözleşmeyle ilerlemesini kolaylaştırır. Kaynak: [FastAPI resmi belgeleri](https://fastapi.tiangolo.com/).

Önerilen klasörler: `backend/api`, `backend/services`, `backend/repositories`, `backend/db/migrations`, `frontend/css`, `frontend/js/api`, `frontend/js/components`, `frontend/js/pages`, `tests`, `scripts`. İş kuralları service katmanında; SQL repository katmanında; görünüm ve kullanıcı olayları frontend modüllerinde tutulur.

İlk sürümde Python `sqlite3` ile parametreli sorgular ve numaralı SQL migration dosyaları önerilir. ORM zorunlu değildir. Her migration kaydı sürüm tablosunda tutulur ve boş veritabanı kurulumu ile önceki sürümden yükseltme doğrulanır. Bu seçim ilk geliştirme işinde tekrar değerlendirilip karar kaydına işlenmelidir.

## Kurulum sınırı

Tarayıcılar HTTP(S) üzerinden Python sunucusuna erişir. SQLite dosyası sunucunun yerel kalıcı diskinde bulunur. Dosya istemcilere dağıtılmaz, ağ paylaşımına konmaz. WAL okuyucu/yazıcı eşzamanlılığına yardımcı olur; aynı anda tek yazıcı sınırı sürer. Kaynak: [SQLite WAL](https://www.sqlite.org/wal.html).

Bağlantı başına `foreign_keys=ON`, kontrollü `busy_timeout`, kısa transaction ve uygun WAL yapılandırması planlanır. SQLite sürümü geliştirme başlangıcında resmi sürüm notlarına göre seçilip sabitlenir. Sadece async endpoint yazmak SQLite yazma kapasitesini artırmaz.

## Veri modeli taslağı

| Grup | Önerilen tablolar | Temel ilişki ve kurallar |
| --- | --- | --- |
| Kimlik | users, sessions | Aktiflik, rol, parola özeti, oturum iptali; geçmişte kullanıcı FK korunur |
| Konum | locations, device_location_events | Parent/tür/ad; eski ve yeni konum hareketi; döngü kontrolü |
| Envanter | devices, network_interfaces, cables, switch_ports | Tekil varlık/kablo; switch içinde tekil port; cihaz içinde tekil arayüz adı |
| Bağlantı | connections, connection_changes, field_verifications | Başlangıç/bitiş, önceki/yeni bağlantı, gerekçe, yapan, doğrulama olayları |
| Arıza | incidents, interventions, incident_events | Atama, durum geçmişi, çözüm ve yeniden açma olayları; ilgili bağlantı değişikliği |
| OT bağlamı | security_zones, criticality_events | Bölge etiketi, kritiklik ve değerlendirme gerekçesi; konumdan ayrı |
| Kontrol | checklist_templates, checklist_versions, checklist_items, assessments, assessment_results, applicability_approvals | Tamamlanan değerlendirme sabit sürüme bağlı; uygulanamaz onayı bağımsız |
| Bulgu | findings, finding_actions, finding_events, finding_verifications | Cihaz zorunlu, port/bağlantı isteğe bağlı; hedef tarih ve sorumlu geçmişi |
| Destek | attachments, import_batches, import_rows, audit_events, request_keys, schema_migrations | Yetkili dosya erişimi, aktarım özeti, güvenli tekrar, şema sürümü |

Bu tablo listesi fiziksel şemanın son hali değildir. Birleştirme veya ayrıştırma, iş kurallarını koruyan veri tasarımı sırasında yapılabilir.

Değiştirilebilir kayıtlarda `version`, `created_at`, `updated_at` bulunur. Zamanlar UTC saklanır; arayüz Europe/Istanbul gösterir. Takvim hedef tarihleri ayrıca tarih olarak ele alınır; gecikme hesabı tesis saat dilimine göre yapılır. Kayıt kodları veritabanı kimliğinden ayrı kullanıcıya okunabilir alanlar olabilir.

## Aktif bağlantının bütünlüğü

`connections` için en az `interface_id`, `port_id`, `cable_id`, `started_at`, `ended_at`, `created_by` ve işlem ilişkisi gerekir. Aktiflik `ended_at IS NULL` üzerinden türetilir.

```sql
CREATE UNIQUE INDEX uq_active_connection_interface
ON connections(interface_id) WHERE ended_at IS NULL;

CREATE UNIQUE INDEX uq_active_connection_port
ON connections(port_id) WHERE ended_at IS NULL;

CREATE UNIQUE INDEX uq_active_connection_cable
ON connections(cable_id) WHERE ended_at IS NULL;
```

Bu tasarım aynı ucun iki aktif bağlantıya atanmasını veritabanı seviyesinde engellemeyi amaçlar. SQLite unique partial index desteği: [resmi belge](https://www.sqlite.org/partialindex.html).

Port uygunluğu, cihaz aktifliği ve kayıt sürümü transaction içinde yeniden okunur. Servis doğrulamaları ve gerekiyorsa DB trigger'ları birlikte tasarlanır. Yalnızca hedef port listesini filtrelemek yeterli değildir.

Taşıma işlemi sırası:

1. Kullanıcı/rol, beklenen kayıt sürümü ve istek tekrar anahtarı kontrol edilir.
2. Kısa yazma transaction'ı başlatılır; mevcut bağlantı ve hedef uçlar yeniden okunur.
3. Eski bağlantı aynı işlem zamanında sonlandırılır; yeni kayıt açılır.
4. Değişiklik geçmişi ve ilgili arıza ilişkisi yazılır. Yeni bağlantıya eski saha doğrulaması kopyalanmaz.
5. Bütün yazmalar başarılıysa commit yapılır. Hata varsa tamamı rollback olur.
6. Ağ yanıtı kaybolursa istemci aynı istek anahtarıyla sonucu sorgular/yeniden ister. İşlem ikinci kez uygulanmaz.

İstek anahtarı kullanıcı, işlem kapsamı ve içerik özetiyle bağlanmalıdır. Aynı anahtarın farklı içerikle tekrar kullanımı reddedilir. Kilit bekleme süresi dolduğunda anlaşılır, tekrar denenebilir hata verilir; sınırsız otomatik tekrar yapılmaz.

## API sözleşmesi başlangıcı

| Kaynak | Örnek uçlar | Beklenen davranış |
| --- | --- | --- |
| Oturum | `/api/auth/login`, `/logout`, `/me` | Sunucu taraflı oturum; çıkış ve pasifleştirmede iptal |
| Envanter | `/api/devices`, `/locations`, `/interfaces`, `/cables`, `/switches/{id}/ports` | Filtre, sayfalama, sürüm kontrollü değişiklik |
| Pasaport | `/api/devices/{id}/passport` | Aynı bağlantı kaynağından güncel özet ve ilişkiler |
| Bağlantı | `/api/connections`, `/api/connection-changes`, `/api/connections/{id}/verifications` | İşlem türüyle atomik değişiklik; doğrulama ayrı olay |
| Arıza | `/api/incidents`, `/{id}/interventions`, `/{id}/transitions` | İzin verilen durum geçişi ve gerekçe doğrulaması |
| OT | `/api/assessments`, `/api/findings`, `/api/findings/{id}/transitions` | Sürümlü kontrol ve doğrulamalı bulgu |
| Aktarım | `/api/imports/preview`, `/api/imports/{id}/commit` | Aynı önizlemenin kontrollü onayı; commit anında tekrar doğrulama |
| Rapor | `/api/reports/{type}`, `/api/reports/{type}/export` | Ortak filtre şeması ve aynı sonuç kapsamı |

Endpoint adları uygulama öncesi OpenAPI sözleşmesiyle kesinleştirilir. Hatalarda ortak `code`, `message`, `field_errors`, `request_id` yapısı önerilir. Doğrulama hatası 422, kimlik doğrulama 401, yetki 403, bulunamayan kayıt 404, sürüm/iş kuralı çakışması 409 olarak ayrılır. Frontend tekrar kayıt yapmadan önce işlem sonucunu kontrol edebilir.

## Oturum ve dosyalar

Tarayıcı uygulamasında HttpOnly, SameSite cookie ile sunucu taraflı oturum önerilir. Pilot ortamda HTTPS ve Secure cookie gerekir. Yazma isteklerinde CSRF koruması, rol/atama kontrolü; girişte hız sınırlaması ve güvenilir parola özeti kullanılır. Parola düz metin veya genel audit içine yazılmaz. İlk sorumlu komut satırı kurulumuyla oluşturulur; sabit demo parolası pilotta kullanılmaz.

Ekler veritabanı dışında, web kökünden ayrı dizinde; metadata ve ilişki DB içinde saklanır. Dosya türü/boyutu doğrulanır, sunucunun ürettiği ad kullanılır ve her indirmede yetki kontrol edilir. İlk kapsam fotoğraf ve PDF önerisidir; limitler karar kaydında açık tutulur. Eklere parola veya gizli anahtar konmaz.

## Aktarım ve rapor karar önerileri

CSV başlangıç sütunları: `asset_code`, `name`, `device_type`, `location_code`, `description`. Konumların önceden tanımlanmış tekil kodu kullanılmalıdır; aynı isimli farklı konumlar isimden tahmin edilmez. Bu nedenle konum kodu veri tasarımına eklenmesi önerilen teknik ayrıntıdır.

Dosya içi ve mevcut veriyle mükerrerler önizlemede gösterilir. Kullanıcının onayladığı uygun satırlar commit anında yeniden kontrol edilir. Araya giren değişiklik nedeniyle geçersizleşen satır atlanır ve nedeni raporlanır; mevcut kayıt sessizce güncellenmez. Bir aktarım onayı ikinci kez yeni kayıt üretmez.

İlk rapor çıktısı UTF-8 CSV ve print CSS ile tarayıcı yazdırması/PDF kaydı önerilir. Bu, sunucuda üretilen kurumsal PDF raporunun eşdeğeri sayılmaz. XLSX veya sunucu PDF üretimi ayrıca kapsamlandırılır. CSV dışa aktarmada formül olarak yorumlanabilecek kullanıcı verileri güvenli biçimde işlenir.

## Pilot işletim ölçütleri

Veritabanı ve eklerin tutarlı yedeği alınmalı, ayrı ortamda geri yükleme denenmelidir. WAL açıkken sadece ana `.db` dosyasını gelişigüzel kopyalamak yerine SQLite backup mekanizması veya kontrollü tutarlı yedek yöntemi seçilir. Operasyon kaydı ve uygulama hata logu ayrılır; loglar gizli bilgiler içermez.

Pilot cihaz/kullanıcı sayısı ve eşzamanlı yazma yükü öğrenilmeden performans garantisi verilmez. SQLite seçimi korunur; yük testi başarısız olursa önce transaction süreleri, sorgular ve indeksler iyileştirilir. Veritabanı değişimi ancak ayrı kullanıcı kararıyla değerlendirilir.
