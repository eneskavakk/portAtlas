# PortAtlas teslim planı ve iş listesi

Tarih: 31 Ekim 2026. Ekip: iki kişi. Hedef: en kısa sürede çalışan ders demosu, ardından tam ders kapsamı ve saha pilotu. Kesin teslim tarihi henüz verilmedi.

## Çalışma biçimi

PM sorumluluğu kapsamı, önceliği, bağımlılıkları, kararları, kabul koşullarını ve sürüm hazırlığını takip etmektir. Ürün sahibi kapsam değişikliklerini ve tasarım kütüphanelerini onaylar. İki geliştirici için A/B sorumlulukları önerilir; kişilerin güçlü yönleri bilinmediğinden isim ataması yapılmadı.

Geliştirici A backend, veri modeli ve bütünlük akışlarını; geliştirici B vanilla JS ekranlarını ve responsive davranışları üstlenir. Birlikte önce API sözleşmesini, sonra günlük entegre akışı kontrol ederler. Frontend geçici veriyi yalnızca geliştirme sırasında kullanabilir; kabul demosu kalıcı API/SQLite üzerinde çalışır.

İş durumları: İş listesinde, Hazır, Geliştiriliyor, Kontrolde, Kabul edildi, Engelli. Aynı kişi aynı anda bir ana işe odaklanır. Bir iş API/arayüz/veri akışı ve kabul koşulu tamamlanmadan bitti sayılmaz. Engeller karar kaydına, yeni fikirler özellik önerilerine eklenir.

## Kilometre taşları

Aşağıdaki süreler başlangıç efor tahminidir; ekip deneyimi, günlük çalışma süresi ve ders koşulları bilinmediğinden teslim taahhüdü değildir. Kişi-gün bir kişinin bir çalışma günüdür. İlk iki geliştirme günündeki gerçek ilerlemeyle yeniden tahmin edilir.

| Aşama | Teslim | Başlangıç eforu | Çıkış koşulu |
| --- | --- | --- | --- |
| T0 Temel hazırlık | API sözleşmesi, şema, kurulum, örnek veri, ilk sorumlu ve arayüz iskeleti | 2–3 kişi-gün | İki kişinin aynı veritabanı sürümünü kurabilmesi ve oturum açması |
| T1 Bağlantı çekirdeği | Cihaz/konum/kablo/arayüz, pasaport, port paneli, atomik değişiklik ve geçmiş | 7–10 kişi-gün | Taşıma, çifte atama engeli, rollback, doğrulama sıfırlama geçer |
| T2 İlk uçtan uca demo | Arıza açma/atama/müdahale/çözüm, temel genel bakış ve mobil pasaport | 4–6 kişi-gün | CNC-014 demo senaryosu gerçek API/SQLite ile tamamlanır |
| T3 Tam ders kapsamı | OT kontrolleri/bulgular, rapor, CSV aktarımı, kullanıcı yönetiminin ayrıntıları | 9–13 kişi-gün | 17 ekran ve 24 kaynak kabul senaryosu tamamlanır |
| T4 Pilot hazırlığı | Geri yükleme, pilot kurulum, gerçek veri örneği, saha kabulü ve kullanım notları | 4–6 kişi-gün + saha bekleme süresi | Gerçek kullanıcı görevleri ve işletim kontrolleri geçer |

T0–T2 toplamı 13–19 kişi-gündür. İki kişinin tam zamanlı ve bağımlılıklar olmadan çalıştığı iyimser durumda yaklaşık 7–10 iş günü eder; entegrasyon ve hata düzeltmeleri takvim süresini uzatabilir. T3 dahil toplam 22–32 kişi-gündür. İlk gösterim T2'de yapılabilir; T3 tamamlanmadan “tam ders sürümü” ilan edilmez.

Hız için ayrı landing page, mikroservis, kapsamlı animasyon, AI, XLSX, harita/topoloji editörü ve özelleştirilebilir dashboard ilk geliştirmeye alınmaz. Mobil pasaport, yetkilendirme ve veri bütünlüğü ertelenmez.

