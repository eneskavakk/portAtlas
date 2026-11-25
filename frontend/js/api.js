// Frontend ile Python API arasındaki ortak JSON ve oturum/hata iletişim katmanı.
import { t as tr, msg } from './i18n.js?v=i18n-1';
export let session = null;
// Geçerli kullanıcı bilgisini modül içinde tutar; hassas oturum çerezi JavaScript tarafından okunmaz.
export function setSession(value) { session = value; }

// JSON isteklerini oturum çerezi ve CSRF başlığıyla gönderir; ağ, yanıt ve alan hatalarını ortak biçimde iletir.
export async function api(path, { method = 'GET', body } = {}) {
  let response;
  try {
    // Çerez oturumu aynı kaynağa gönderilir; yazma isteklerinin CSRF başlığı mevcut oturum bilgisinden alınır.
    response = await fetch(`/api${path}`, {
      method, credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', ...(session ? { 'X-CSRF-Token': session.csrf_token } : {}) },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  } catch {
    throw new Error(tr('Sunucuya ulaşılamadı. İşlem yapılmış olabilir; tekrar kaydetmeden önce güncel kaydı kontrol edin.'));
  }
  let data;
  try { data = await response.json(); }
  // JSON olmayan sunucu yanıtı teknik ayrıntı yerine anlaşılır genel hataya dönüştürülür.
  catch { throw new Error(tr('Sunucu işlemi tamamlayamadı. Kaydı kontrol edip yeniden deneyin.')); }
  if (!response.ok) {
    // Süresi bitmiş oturum bütün ekranlar için ortak olay üretir; backend hata mesajı seçilen dilde gösterilir.
    if (response.status === 401 && session) window.dispatchEvent(new CustomEvent('session-expired'));
    const error = new Error(tr(data.message) || tr('İşlem tamamlanamadı.'));
    error.fields = Object.fromEntries(Object.entries(data.field_errors || {}).map(([key, value]) => [key, tr(value)]));
    error.status = response.status;
    throw error;
  }
  return data;
}
