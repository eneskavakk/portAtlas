# PortAtlas kaynak incelemesi

İnceleme tarihi: 31 Ekim 2026. Amaç, mevcut materyallerdeki ortak ürün kapsamını ve uygulama öncesinde çözülmesi gereken farklılıkları belirlemektir.

## İncelenen materyaller

| Kod | Kaynak | İnceleme ve ürün açısından yeri |
| --- | --- | --- |
| S1 | `PortAtlas_Proje_ve_Arayuz_Dokumani.docx` | 24 bölümün tamamı okundu. 29 Eylül 2026 tarihli web kapsamı; 5 modül, 17 ekran, 2 rol, K01–K10, 16 temel ve 8 OT kabul senaryosu. Ana gereksinim kaynağı. |
| S2 | `PortAtlas_Proje_ve_Arayuz_Dokumani.pdf` | 25 sayfanın metni çıkarıldı ve DOCX paragraflarıyla karşılaştırıldı. Uzun DOCX paragraflarının tamamı PDF metninde eşleşti. Pasaport, port paneli ve OT görünümü görsel olarak ayrıca incelendi. Aynı belgenin PDF sunumu. |
| S3 | `Fabrika Ağ Yönetimi Proje Sunumu.pdf` | 4 sayfanın tamamı okundu. Önceki NetTrack fikri, SQLite, SCD Type 2 bağlantı geçmişi ve ilk iş kuralları. Tarihsel destek kaynağı. |
| S4 | `PortAtlas_Industrial_Command_Center (2).pptx` | 15 slaydın tamamı görsel olarak okundu. Slaytlar görsel tabanlı; metin çıkarımı içerik okumak için yeterli değil. Ürün anlatımı ve sunum referansı. |
| S5 | `PortAtlas_ Dijital Bağlantı Pasaportu.png` | Görselin tamamı incelendi. Dört modüllü eski masaüstü yaklaşımı, C# ve Windows Forms içeriyor. Renk ve kavram referansı; teknoloji kararı değil. |
| S6 | `AI Arıza Asistanı_ kaynaklı teknik destek.png` | Görselin tamamı incelendi. Teknik doküman yönetimi, yerel LLM, RAG ve kaynak sayfasına dayanan yanıt fikri. PortAtlas ilk sürümüne dahil edilmeyen ayrı ürün/ileriki entegrasyon adayı. |

Dosya adlarında işletim sisteminin Unicode gösterimi nedeniyle karakter kodlaması farklı görünebilir. Kaynak dosyalar değiştirilmedi.

## Kaynak önceliği

Kullanıcının güncel kararları teknoloji ve teslim hedefinde esastır: Python, vanilla JavaScript, SQLite, iki kişi, hızlı ders demosu ve ardından saha pilotu. İşlevsel ayrıntılarda S1/S2 esas alınır. S3–S5 ortak fikri destekler, çelişen eski davranışları otomatik olarak kapsam haline getirmez. S6 yeni bir modül talebi sayılmaz.

Bu sıralama PM çalışma kararıdır. Açık ürün kararları `05_KARARLAR.md` içinde takip edilir.

## Kaynak farklılıkları ve önerilen çözüm

| Konu | Kaynak farkı | Uygulama için çalışma kararı |
| --- | --- | --- |
| Ürün adı | S3 NetTrack, diğer ana kaynaklar PortAtlas | PortAtlas kullanılacak. |
| Platform | S5 masaüstü, S1/S2 web | Tarayıcı tabanlı Python + vanilla JS. |
| Modül sayısı | S5 dört, S1/S2 ve S4 beş | OT güvenlik dahil beş modül; ilk demo bütün modülleri bitirme iddiası taşımaz. |
| Bulgu oluşturma | S4 slayt 12 otomatik bulgu, S1 bölüm 20 öneri ve mevcut bulguya bağlama | Kullanıcı açıkça bulgu açar veya mevcut bulguya bağlar. Otomatik mükerrer kayıt oluşturulmaz. |
| Aktarım formatı | S4 slayt 14 Excel şablonu, S3 CSV, S1 formatı kesinleştirmiyor | İlk sürüm için UTF-8 CSV önerilir. XLSX desteği ayrı kapsam kararıdır. |
| IP/MAC tekilliği | S3 küresel aktif IP/MAC tekilliği ister; S1 bölüm 11 IP bilgisini isteğe bağlı tutar | Boş değer kabul edilir. MAC normalize edilir. IP tekilliğinin ağ kapsamı pilot öncesi belirlenir; farklı ağlarda aynı IP ihtimali nedeniyle küresel yasak sessizce uygulanmaz. |
| Port değiştirme yetkisi | S3 teknisyen işlemlerini atanan arızayla sınırlar; S1 iki role de bağlantı değişikliği verir | S1 matrisi esas: teknisyen bağlantı kurabilir/değiştirebilir. Arıza çözme ve yeniden açma yalnızca atandığı kayıtlarda. |
| Port numaraları | S4 slayt 8'in temsili ızgarasında bazı numaralar eksik | Gerçek portlar cihaz tanımından üretilecek; görseldeki eksik numaralar kopyalanmayacak. |
| Canlı bağlantı ifadesi | S4 slayt 7 bir açıklamada “canlı fiziksel bağlantı yolu” der; S1 kayıtlı bilgiyi esas alır | Arayüzde “Kayıtlı bağlantı” yazılacak. |
| MTTR ve duruş | S3 MTTR/üretim kaybı söylemi kullanır; S1 bölüm 15 açılış–çözüm takvim süresini tanımlar | İlk rapor “Çözüm için geçen süre” gösterecek. Ölçülmeyen üretim duruşu ve maliyet tasarrufu hesaplanmayacak. |
| OT örnek kaydının sahibi | S1 bölüm 24 CNC-014 bağlamında switch Port 12 kontrolünü anlatır; S4 slayt 13 OT-007'yi switch'e bağlar | Demo bulgusu SW-HAT2-01 / Port 12 üzerinde tutulacak; CNC-014 ilişkili cihaz bağlamı olarak gösterilebilir. |
| AI asistanı | S6 ayrı teknoloji ve veri modeli öneriyor; S1 ilk sürüm dışında tutuyor | Sonraki sürüm araştırması. Laravel, MySQL ve ChromaDB bu projeye taşınmayacak. |

## Geliştirme öncesi bulunan boşluklar

Kaynaklar kullanıcı akışını iyi açıklıyor; aşağıdaki ayrıntılar henüz uygulama tasarımına dönüşmemiş:

- API sözleşmesi, kalıcı veri şeması, şema geçişleri ve bağlantı işlem sınırları.
- Eşzamanlı değişiklikte sürüm kontrolü ve sonucu belirsiz isteğin güvenli tekrarı.
- Arıza durum geçişlerinde rol, atama, gerekçe ve kapanış doğrulaması ayrıntıları.
- OT şablon sürümü, uygulanamaz onayı ve yüksek öncelikte farklı doğrulayıcı kontrolü.
- İlk sorumlu hesabının kurulması, parola yenileme, oturum iptali ve son sorumlunun korunması.
- Yedekleme/geri yükleme, ek dosyaların saklanması, kurulum ortamı ve veri saklama süresi.
- CSV sütunları, dosya limitleri, önizleme ile kesin kayıt arasında yeniden doğrulama.
- Dersin resmi değerlendirme ölçütleri, kesin teslim tarihi ve saha kabulünün sahibi.

Saha ihtiyacı, zaman kazancı ve kullanılabilirlik henüz gerçek kullanıcı görüşmeleriyle doğrulanmış bulgu sayılmaz. Demo verileri temsili olarak işaretlenmelidir.
