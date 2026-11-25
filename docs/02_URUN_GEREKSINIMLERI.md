# PortAtlas ürün gereksinimleri

Sürüm: 0.1. Tarih: 31 Ekim 2026. Durum: Kaynaklardan türetilen geliştirme başlangıcı ve PM önerileri. Kaynak referansları `01_KAYNAK_INCELEMESI.md` içinde tanımlıdır.

## Ürün amacı ve teslim ayrımı

Teknisyen bir makineyi bulduğunda konumunu, her fiziksel arayüzünün kayıtlı kablo/switch/port ilişkisini, son saha doğrulamasını ve geçmiş müdahaleleri tek pasaportta görebilmelidir. IT/OT sorumlusu kayıtların bütünlüğünü, açık arızaları ve OT bulgularının doğrulanarak kapanmasını yönetebilmelidir.

İlk gösterilebilir demo, temel bağlantı ve arıza akışını uçtan uca tamamlar. Tam ders sürümü kaynaklardaki 5 modül ve 17 ekranı kapsar. Saha pilotu, bu işlevlerin yanında kurulum, geri yükleme ve gerçek kullanıcı kabulü gerektirir. Bir ara demonun bitmesi tam sürümün bittiği anlamına gelmez.

İlk sürüm tek işletmenin birden fazla tesis/konumunu destekler. Doğrudan makine arayüzü–kablo–switch portu modeli kullanılır. Otomatik keşif, ping/SNMP izleme, uzaktan cihaz yönetimi, patch panel yolları, switch uplink topolojisi ve AI teşhis kapsam dışıdır.

## Roller

| İşlem | IT/OT sorumlusu | Teknisyen |
| --- | --- | --- |
| Envanter, bağlantı, geçmiş ve rapor görme | Evet | Evet |
| Cihaz, konum, kablo, arayüz ve switch portu tanımlama | Evet | Hayır |
| Bağlantı kurma, değiştirme, saha doğrulama | Evet | Evet |
| Arıza açma ve müdahale ekleme | Evet | Evet |
| Arıza atama | Evet | Hayır |
| Arıza çözme ve yeniden açma | Tüm kayıtlar | Atandığı kayıtlar |
| Kullanım dışına alma ve kullanıcı yönetimi | Evet | Hayır |
| OT değerlendirmesi ve bulgu oluşturma | Evet | Evet |
| OT aksiyonu güncelleme | Evet | Kendisine verilen aksiyon |
| Kritiklik, şablon, bulgu önceliği, sorumlu ve hedef tarih yönetimi | Evet | Hayır |
| OT bulgusunu doğrulayıp kapatma | Evet | Hayır |

Yetki kontrolü backend üzerinde yapılır. Arayüzde düğmeyi gizlemek yeterli değildir. Pasif hesap yeni işlem yapamaz; geçmişteki kimliği korunur. Atanmamış arıza için teknisyen ekranında “Atama bekliyor” gösterilir. Arıza iptali ve başkasına atanmış arızaya müdahale ekleme sınırları açık karar listesinde tutulur.

## Modüller ve tamamlanma ölçütleri

| Modül | Kapsam | Tamamlanma ölçütü | Kaynak |
| --- | --- | --- | --- |
| M1 Varlık ve konum | Makine/switch, konum ağacı, arayüz, kablo, arşivleme | Benzersiz kod, döngüsüz konum, yer değişikliği geçmişi; aktif bağlı öğe arşivlenemez | S1 §3, §8, §11 |
| M2 Port ve bağlantı | Değişken sayıda port, kayıtlı doluluk, kullanım uygunluğu, saha doğrulaması | Pasaport ve port paneli aynı aktif bağlantıyı gösterir; uçlar çifte atanmaz | S1 §4, §9–11 |
| M3 Değişiklik | Oluşturma, port taşıma, kablo değiştirme, sonlandırma, gerekçeli düzeltme | Eski/yeni bağlantı ve işlem günlüğü tek transaction ile yazılır; başarısızlıkta eski durum korunur | S1 §4–5, §11–12 |
| M4 Arıza ve müdahale | Bildirim, atama, inceleme, bekleme, çözüm, yeniden açma | Çözüm açıklaması ve doğrulama olmadan kapanmaz; eski çözüm korunur | S1 §5, §12–13 |
| M5 OT kontrol ve bulgu | Kritiklik, bölge etiketi, sürümlü kontrol listesi, aksiyon, doğrulama | Bilinmeyen uygun sayılmaz; yüksek öncelikte uygulayan ve doğrulayan farklıdır | S1 §18–24 |