## Öncelikli iş listesi

P0 ilk demo, P1 tam ders sürümü, P2 pilot/iyileştirme önceliğidir. Tüm işler başlangıçta “İş listesinde” durumundadır. Eforlar milestone toplamlarının içindedir; aşağıdaki tablo ek efor değildir.

| ID | Öncelik | İş ve kabul koşulu | Sorumlu | Bağımlılık |
| --- | --- | --- | --- | --- |
| PA-001 | P0 | Proje kurulumu, yapılandırma, migration ve demo seed tek komut akışıyla çalışır | A | Yok |
| PA-002 | P0 | API hata/filtre/sürüm sözleşmesi ve ortak arayüz iskeleti belirlenir | A+B | Yok |
| PA-003 | P0 | Oturum, iki rol, pasif hesap ve backend yetki kontrolü çalışır | A | 001–002 |
| PA-004 | P0 | Giriş, gezinme, hata/boş/yükleme durumları ve mobil menü çalışır | B | 002–003 |
| PA-005 | P0 | Konum ağacı ve cihaz CRUD; tekil kod ve aktif bağlı cihaz arşiv engeli | A+B | 001–004 |
| PA-006 | P0 | Arayüz/kablo/port tanımı, farklı port sayıları ve port uygunluğu kaydı | A+B | 005 |
| PA-007 | P0 | Bağlantı kurma/taşıma/kablo değişimi/sonlandırma atomik ve gerekçeli | A | 006 |
| PA-008 | P0 | Pasaport ve port paneli aynı aktif uçları gösterir; mobil kullanılır | B | 006–007 |
| PA-009 | P0 | Saha doğrulaması, uyuşmazlık ve önce/sonra geçmişi korunur | A+B | 007–008 |
| PA-010 | P0 | Arıza açma, atama, müdahale, çözüm ve yeniden açma rol kurallarıyla çalışır | A+B | 003, 008–009 |
| PA-011 | P0 | Genel bakış ve cihaz/switch/kablo araması gerçek veriyi kullanır | A+B | 008–010 |
| PA-012 | P0 | CNC-014 uçtan uca kabulü, yarış durumu ve rollback kanıtı kaydedilir | A+B | 007–011 |
| PA-013 | P1 | Kritiklik/bölge, OT01–OT08 şablon sürümü ve taslak/tamamlanmış değerlendirme | A+B | 005, 009 |
| PA-014 | P1 | Uygulanamaz onayı, mevcut bulgu önerisi ve aksiyon/doğrulama akışı | A+B | 013 |
| PA-015 | P1 | OT genel görünümünde açık/gecikmiş/bilinmeyen ayrımları ve pasaport bağlantıları | B | 014 |
| PA-016 | P1 | Rapor filtreleri, sayım tanımları, CSV ve yazdırma aynı kapsamda | A+B | 010–015 |
| PA-017 | P1 | Cihaz CSV önizleme/onay, satır hataları, tekrar ve commit çakışması | A+B | 005 |
| PA-018 | P1 | Kullanıcı ekranı, parola yenileme, son sorumlu koruması ve iş devri | A+B | 003, 010, 014 |
| PA-019 | P1 | Fotoğraf/PDF ekleri, yetkili indirme ve dosya doğrulama | A+B | 003, 010, 014 |
| PA-020 | P1 | 24 kaynak kabul senaryosu, responsive kontrol ve ders sunum provası | A+B | 012–019 |
| PA-021 | P2 | Tutarlı DB/ek yedeği, geri yükleme ve sürüm yükseltme provası | A | 020 |
| PA-022 | P2 | Gerçek konum/etiket örnekleriyle saha pilotu, kullanıcı görev gözlemi | A+B + saha sorumlusu | 021, saha kararları |

## Kabul senaryosu izlenebilirliği

