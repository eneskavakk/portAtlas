# PortAtlas geliştirme durumu

Tarih: 31 Ekim 2026. Güncel sürüm: 0.2.0 yerel demo. Aşağıdaki ilk teslim kaydı 0.1.0 içindir; ikinci sprint güncellemesi belgenin sonunda bulunur. İlk planlardaki “henüz uygulanmadı” ifadeleri başlangıç tarihçesidir.

## İlk çalışan teslim

FastAPI, Python sqlite3 ve numaralı SQL migration yapısı kuruldu. Frontend ES modules, özel CSS ve onaylanan yerel Chart.js 4.6.1 kullanır. Ek bir UI framework veya CDN bağımlılığı yoktur. Kaynaklar `backend/`, `frontend/`, `scripts/` ve `tests/` altında bulunur.

| İş | Mevcut durum | Kanıt / sınır |
| --- | --- | --- |
| PA-001 | Uygulandı | Sanal ortam, migration, demo seed, boş kurulum ve admin CLI |
| PA-002 | Uygulandı | `/docs` ve `/openapi.json`; JSON hata ve sürüm sözleşmeleri; ortak arayüz |
| PA-003 | Uygulandı | HttpOnly/SameSite oturum, scrypt, CSRF, yetki ve pasif kullanıcı testi |
| PA-004 | Uygulandı | Giriş, gezinme, yükleme/boş/hata durumu; responsive menü |
| PA-005 | Kısmen uygulandı | Cihaz ekleme/düzenleme/arşivleme; konum oluşturma ve hiyerarşi. Konum düzenleme/taşıma henüz yok |
| PA-006 | Kısmen uygulandı | Kablo/arayüz oluşturma; switch oluştururken port sayısı; uygunluk güncelleme. Kablo/arayüz düzenleme ve arşivleme henüz yok |
| PA-007 | Uygulandı | Dört işlem türü, transaction, unique index, eski bağlantı kontrolü, tekrar anahtarı |
| PA-008 | Uygulandı | Pasaport, switch paneli, çoklu arayüz; 375–1440 px genişlik kontrolleri |
| PA-009 | Kısmen uygulandı | Bağlantıya özel doğrulama, uyuşmazlık ve önce/sonra geçmişi. Geçmişe düzeltme notu ve ayrıntılı filtreler henüz yok |
| PA-010 | Uygulandı | Arıza bildirme, atama, müdahale, bekleme/çözme/yeniden açma; rol ve kayıt sürümü kontrolü |
| PA-011 | Uygulandı | Gerçek DB'den genel bakış; cihaz/switch adı-kodu ve aktif kablo etiketinden cihaz arama |
| PA-012 | Uygulandı | Otomatik bütünlük kontrolleri ve tarayıcıdan bağlantı/arızayı sonuçlandırma |
| PA-013–015 | İş listesinde | OT kritiklik, şablon, değerlendirme, bulgu ve aksiyon ekranları |
| PA-016 | Kısmen uygulandı | Tüm tesisler için temel bağlantı CSV/yazdırma ve arıza durum grafiği. Gelişmiş filtreli raporlar henüz yok |
| PA-017 | İş listesinde | Kontrollü cihaz CSV aktarımı |
| PA-018 | Kısmen uygulandı | Hesap oluşturma ve rol gösterimi. Parola yenileme, rol değişikliği, son sorumlu koruması ve görev devri henüz yok |
| PA-019 | İş listesinde | Fotoğraf/PDF ekleri |
| PA-020 | Başlamadı | Tam ders kapsamı bitmedi; tüm 24 kaynak senaryosu geçmiş sayılmıyor |
| PA-021 | Kısmen uygulandı | SQLite backup CLI ve yedeğin bütünlük kontrolü. Tam pilot geri yükleme/yükseltme provası henüz yok |
| PA-022 | Başlamadı | Gerçek saha kabulü yapılmadı |

## Doğrulama kaydı

Otomatik API/domain testleri `tests/test_core.py` içinde bulunur. Son çalıştırmada 20 test geçti. Üst bağımlılıktan bir AnyIO deprecation uyarısı geldi; test hatası yok. Testler temsili SQLite verisini her seferinde yeni geçici dizinde oluşturur. Kapsam: oturum/CSRF/yetki, pasif hesap, değişken port sayısı, aktif uç tekilliği, uygun olmayan hedefler, eski bağlantı sürümü, idempotent tekrar, kablo değişimi ve sonlandırma, cihaz arşiv engeli, port arızasında mevcut bağlantının korunması, arıza yaşam döngüsü ve atama sınırı, konum sırası, isteğe bağlı IP, migration/backup ve paralel tarayıcı istekleri.