Ortak işlevler: oturum, genel arama, genel bakış, kullanıcı yönetimi, raporlar, kontrollü cihaz CSV aktarımı, mobil görünüm ve ek dosyalar.

## Ekran envanteri

| Ekran | Ana amaç | Başlıca kabul noktası | Teslim |
| --- | --- | --- | --- |
| E01 Giriş | Yetkili oturum | Hatalı giriş genel mesaj verir; pasif hesap engellenir | Demo |
| E02 Genel bakış | Açık işler ve güncelleme özeti | Gösterge ile açılan liste aynı filtreyi kullanır; veri hatası sıfır gösterilmez | Demo temel / tam sürüm ayrıntı |
| E03 Cihazlar | Makine/switch kaydı | Tekil varlık kodu, filtre, bağlı cihazı arşivleme engeli | Demo |
| E04 Konumlar | Tesis/bölge/hat/istasyon | Kendi altına taşıma ve bağlı kaydı olan konumu silme engeli | Demo |
| E05 Makine pasaportu | Bağlantı ve müdahale merkezi | Çoklu arayüz; bağlantı/doğrulama/geçmiş tutarlılığı | Demo / OT sekmesi sonra |
| E06 Switch port paneli | Porttan makineye erişim | Port sayısı tanımdan gelir; doluluk ve uygunluk ayrıdır | Demo |
| E07 Kablo ve arayüz | Fiziksel uç envanteri | Kablo tekil, aynı makinede arayüz adı tekil, boş IP kabul edilir | Demo |
| E08 Bağlantı işlemi | Mevcut/yeni bağlantı karşılaştırma | Gerekçe, atomik taşıma, çakışma mesajı, yeni doğrulama | Demo |
| E09 Geçmiş | Kim/ne zaman/neden | Önce/sonra, filtre, silinmeyen asıl kayıt ve ek düzeltme | Demo |
| E10 Arızalar | İş listesi ve bildirim | Cihaz pasaportuyla ortak kayıt; mevcut açık sorun uyarısı | Demo |
| E11 Müdahale | Arızayı sonuçlandırma | Atama yetkisi, günlük, doğrulanmış çözüm ve yeniden açma | Demo |
| E12 Rapor merkezi | Kapsama göre çıktı | Liste/CSV/yazdırma aynı sonuç kümesi ve filtreleri temsil eder | Tam sürüm |
| E13 Kullanıcılar | Hesap/rol yönetimi | Son aktif sorumlu korunur; açık işler yeniden atanır | Demo temel / tam sürüm ayrıntı |
| E14 Toplu aktarım | Cihaz envanteri başlatma | Önizleme ve onay; hatalar satır bazında; tekrar mükerrer yaratmaz | Tam sürüm |
| E15 OT genel görünümü | Kontrol ve aksiyon listesi | Açık/gecikmiş/tarih bekliyor/değerlendirilmedi ayrımı | Tam sürüm |
| E16 Cihaz kontrolü | Sürümlü değerlendirme | Taslak, açıklamalar, uygulanamaz onayı, tamamlanan kaydın korunması | Tam sürüm |
| E17 Bulgu ve aksiyon | Eksikliği doğrulanmış kapanışa götürme | Atama/tarih geçmişi, kanıt, farklı doğrulayıcı kuralı | Tam sürüm |

## Değişmez iş kuralları

- K01: Varlık kodu ve kablo etiketi tekil; port numarası switch içinde tekil.
- K02: Arayüz, kablo ve port aynı anda yalnızca bir aktif doğrudan bağlantıya katılır.
- K03: Arızalı/devre dışı porta yeni bağlantı kurulamaz. Mevcut bağlantı görünür kalır.
- K04: Port/kablo değişikliği gerekçelidir. Eski bitiş, yeni başlangıç ve geçmiş birlikte kaydedilir.
- K05: Eski ekran verisiyle ikinci değişiklik engellenir; güncel durum kullanıcıya gösterilir.
- K06: Doğrulama bağlantı kaydına aittir. Yeni bağlantı eski doğrulamayı devralmaz.
- K07: Aktif bağlı cihaz, kablo veya arayüz önce bağlantısı düzenlenmeden arşivlenemez.
- K08: Arıza çözümü açıklama ve kontrol sonucu gerektirir. Yeniden açma gerekçelidir.
- K09: Bilinmeyen kontrol uygun değildir. Cihaz kritikliği bir standart güvenlik seviyesi değildir.
- K10: OT bulgusu yalnızca aksiyon tamamlandı bildirimiyle kapanmaz; doğrulama gerekir.

