# PortAtlas arayüz sistemi

31 Ekim 2026. Ürün içi operasyon arayüzü. Kaynak projenin lacivert/turkuaz/açık zemin dili esas alınır. UI/UX Pro Max ilk aramasındaki pazarlama, canlı veri ve harici font önerileri bu ürünün bağlamına uyarlanmıştır.

- Stack: HTML, özel CSS, vanilla JavaScript ES modules. Tek onaylı görselleştirme paketi Chart.js 4.6.1.
- Renkler: gezinme #102c37, ana işlem #087c7b, zemin #f4f7f8, metin #203b46. Tokenlar frontend/css/tokens.css içinde.
- Tipografi: yerel sistem sans; cihaz kodları için sistem monospace. Harici font isteği yok.
- Düzen: sabit sol menü, üst arama, başlık/işlem, ana içerik. Mobilde açılır menü.
- Port paneli: gerçek fiziksel port sayısı, numara, metin etiketi ve seçili durum. Doluluk ve uygunluk ayrı gösterilir.
- Etkileşim: en az 44 px temel düğmeler, görünür odak, semantik form etiketleri, yerel dialog.
- Hareket: kısa hover/geri bildirim, prefers-reduced-motion desteği.
- Veri: yalnızca API/SQLite sonuçları. Canlı ağ veya güvenlik garantisi iddiası yok.
- Grafikler: karşılık gelen sayılar metinde/tablolarda da erişilir.
- Duyarlılık: 375, 768, 1024, 1440 px; sayfa taşması yok, geniş tablolar kendi içinde kaydırılır.