Taşıma sırasında geçmiş yazmasına hata enjekte edilerek eski bağlantının geri geldiği ve yeni bağlantı/istek kaydının oluşmadığı kontrol edilir. İki yazıcının aynı hedef porta eşzamanlı isteğinde birinin başarılı, diğerinin çakışma aldığı doğrulanır.

Tarayıcı kabulü: yerel sunucuda admin oturumu açıldı. Genel aramada CNC-014 bulundu. Ethernet-1 / KBL-0087, SW-HAT2-01 Port 05'ten Port 08'e gerekçeli taşındı ve ARZ-001 ile ilişkilendirildi. Eski ve yeni kayıtların tarih sınırı SQLite üzerinden kontrol edildi. Yeni bağlantı sahada doğrulandı. Port 05 ayrıca arızalı işaretlendi. ARZ-001 incelemeye alındı, müdahale eklendi, saha kontrolü ve çözüm açıklamasıyla çözüldü. Switch paneliyle pasaport aynı Port 08 kaydını gösterdi.

375 px port paneli ve pasaport görsel olarak incelendi. Pasaportta 375, 768, 1024 ve 1440 px genişliklerinde sayfa taşması bulunmadı. Mobilde geniş tablolar kendi yatay kaydırma alanındadır; tam mobil liste dönüşümü sonraki iyileştirmedir. Grafikler API sonuçlarıyla hazırlanır; canlı cihaz durumu gösterilmez.

Tarayıcı kontrolünde bulunan istekler arası worker thread değişimi sorunu, her HTTP isteğine ayrı SQLite bağlantısı ve `check_same_thread=False` ile düzeltildi. Sonraki paralel okuma testi bu durumu kapsar. Test başlangıcında bu bilgisayarın Anaconda readline/pdb modülü çöktüğü için yalnızca pytest debugging eklentisi kapatıldı.

## Sonraki geliştirme sırası

1. Envanter/konum düzenleme ve geçmiş düzeltme eksiklerini tamamlamak; filtreye geri dönüşü korumak.
2. OT kontrol listesi sürümleri ve değerlendirme; ardından bulgu/aksiyon/doğrulama.
3. Kullanıcı görev devri ve parola yenileme; kontrollü CSV aktarımı.
4. Filtreli raporlar, kanıt ekleri ve tüm kaynak kabul senaryoları.
5. Saha verisiyle yedek/geri yükleme ve pilot kabulü.

Yerel demo, gerçek sahada kullanıma hazır pilot veya tam 17 ekran teslimi olarak sunulmaz.

## İkinci sprint güncellemesi

Kullanıcı zone oluşturma, SL-T hedefi ve SL-A mevcut değerlendirmesi istedi. Bunun üzerine kapsam genişletilerek [OT güvenlik sprintindeki](07_OT_SPRINTI.md) sistem/zone/conduit, seviye revizyonları ve aksiyon takibi uygulandı.

PA-013: cihaz kritiklik kaydı ve sürümlü sabit PortAtlas-OT-v1 kontrolü uygulandı. Dinamik şablon düzenleme henüz yok. PA-014: kapsam dışı onayı, mükerrer kontrol bulgusu engeli, sorumlu/tarih/öncelik geçmişi, kanıt referanslı aksiyon ve farklı doğrulayıcı kuralı uygulandı. Uygulanamaz kararını reddederek taslağa döndürme henüz yok. PA-015: OT genel görünümü, zone/conduit profilleri, açık/gecikmiş bulgular, bilinmeyen kritiklik ve zone atanmamış cihazlar listeleniyor. Kuruma özgü dönem bazlı kritik cihaz raporu sonraki iş olarak duruyor.

Son doğrulama: 44 otomatik test geçti; bunların 20'si ilk sprintin çekirdek testleri. OT testleriyle birlikte 12 yeni görünümün gerçek API cevaplarından HTML üretimi de kontrol edildi. Yerel HTTP sunucusunda v0.2.0, OT uçları ve statik dosyalar doğrulandı. Eski CNC-014 / Port 08 bağlantısı korundu. Temsili 1 SUC, 3 zone ve 1 conduit eklendi; seviye veya kanıt uydurulmadı. Yeni OT ekranları için tarayıcı görsel/etkileşim kabulü bu sprintte yapılmadı. Ayrıntılar ve sonraki öneriler sprint belgesinde.
