# OT güvenlik sprinti

Tarih: 31 Ekim 2026. Sürüm: 0.2.0. Kullanıcının zone oluşturma, SL-T ve SL-A isteğiyle ilk kapsam genişletildi. Yeni yapı, envanterin güvenlik bağlamını zone/conduit seviyesinde tutar ve kontrol bulgularını aksiyonlara bağlar.

## Kesinleşen ürün kararı

Kullanıcı yönlendirmesi: SL-A şimdiki, SL-T hedef seviye olacak. Arayüzde SL-A “Mevcut değerlendirilen seviye”, SL-T “Hedef güvenlik seviyesi” olarak gösterilir. Mevcut durum kaydı, değerlendirmeye ve kanıta dayanır; uygulama seviye veya sertifikasyon sonucunu kendi başına doğrulamaz.

Ana proje belgesindeki yalnızca isteğe bağlı zone etiketi ve SL hesaplamama sınırı bu sprintte genişletildi: artık sistem, zone, conduit ve manuel seviye değerlendirmeleri kayıt altındadır. Otomatik riskten SL üretimi, canlı ağ taraması, firewall uygulaması ve standart uygunluğu kararı kapsam dışında kalır.

## Uygulanan akış

1. Sorumlu, sistem kapsamını (SUC), sınırlarını ve sorumlusunu tanımlar.
2. Aynı güvenlik ihtiyacını paylaşan varlıklar için zone oluşturur. Zone fiziksel konumdan türetilmez.
3. Cihazları zone içine atar. İlk modelde bir cihazın tek bir birincil zone üyeliği vardır; birden fazla arayüzün farklı zone'larda olması ayrı model genişletmesi gerektirir.
4. Aynı sistemdeki iki farklı zone arasında conduit oluşturur. Yön, protokol/port bilgisi, iletişim amacı ve koruma önlemleri kaydedilir. Bu, gerçek ağ bağlantısı veya uygulanmış kural iddiası değildir.
5. Zone ve conduit için SL-A ve SL-T ayrı değerlendirmeler olarak kaydedilir. Her biri FR1–FR7 sırasında yedi değer içerir.
6. Değerlendirmeler taslak veya sorumlu onaylıdır. Onay için yedi değer ile gerekçe ve kanıt/risk referansı gerekir. Yeni kayıt eski kaydı güncellemek yerine yeni revizyon oluşturur.
7. İki güncel, onaylı profil arasında her FR için `max(0, SL-T - SL-A)` farkı gösterilir. Bu yalnızca ordinal seviye farkıdır; risk puanı, ilerleme yüzdesi veya uygunluk sonucu değildir. Profil yoksa, taslaksa veya bağlamı değişmişse fark hesaplanmaz.
8. Fark olan FR üzerinden ilgili SL-T revizyonuna bağlı bulgu açılır. Aynı hedef revizyonu/FR için açık bulgu varsa mevcut aksiyon kullanılır.
9. Cihazlar için kritiklik belirlenir ve PortAtlas-OT-v1 kontrolü yapılır. Uygun, Uygun Değil, Bilinmiyor ve Uygulanamaz ayrı sonuçlardır. Tamamlanan kontrol dondurulur; yeniden kontrol yeni kayıt açar.
10. Uygulanamaz gerekçeleri ayrıca sorumlu onayı bekler. Uygun olmayan/bilinmeyen maddeler kullanıcı seçimiyle bulguya dönüşür; mevcut açık bulgu önerilir.
11. Sorumlu bulgunun önceliğini, aksiyon sahibini ve hedef tarihini gerekçeyle belirler. Teknisyen uygulamayı kaydeder ve kanıt referansıyla doğrulamaya gönderir.
12. Sorumlu doğrular veya gerekçeyle işleme döndürür. Yüksek öncelikte uygulayan kişi doğrulayamaz. Kapanan bulgu sorumlu tarafından gerekçeyle yeniden açılabilir. İptal kayıtları korunur.

## SL-A ve SL-T değerlendirme kuralları

| Alan | SL-A | SL-T |
| --- | --- | --- |
| Anlam | Kayıtlı mevcut/elde edilen seviye değerlendirmesi | Risk değerlendirmesinden doğan hedef |
| Kapsam | Zone veya conduit | Zone veya conduit |
| Dayanak | Mevcut durum incelemesi ve kanıt referansı | Risk değerlendirmesi, karar veya gereksinim referansı |
| Değerler | Her FR için 0–4 veya taslakta belirlenmedi | Her FR için 0–4 veya taslakta belirlenmedi |
| Yetki | IT/OT sorumlusu | IT/OT sorumlusu |
| Otomasyon | Kontrol sayısından türetilmez | Cihaz kritikliği veya komşu zone'dan türetilmez |

“Belirlenmedi” null olarak saklanır. Sayısal 0 ayrı bir değerdir. Vektör ortalaması, en düşük değerden tek bir genel SL veya standart uyum yüzdesi üretilmez. SL-C ürün kapasitesi bu sprintte tutulmaz ve SL-A yerine kullanılmaz.

Temel gereksinim sırası: FR1 kimlik tanımlama/doğrulama, FR2 kullanım kontrolü, FR3 sistem bütünlüğü, FR4 veri gizliliği, FR5 kısıtlı veri akışı, FR6 olaylara zamanında yanıt, FR7 kaynak kullanılabilirliği.