Kaynak: S1 bölüm 16 ve 23. Aşağıdakiler planlanan testlerdir; hiçbiri şu anda geçmiş değildir.

| Senaryo | Doğrulanan davranış | İlgili işler |
| --- | --- | --- |
| 01 | Tekrarlı varlık kodu engellenir | 005 |
| 02 | İki arayüz bağımsız bağlantı taşır | 006–008 |
| 03 | Dolu porta ikinci aktif bağlantı kurulamaz | 007, 012 |
| 04 | Aynı kablo ikinci aktif bağlantıya atanamaz | 007, 012 |
| 05 | Arızalı/devre dışı porta yeni bağlantı kurulamaz | 006–007 |
| 06 | Port 05 → 08 taşınır, eski kayıt korunur | 007–009 |
| 07 | İki kullanıcının aynı portu seçmesinde ikinci işlem engellenir | 007, 012 |
| 08 | Değişiklik sonrası eski doğrulama aktarılmaz | 009 |
| 09 | Eksik çözümle arıza kapanmaz | 010 |
| 10 | Yeniden açma gerekçeli; eski çözüm korunur | 010 |
| 11 | Teknisyen kullanıcı yönetimi işlemi yapamaz | 003, 018 |
| 12 | Aktif bağlı cihaz arşivlenemez | 005, 007 |
| 13 | Telefonda pasaport ve saha işlemleri erişilir | 008, 020 |
| 14 | Filtreli rapor ve dışa aktarma kapsamı aynıdır | 016 |
| 15 | Hatalı/mükerrer aktarım satırları açıklanır | 017 |
| 16 | Yanıt kesilince kayıt sonucu kontrol edilir; ikinci değişiklik oluşmaz | 007, 012 |
| OT1 | Kritiklik yoksa Bilinmiyor görünür | 013, 015 |
| OT2 | Bilinmiyor açıklama ister ve uygun sayılmaz | 013 |
| OT3 | Uygulanamaz gerekçe ve sorumlu onayı gerektirir | 013–014 |
| OT4 | Aynı cihaz/madde açık bulgusu önerilir | 014 |
| OT5 | Aksiyon tamamlandı yalnızca doğrulama beklemeye götürür | 014 |
| OT6 | Yüksek öncelikte uygulayan kendi işini doğrulayamaz | 014 |
| OT7 | Hedef tarih değişikliğinin eski değeri ve gerekçesi korunur | 014 |
| OT8 | Port değişimi ilgili kontrolü tekrar değerlendirmeye açar | 009, 013–014 |

Kaynaklara ek teknik kabul: taşıma ortasında hata enjekte edilince tüm yazmalar geri alınır; HTTP isteği doğrudan gönderildiğinde rol koruması çalışır; kapanış ve sürüm çakışmaları korunur; son sorumlu pasifleştirilemez; tamamlanan OT değerlendirmesi şablon değişikliğinden etkilenmez; yedek geri yüklenince eklerle ilişkiler tutarlıdır.

Her kabul kaydı örnek veri, adımlar, beklenen/gözlenen sonuç, tarih ve doğrulayan kişi içerir. Sayfa açılmasının tek başına başarı kabul edilmemesi gerekir.

## İki sunum akışı

İlk demo: Hat 2 / İstasyon 4 içindeki CNC-014 ve Ethernet-1, KBL-0087 ile SW-HAT2-01 Port 05'e bağlıdır. Arıza açılır ve atanır. Port 08'e gerekçeli taşıma yapılır. Eski Port 05 ayrıca arızalı işaretlenir. Eski kayıt geçmişte, yeni bağlantı doğrulama bekliyor görünür. Saha doğrulaması ve çözüm açıklamasıyla arıza çözülür. Aynı bağlantı pasaport ve panelde görülür.

