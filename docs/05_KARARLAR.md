# PortAtlas karar ve açık konu kaydı

Tarih: 31 Ekim 2026. Kullanıcı kararları ile PM önerileri ayrı durumlarla tutulur. Bir önerinin bu belgede bulunması onaylandığı anlamına gelmez.

## Kesinleşmiş kullanıcı kararları

| ID | Karar | Durum |
| --- | --- | --- |
| D01 | Backend Python | Kesin |
| D02 | Frontend vanilla JavaScript | Kesin |
| D03 | Veritabanı SQLite | Kesin |
| D04 | Tasarım kütüphaneleri kullanılmadan önce kullanıcı onayı | Kesin |
| D05 | İlk hedef ders demosu, ardından gerçek saha pilotu | Kesin |
| D06 | İki kişilik ekip, olabildiğince hızlı geliştirme | Kesin; tarih belirtilmedi |

## PM çalışma kararları ve öneriler

| ID | Konu | Öneri veya mevcut yaklaşım | Durum |
| --- | --- | --- | --- |
| D07 | Gereksinim kaynağı | Güncel web DOCX/PDF esas, eski masaüstü teknoloji referansları tarihsel | Çalışma kararı |
| D08 | İlk teslim | T2 bağlantı + arıza demosu; tam 17 ekran T3 | Plan önerisi |
| D09 | Python framework | FastAPI, aynı origin API ve statik frontend | Uygulandı |
| D10 | Veri erişimi | sqlite3, parametreli sorgular, sürümlü SQL migrations | Uygulandı |
| D11 | Tasarım tabanı | Özel CSS, CSS Grid/Flexbox, sistem fontları ve yerel SVG | Öneri; üçüncü taraf tasarım paketi gerektirmez |
| D12 | Grafikler | Gerektiğinde Chart.js 4.6.1; yerel UMD ve MIT lisansı eklendi | Kullanıcı onayladı, uygulandı |
| D13 | İlk aktarım | UTF-8 CSV, cihaz envanteriyle sınırlı | Öneri; XLSX ayrıca karar |
| D14 | Rapor çıktısı | CSV ve print CSS / tarayıcıdan PDF kaydı | Öneri; sunucu PDF ayrıca karar |
| D15 | Bulgu oluşturma | Kullanıcı oluşturur veya mevcut bulguya bağlar | Ana belgeye dayalı çalışma kararı |
| D16 | AI asistanı | İlk sürüm dışı, V2 keşif adayı | Ana belgeye dayalı çalışma kararı |
| D17 | OT kapsamını genişletme | Kullanıcının yeni isteğiyle zone ve conduit oluşturma, sistem kapsamı ve SL profilleri eklendi | Kullanıcı yönlendirmesiyle uygulandı |
| D18 | SL-A / SL-T ayrımı | SL-A mevcut değerlendirilen seviye, SL-T hedef; FR1–FR7 için ayrı vektör ve dayanak | Kullanıcı yönlendirmesiyle uygulandı |
| D19 | Seviye onayı | Manuel değerlendirme, gerekçe, referans, yeni revizyon ve güncellik kontrolü; otomatik uygunluk sonucu yok | Uygulandı; ürün iş kuralı |
| D20 | İlk zone üyelik modeli | Cihaz başına tek bir birincil zone; fiziksel konumdan bağımsız. Arayüz bazlı çoklu üyelik sonraki genişletme | Çalışma kararı, uygulandı |

## Tasarım önerisi ve kütüphane onayı

Ürün dili: açık zemin, lacivert gezinme, turkuaz ana işlem, okunabilir port numaraları, sınırlı durum renkleri. Sunumdaki neon/dekoratif görseller ürün arayüzüne olduğu gibi taşınmaz. Ana ekranlar yoğun veride okunabilirliği ve saha işlemlerini önceler. Mobil pasaport ilk geliştirmeden itibaren ele alınır.

İlk tasarım örneği E05 pasaport ve E06 port paneli üzerinden hazırlanmalıdır. Özel CSS için Bootstrap/Tailwind veya hazır yönetim paneli paketi önerilmiyor. Böylece vanilla JS yapısı ve kaynak tasarım dili doğrudan korunabilir.

31 Ekim 2026 tarihinde kullanıcı tarafından onaylanan tasarım paketi:

| Paket | Nerede ve neden | Alternatif | Durum |
| --- | --- | --- | --- |
| [Chart.js](https://www.chartjs.org/docs/latest/) | E12/E15 içinde arıza eğilimi, port dağılımı ve kontrol sonucu grafikleri | HTML tablo ve basit CSS çubukları | Onaylandı; 4.6.1 sürümü yerel dosya ve lisansıyla eklendi |

Grafik yanında aynı sayılara erişilebilen metin/tablo bulunacaktır. Onaylanan sabit sürüm yerel dosya olarak sunulur, lisans bilgisi korunur. Pilot kullanımının CDN erişimine bağımlı olmaması önerilir. Daha sonra ikon, tablo veya başka tasarım kütüphanesi gerekirse amacı ve alternatifiyle ayrıca onaya sunulur.

## Açık kararlar

| ID | Soru | Geçici yaklaşım | Gerekli aşama |
| --- | --- | --- | --- |
| Q01 | Kesin ders teslim tarihi ve günlük geliştirme kapasitesi? | Kişi-gün aralıklarıyla planlama; ilk iki günde revizyon | Takvim bağlamadan önce |
| Q02 | Dersin resmi teknoloji ve değerlendirme koşulları? | Kaynakların kapsamı esas; resmi rubrik doğrulanmış sayılmaz | Tam ders kabulünden önce |
| Q03 | İki kişinin backend/frontend sorumluluk tercihi? | A backend/veri, B arayüz; ortak entegrasyon | T0 başlangıcı |
| Q04 | Chart.js kullanımına onay var mı? | Çözüldü: Kullanıcı onayladı; grafikler uygulandı | 31 Ekim 2026 |
| Q05 | Gerçek işletmenin cihaz, switch, port ve eşzamanlı kullanıcı sayısı? | Kapasite garantisi verilmez | Pilot yük testinden önce |
| Q06 | Pilot sunucusu ve istemci işletim sistemleri, ağ ve HTTPS düzeni? | Tek sunucu, yerel kalıcı SQLite; tarayıcı erişimi | Pilot kurulumundan önce |
| Q07 | IP tekilliği hangi ağ kapsamında? MAC mükerrerliği nasıl ele alınacak? | IP/MAC isteğe bağlı; zorunlu küresel IP tekilliği henüz yok | Arayüz kayıt kuralı kesinleşmeden |
| Q08 | Etiket standardı ve konum kodları? | CNC-014, SW-HAT2-01, KBL-0087 örnekleri yalnızca demo | Gerçek aktarım öncesi |
| Q09 | Teknisyenin başkasına atanan arızaya müdahale ve iptal yetkisi? | Çözme/yeniden açma yalnızca atandığı kayıtlar; belirsiz işlemler backend sözleşmesinde kesinleştirilir | PA-010 öncesi |
| Q10 | Kontrol sıklığı ve gecikmenin takvim tanımı? | Kullanıcının seçtiği dönem; zorunlu periyot uydurulmaz | Planlı kontroller/pilot raporu öncesi |
| Q11 | Dosya türü/boyutu, saklama süresi ve kanıt erişimi? | Fotoğraf/PDF önerisi, yerel korumalı depolama | PA-019 öncesi |
| Q12 | Kapalı OT bulgusu tekrar açılabilir mi, yoksa yeni bulgu mu oluşur? | Geçmiş korunur; yeniden açma otomatik eklenmez | PA-014 durum sözleşmesi öncesi |
| Q13 | CSV yeterli mi; XLSX veya sunucudan üretilmiş PDF gerekli mi? | CSV + yazdırma önerisi | PA-016–017 öncesi |
| Q14 | Pilot doğrulama ve kabulünün işletmedeki sorumlusu kim? | İsim atanmadı; yüksek öncelik için farklı yetkili doğrulayıcı gerekli | Pilot öncesi |
| Q15 | Yedekleme sıklığı, saklama ve geri dönüş hedefi? | Geri yükleme provası zorunlu pilot kabulü; süreler henüz belirlenmedi | PA-021 öncesi |

Bu soruların tümü ilk geliştirme öncesinde kullanıcıya topluca yöneltilecek engeller değildir. İlgili iş yaklaşırken, eldeki proje bilgileriyle çözülemeyen kararlar sorulur.

## Değişiklik ve durum kayıt yöntemi

Yeni talep için sorun, beklenen kullanıcı yararı, etkilenen ekran/veri, efor, ertelenecek iş ve karar yazılır. Kapsam sessizce genişletilmez. Kabul edilen değişiklik ürün gereksinimleri, iş listesi ve kabul senaryolarına birlikte işlenir.

İlerleme bildirimleri tamamlanan kullanıcı akışı, gözlenen kanıt, kalan risk ve sıradaki teslimi açıklar. Henüz geliştirilmemiş özellik, gerçekleştirilmiş test veya gerçek işletme kazanımı olarak raporlanmaz.
