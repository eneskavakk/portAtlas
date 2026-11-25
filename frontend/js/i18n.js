// Türkçe/İngilizce dil seçimi ve kullanıcı verisini değiştirmeyen statik metin çevirisi.
import { en } from './translations.js?v=i18n-1';
// Dil tercihini diğer tarayıcı verilerinden ayıran uygulamaya özgü depolama anahtarıdır.
const storageKey = 'portatlas.language';
// Tarayıcı tercihinden desteklenen dili seçer; depolama okunamazsa Türkçe varsayılır.
function readLanguage() {
  try { return localStorage.getItem(storageKey) === 'en' ? 'en' : 'tr'; }
  catch { return 'tr'; }
}
// Dil başlangıçta okunur; değişimde sayfa yenilendiği için bütün modüller aynı dilde başlar.
export const language = readLanguage();
// Tarih gösteriminde kullanılacak yerel biçimi desteklenen dil koduyla eşleştirir.
export const locale = () => language === 'en' ? 'en-GB' : 'tr-TR';
const escapePattern = value => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const wordCharacter = /[\p{L}\p{N}_]/u;
const patterns = Object.keys(en).sort((a,b) => b.length-a.length).map(escapePattern);
// Uzun çeviri anahtarları önce eşleşir; kısa bir kelimenin uzun cümle çevirisini bölmesi azaltılır.
const textPattern = new RegExp(patterns.join('|'), 'gu');
// Yalnızca arayüze ait sabit metinleri çevirir; kullanıcı adları, gözlemler ve kanıt içerikleri bu işleve verilmemelidir.
export function t(text) {
  if (language !== 'en' || typeof text !== 'string') return text;
  if (Object.hasOwn(en, text)) return en[text];
  return text.replace(textPattern, (match, offset) => {
    // Kelime sınırı kontrolü, kısa anahtarların başka bir kelimenin içini yanlışlıkla çevirmesini önler.
    if (wordCharacter.test(match[0]) && offset > 0 && wordCharacter.test(text[offset - 1])) return match;
    const end = offset + match.length;
    if (wordCharacter.test(match.at(-1)) && end < text.length && wordCharacter.test(text[end])) return match;
    return en[match];
  });
}
// Şablonun sabit parçalarını çevirir; araya eklenen veri değerlerini aynen koruyarak kullanıcı kayıtlarının değişmesini önler.
export function msg(strings, ...values) {
  return strings.reduce((out, part, i) => out + t(part) + (i < values.length ? String(values[i]) : ''), '');
}
// Seçili dili ve erişilebilir basılı durumunu içeren TR/EN düğmesini oluşturur.
export function languageToggle() {
  return `<button type="button" class="language-toggle" data-language-toggle aria-label="${language === 'en' ? 'Switch to Turkish' : 'İngilizceye geç'}" aria-pressed="${language === 'en'}" title="${language === 'en' ? 'Language: English' : 'Dil: Türkçe'}"><span lang="tr" class="${language === 'tr' ? 'selected' : ''}">TR</span><span lang="en" class="${language === 'en' ? 'selected' : ''}">EN</span></button>`;
}
// Belge dilini ve sayfa metaverisini ayarlar; dil değişince tercihi saklayıp aynı adresi yeniden yükler.
export function initializeLanguage() {
  document.documentElement.lang = language;
  document.querySelector('.skip-link').textContent = t('İçeriğe geç');
  document.querySelector('meta[name="description"]').content = t('PortAtlas endüstriyel bağlantı ve müdahale yönetimi');
  document.title = t('PortAtlas · Bağlantı ve Müdahale Yönetimi');
  document.addEventListener('click', event => {
    if (!event.target.closest('[data-language-toggle]')) return;
    // Tercih tarayıcıya kaydedilir; adres ve sunucu çerezi korunarak bütün modüller tek dilde yeniden başlar.
    try { localStorage.setItem(storageKey, language === 'tr' ? 'en' : 'tr'); }
    catch { return; }
    window.location.reload();
  });
}
