// Ortak arayüz yardımcıları: güvenli metin, biçimlendirme, tablo, form ve bildirimler.
import { t as tr, msg, locale } from './i18n.js?v=i18n-1';
// API’nin sabit durum/rol kodlarını seçilen dilde görünen adlarla eşleştirir; kayıt kodları değişmez.
export const labels = {
  open: tr('Açık'), investigating: tr('İnceleniyor'), waiting: tr('Beklemede'), resolved: tr('Çözüldü'), cancelled: tr('İptal'),
  verified: tr('Doğrulandı'), pending: tr('Doğrulama bekliyor'), mismatch: tr('Uyuşmazlık var'),
  low: tr('Düşük'), medium: tr('Orta'), high: tr('Yüksek'), suitable: tr('Uygun'), faulty: tr('Arızalı'), disabled: tr('Devre dışı'),
  create: tr('Yeni bağlantı'), move: tr('Port taşıma'), replace_cable: tr('Kablo değişimi'), terminate: tr('Sonlandırma'),
  machine: tr('Makine'), switch: 'Switch', facility: tr('Tesis'), area: tr('Bölge'), line: tr('Hat'), station: tr('İstasyon'),
  manager: tr('IT/OT sorumlusu'), technician: tr('Saha teknisyeni'),
};
// Dinamik metindeki HTML özel karakterlerini kaçırır; kullanıcı verisinin HTML olarak çalışmasını önler.
export const e = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Kayıt zamanını seçilen dilin biçimiyle ve İstanbul saat diliminde gösterir.
export const date = value => value ? new Intl.DateTimeFormat(locale(), { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Europe/Istanbul' }).format(new Date(value)) : tr('Henüz kaydedilmedi');
// Durum kodunun görünen adını rozet olarak üretir; CSS sınıfı görsel durumu taşır.
export const badge = value => `<span class="badge ${e(value)}">${e(labels[value] || value)}</span>`;
// Boş liste açıklamasını güvenli metin olarak gösterir; eksik kayıtları uydurma sonuçlarla doldurmaz.
export const empty = text => `<div class="empty">${e(text)}</div>`;
// Ekranın başlığını, açıklamasını ve isteğe bağlı ana aksiyonunu ortak yapıda oluşturur.
export const heading = (title, text, action = '') => msg`<header class="page-heading"><div><p class="eyebrow">ÇALIŞMA ALANI</p><h1>${e(title)}</h1><p>${e(text)}</p></div>${action}</header>`;
// Görünen düğme adını işlem anahtarından ayırır; data-action ortak olay yönlendiricisi tarafından okunur.
export const button = (text, action, attrs = '') => `<button class="button primary" data-action="${action}" ${attrs}>${e(text)}</button>`;
// Seçenek değerlerini ve etiketlerini ayrı tutar; dil değişimi API’ye gönderilen değeri değiştirmez.
export const select = (name, title, options, value = '', attrs = '') => `<label>${e(title)}<select name="${name}" ${attrs}>${options.map(([v,t]) => `<option value="${e(v)}" ${String(v)===String(value)?'selected':''}>${e(t)}</option>`).join('')}</select></label>`;
// Alan adı ve mevcut değeriyle ortak giriş bileşeni üretir; dinamik değerler HTML’den kaçırılır.
export const input = (name, title, value = '', attrs = '') => `<label>${e(title)}<input name="${name}" value="${e(value)}" ${attrs}></label>`;
// Uzun açıklama alanını ortak genişlikte üretir; kullanıcı içeriğini güvenli metin olarak korur.
export const textarea = (name, title, value = '', attrs = '') => `<label class="full">${e(title)}<textarea name="${name}" rows="3" ${attrs}>${e(value)}</textarea></label>`;
// Kısa işlem sonucunu canlı bildirim alanında gösterir; önceki kapanma zamanlayıcısını temizler.
export function toast(text) {
  const el = document.querySelector('#toast'); el.textContent = text; el.classList.add('visible');
  clearTimeout(el.hideTimer); el.hideTimer = setTimeout(() => el.classList.remove('visible'), 5000);
}
// Başlıkları erişilebilir sütun başlıklarıyla sarar; satır içeriği çağıran ekran tarafından hazırlanır.
export function table(headers, body) {
  return `<div class="table-wrap"><table><thead><tr>${headers.map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div>`;
}
// Ortak form penceresini kurar; değişiklik uyarısı, alan hataları ve çift gönderimi önleyen düğme durumu burada yönetilir.
export function modal(title, content, onSubmit) {
  const dialog = document.querySelector('#modal');
  let dirty=false;
  dialog.innerHTML = msg`<form id="modal-form"><div class="modal-heading"><h2 id="modal-title">${e(title)}</h2><button type="button" class="icon-button" data-close aria-label="Pencereyi kapat">×</button></div><div class="form-grid">${content}</div><p class="form-error" role="alert"></p><footer><button type="button" class="button" data-close>Vazgeç</button><button class="button primary" type="submit">Kaydet</button></footer></form>`;
  // Kullanıcı formu değiştirmişse kapatmadan önce onay istenir; yanlışlıkla veri kaybı azaltılır.
  const mayClose=()=>!dirty||window.confirm(tr('Kaydedilmemiş değişiklikler var. Vazgeçmek istiyor musunuz?'));
  dialog.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>{if(mayClose())dialog.close();}));
  dialog.oncancel=event=>{if(!mayClose())event.preventDefault();};
  dialog.addEventListener('input',()=>{dirty=true;},{once:true});
  // Açık ve değiştirilmiş form varken sayfadan ayrılmada tarayıcının yerel kayıp uyarısı kullanılır.
  const unload=event=>{if(dialog.open&&dirty){event.preventDefault();event.returnValue='';}};
  window.addEventListener('beforeunload',unload);
  dialog.addEventListener('close',()=>window.removeEventListener('beforeunload',unload),{once:true});
  const handler = async event => {
    event.preventDefault(); const submit=dialog.querySelector('[type="submit"]');
    const error=dialog.querySelector('.form-error'); error.textContent='';
    dialog.querySelectorAll('[aria-invalid]').forEach(el=>el.removeAttribute('aria-invalid'));
    // Gönderim sürerken ikinci kaydı engeller; sunucu hatasında form açık ve düzenlenebilir kalır.
    submit.disabled=true; submit.textContent=tr('Kaydediliyor…');
    try { await onSubmit(Object.fromEntries(new FormData(event.target))); dialog.close(); }
    catch (err) {
      error.textContent=err.message;
      // Sunucunun alan yolları form elemanlarıyla eşleştirilir; hatalı alanlar aria-invalid ile işaretlenir.
      Object.entries(err.fields || {}).forEach(([name,message])=>{
        const field=event.target.elements.namedItem(name);
        if(field) { field.setAttribute('aria-invalid','true'); error.textContent+=` ${field.closest('label')?.firstChild?.textContent || name}: ${message}`; }
      });
    } finally { submit.disabled=false; submit.textContent=tr('Kaydet'); }
  };
  dialog.querySelector('form').addEventListener('submit',handler);
  dialog.showModal();
  return dialog;
}