Zone üyeliği, cihaz veya kritiklik kaydı, ilgili aktif bağlantı veya port uygunluğu değişirse profil bağlamı kontrol edilir. Eski seviyeler silinmez; “Gözden geçirme gerekli” olur. Conduit değerlendirmesi uç zone bağlamına da bağlıdır. Kontrol listesinde bağlantı değişimi yalnızca OT02/OT06, zone/kritiklik değişimi OT05 için yeniden değerlendirme ihtiyacı doğurur. Diğer sonuçlar korunur.

## Yeni ekranlar ve servisler

Menüde OT Güvenlik alanı eklendi. Genel görünüm, sistem/zone envanteri, zone ayrıntısı, conduit envanteri/ayrıntısı, cihaz güvenlik kaydı, kontrol listesi/ayrıntısı, bulgu listesi/ayrıntısı ve OT geçmişi bulunur. Makine pasaportundan cihaz güvenlik kaydına geçilir.

API uçları `/api/ot` altında; temel varlıklar `systems`, `zones`, `conduits`, `levels`, `devices`, `assessments`, `findings` ve `history`dir. Yeni SQLite tabloları `002_ot_security.sql`, hedefe bağlı bulgu alanları `003_finding_target_links.sql` ile eklenir. Eski cihaz ve bağlantı verileri sıfırlanmaz.

## Demo ve doğrulama

`python -m scripts.manage ot-demo`, yalnızca `demo=true` olan ve henüz OT sistemleri bulunmayan veritabanına temsili bir SUC, üç zone ve bir conduit ekler. SL-A/SL-T seviyesi, saha kanıtı veya tamamlanmış kontrol oluşturmaz. Mevcut OT kayıtlarının üzerine yazmaz. Bu çalışma klasörünün temsili veritabanına örnek zone/conduit verisi eklenmiştir.

Test kapsamı: zone üyeliğinin konumdan bağımsızlığı ve tekilliği; farklı sistem/aynı zone conduit engeli; bağımsız SL-A/SL-T ve FR farkları; yedi değer ve dayanak zorunluluğu; null/0 ayrımı; seviye revizyonları ve eski sürüm çakışması; üyelik/port değişiminde güncellik; kontrol eksikliği, bilinmiyor ve uygulanamaz onayı; tamamlanmış kontrolün değiştirilememesi; port taşımasında seçili kontrol maddelerinin eskimesi; mükerrer ve yanlış kapsam bulgusu; kanıt zorunluluğu, yüksek öncelikte farklı doğrulayıcı; tarih geçmişi; kritikliği SL'den ayırma; eski veritabanının korunarak yükseltilmesi.

Ek olarak gerçek API cevaplarıyla 12 OT görünümünün JavaScript HTML üretimi ve rol bazındaki seviye düğmeleri Node üzerinden doğrulanır. Bu bir tarayıcı görsel/etkileşim kabulü değildir; bu sprintte yeni ekranların tarayıcı kabulü yapılmamıştır. Önceki sprintteki 20 çekirdek test korunur. Son test sonucu geliştirme durumu belgesine yazılır.

## Sıradaki ürün önerileri

| Öncelik | Öneri | Kazanım |
| --- | --- | --- |
| 1 | Yapılandırılmış risk kayıtları: senaryo, etkilenen süreç, etki, mevcut önlem, risk sahibi, değerlendirme tarihi ve kabul kararı | SL-T dayanağını metin referansından izlenebilir risk kararına taşır; SL otomatik hesaplanmaz |
| 2 | Gereksinim ve kanıt matrisi: FR altında işletmenin onayladığı gereksinimler, kanıt ekleri, doğrulama tarihi ve telafi edici önlemler | SL-A kararının kanıtlarını denetlenebilir biçimde toplar; lisanslı standart maddeleri birebir kopyalanmaz |
| 3 | Zone/conduit için planlı gözden geçirme ve kurumun belirlediği kontrol dönemleri | Eski kanıt ve hedef kararlarının takip edilmesini sağlar |
| 4 | Arayüz düzeyinde zone üyeliği ve belgelenmiş akış envanteri | Çok arayüzlü varlıklar ve sınır cihazlarını daha doğru temsil eder |

Bu sprintin kontrolleri sabit ve sürümlü PortAtlas-OT-v1 listesidir. Şablon düzenleme, uygulanamaz kararını reddederek revizyona döndürme, dosya kanıtı yükleme, scope arşivleme ve detaylı risk matrisi ayrı işlerdir. Hatalı uygulanamaz kararı için şimdilik yeni değerlendirme açılır; eski kayıt korunur.

## Kavramsal kaynaklar

- [IEC 62443-3-2 resmi kapsamı](https://webstore.iec.ch/en/publication/30727): SUC, zone/conduit risk değerlendirmesi ve SL-T hedeflerinin kapsamı.
- [ISA 62443-3-3 resmi önizlemesi](https://www.isa.org/getmedia/d73509e9-b626-4709-a406-be6fc7616b79/ISA-62443-3-3_Preview.pdf): hedeflere göre gereksinim belirlemenin işletmenin risk değerlendirmesi ve politikalarıyla ilişkisi.
- [Cisco IEC 62443 açıklaması](https://www.cisco.com/c/en/us/td/docs/solutions/Verticals/IoT_Security_Lab/IEC62443_WP.html): yedi FR için vektör yaklaşımı ile SL-A, SL-T ve SL-C ayrımı.

Bu kaynaklar ürün kavramlarını destekler. Tam standart metni üzerinden madde bazında uygunluk değerlendirmesi yapılmamıştır. Onay akışı, veri modeli ve arayüz kontrolleri PortAtlas ürün kararlarıdır.