Tam ders sürümü: SW-HAT2-01 Port 12 için OT03 gözlemi kaydedilir, mevcut açık bulgu yoksa OT-007 açılır. Sorumlu öncelik/teknisyen/hedef tarih atar. Aksiyon tamamlanınca doğrulama bekler. Yüksek öncelikte farklı yetkili kişi doğrular. Rapor ve geçmiş aynı sonucu gösterir. Demo sıfırlama işlemi yalnızca ayrı demo veritabanında çalışır.

## Ek modül ve özellik önerileri

Bunlar onaylanmış teslim kapsamı değildir. Eforlar ilk kaba tahmindir.

| Sıra | Öneri | Değer | Efor | Önerilen zaman ve bağımlılık |
| --- | --- | --- | --- | --- |
| 1 | QR etiketinden pasaport | Sahada cihaz bulmayı hızlandırma potansiyeli | Küçük | T3 sonrası; kalıcı cihaz URL'si ve giriş kontrolü |
| 2 | Planlı saha doğrulama görevleri | Eski kayıtların kontrollü güncellenmesi | Orta | Pilot sonrası; kurumun kontrol aralığı kararı |
| 3 | Uygulama içi görev bildirimleri | Atanan/geciken işleri görünür kılar | Küçük–orta | T3 sonrası; mevcut iş kayıtları yeterli |
| 4 | Veri kalitesi görünümü | Eksik etiket, bilinmeyen kritiklik ve doğrulanmamış bağlantıları toplar | Küçük | Pilot başlangıcı; sahte güvenlik skoru üretmeden |
| 5 | Vardiya devir özeti | Açık arıza ve tamamlanmamış saha işlerini devreder | Orta | Pilot ihtiyacı doğrulanırsa; rol/iş geçmişi |
| 6 | Patch panel ve çok parçalı bağlantı yolu | Gerçek tesis kablolamasını daha geniş kapsar | Büyük | V2; doğrudan bağlantı modelinin yeniden tasarımı |
| 7 | Teknik doküman kütüphanesi | Kılavuzları cihaz pasaportuna bağlar | Orta | V2; ek dosyalar, sürüm ve erişim modeli |
| 8 | Kaynak gösteren yerel AI asistanı | Teknik belge aramasını destekleme potansiyeli | Çok büyük | Ayrı keşif; 7, veri kalitesi, model/donanım ve yanıt değerlendirmesi |
| 9 | Çevrimdışı saha kaydı | Bağlantısı zayıf bölgelerde kullanım | Büyük | Saha ihtiyacı ölçülürse; senkronizasyon ve çakışma çözümü |

İlk ek özellik önerisi QR erişimidir. AI modülü çekirdek sistemin güvenilirliği ve pilot ihtiyacı doğrulanmadan öncelik kazanmaz.

## Riskler ve izleme

| Risk | Etki | Önlem ve kapanış kanıtı |
| --- | --- | --- |
| Kesin tarih ve günlük kapasite bilinmiyor | Plan gerçek takvime bağlanamaz | İlk iki gün sonrası efor revizyonu; ders teslim tarihi öğrenilir |
| 17 ekranın aynı anda geliştirilmesi | Entegrasyon gecikir | Önce T2 uçtan uca akış, sonra T3 |
| SQLite yazma çakışması | Yarım/tekrarlı işlem veya bekleme | Kısa transaction, unique index, sürüm ve tekrar anahtarı; yarış testi |
| Saha etiketleri/veri kalitesi | Doğru ekran yanlış bilgi sunar | Pilot veri örneği ve saha doğrulaması |
| Tek sorumlu ile yüksek öncelikli bulgu | Farklı doğrulayıcı bulunamaz | Pilot ekipte ikinci yetkili doğrulayıcı belirlenir; kural atlanmaz |
| Kapsamın AI/topolojiye genişlemesi | İlk demo gecikir | Ayrı öneri listesi ve değişiklik kararı |
| Sadece başarılı yolun test edilmesi | Demo sonrası veri kaybı | Rollback, yetki, yeniden deneme ve geri yükleme kabulü |
