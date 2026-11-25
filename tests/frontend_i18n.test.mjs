// Dil testleri: kalıcılık varsayılanları, statik çeviri ve kullanıcı verisinin korunması denetlenir.
import test from 'node:test';
import assert from 'node:assert/strict';
// Tarayıcı depolaması kontrollü taklit edilir; her modül örneği başlangıç tercihini ayrı okur.
let storedLanguage = 'en';
globalThis.localStorage = { getItem: () => storedLanguage };
const english = await import('../frontend/js/i18n.js?test=en');
storedLanguage = 'tr';
const turkish = await import('../frontend/js/i18n.js?test=tr');

test('language defaults to Turkish and uses a saved English preference', () => {
  assert.equal(turkish.language, 'tr');
  assert.equal(english.language, 'en');
  assert.equal(turkish.t('Cihaz envanteri'), 'Cihaz envanteri');
  assert.equal(english.t('Cihaz envanteri'), 'Device inventory');
  assert.equal(english.locale(), 'en-GB');
  assert.equal(turkish.locale(), 'tr-TR');
});
// Türkçe kullanıcı metni İngilizce şablona eklense de değişmemeli ve HTML kaçışı korunmalıdır.
test('template interpolation preserves user data and HTML-safe values', () => {
  const name = 'Açık · Üretim Hattı &lt;CNC&gt;';
  assert.equal(english.msg`<h2>Güvenlik bulguları</h2><p>${name}</p>`, `<h2>Security findings</h2><p>${name}</p>`);
  assert.equal(english.msg`${0} kayıt`, '0 records');
  assert.equal(english.msg`<button aria-label="${name} kaydını aç">Kaydet</button>`, `<button aria-label="${name} open record">Save</button>`);
});
// FR adları ve değişken kimlik içeren backend hataları doğru çevrilmelidir.
test('security terminology and interpolated API errors are localized', () => {
  assert.equal(english.t('SL-A · Mevcut'), 'SL-A · Current');
  assert.equal(english.t('Kaynak kullanılabilirliği'), 'Resource availability');
  assert.equal(english.t('Bu hedef ve FR için açık aksiyon var: OT-001. Mevcut kaydı kullanın.'), 'An open action already exists for this target and FR: OT-001. Use the existing record.');
  assert.equal(english.t('Value error, Zone veya conduit seçin.'), 'Value error, Select a zone or conduit.');
});
test('language switch exposes an accessible state', () => {
  assert.match(english.languageToggle(), /aria-pressed="true"/);
  assert.match(turkish.languageToggle(), /aria-pressed="false"/);
  assert.match(english.languageToggle(), /Switch to Turkish/);
});
// Gizlilik ayarı gibi nedenlerle depolama okunamazsa uygulama güvenli varsayılanla açılmalıdır.
test('unavailable storage falls back to Turkish', async () => {
  globalThis.localStorage = {getItem: () => {throw new Error('storage unavailable');}};
  const fallback = await import('../frontend/js/i18n.js?test=fallback');
  assert.equal(fallback.language, 'tr');
});