Ek kaynak kuralları: konum döngüsü engellenir; son aktif sorumlu pasifleştirilemez; geçmiş kayıtlar sessizce değiştirilemez; şablon değişikliği eski değerlendirmeyi değiştirmez; yüksek öncelikli bulguda aynı kişi uygulama ve doğrulama yapamaz.

## Durumların anlamı

| Kayıt | Durumlar | Kullanıcıya anlatılan anlam |
| --- | --- | --- |
| Cihaz | Kullanımda / Kullanım dışı | Envanter kararı; çevrimiçi olma bilgisi değildir |
| Bağlantı | Aktif / Sonlandırılmış | Kayıtlı eşleşmenin geçerlilik aralığı |
| Doğrulama | Bekliyor / Doğrulandı / Uyuşmazlık var | Bağlantının saha kontrol sonucu |
| Port doluluğu | Boş / Kullanımda | Aktif bağlantıdan hesaplanır |
| Port uygunluğu | Uygun / Devre dışı / Arızalı | Yetkili kişinin gerekçeli kaydı |
| Arıza | Açık / İnceleniyor / Beklemede / Çözüldü / İptal | Müdahale sürecinin durumu |
| OT bulgusu | Açık / İşlemde / Doğrulama bekliyor / Kapalı / İptal | Aksiyon ve doğrulama süreci |
| Kontrol sonucu | Uygun / Uygun Değil / Bilinmiyor / Uygulanamaz | Maddeye ait gözlem; güvenlik puanı değildir |

Önerilen geçişler: atanmış açık arıza incelemeye alınır; inceleme beklemeye veya doğrulanmış çözüme gider; beklemeden incelemeye dönülür; çözülmüş kayıt gerekçeyle açılır. İptal gerekçelidir. OT aksiyonu tamamlanınca doğrulama bekler; reddedilen doğrulama gerekçeyle işlemde durumuna döner. Kapalı OT bulgusunun yeniden açılma politikası ayrıca kararlaştırılmalıdır.

## Rapor ve ölçüm tanımları

- Açık arıza: Açık + İnceleniyor + Beklemede. Çözüldü ve İptal hariç.
- Port doluluğu: aktif bağlantısı olan port / tanımlı fiziksel port. Arızalı/devre dışı ayrıca gösterilir. Sıfır portta oran “Hesaplanamadı” olur.
- Doğrulama bekleyen: aktif bağlantının kendisine ait tamamlanmış güncel doğrulama bulunmaması. Uyuşmazlık ayrı gösterilir.
- Çözüm süresi: açılıştan son çözüme geçen takvim süresi. Yeniden açılanlar işaretlenir; üretim duruşu değildir.
- Açık OT bulgusu: Açık + İşlemde + Doğrulama bekliyor.
- Gecikmiş OT aksiyonu: hedef tarihi geçmiş aktif bulgu. Hedef tarihi olmayan “Tarih bekliyor” grubundadır.
- Kontrol bekleyen kritik cihaz: Yüksek kritiklikte ve seçilen kontrol döneminde tamamlanmış değerlendirmesi olmayan cihaz.
- Kontrol sonuçları dört ayrı toplamdır; onaysız uygulanamaz sonuç ayrıca görünür. Uyum yüzdesi hesaplanmaz.

## Kullanılabilirlik ve pilot ölçümleri

Telefon pasaportunda bağlantı özeti, arıza açma ve doğrulama ilk erişilebilir işlemler olacaktır. Durumlar metin ve simgeyle desteklenir. Form hataları girilmiş veriyi kaybettirmez. Klavye odağı, yükleme/boş/hata durumları ve filtreye geri dönüş bütün ekranlarda ele alınır.

Önerilen pilot ölçümleri: makine bağlantısını bulma görevinde geçen süre ve doğru tamamlama oranı; doğrulanmış aktif bağlantı oranı; tekrar açılan arızalar; geciken bulgular; CSV hata oranı. Önce başlangıç ölçümü yapılır, ardından hedef belirlenir. Şimdiden tasarruf veya başarı yüzdesi vaat edilmez.
