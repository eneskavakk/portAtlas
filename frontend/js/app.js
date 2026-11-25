// Ana arayüz: oturum, hash tabanlı yönlendirme, ekran üretimi ve ortak işlem olayları.
import { t as tr, msg, locale, languageToggle, initializeLanguage } from './i18n.js?v=i18n-1';
import { configureOt, renderOt, otActions } from './ot.js?v=i18n-1';
import { api, session, setSession } from './api.js?v=i18n-1';
import { e, labels, date, badge, empty, heading, button, select, input, textarea, toast, table, modal } from './ui.js?v=i18n-1';

initializeLanguage();
// Ana arayüzün bağlandığı kök eleman; ekranlar bu kapsayıcı altında oluşturulur.
const root=document.querySelector('#app');
// Grafik örnekleri ve render sayacı tutulur; eski grafikler temizlenir, gecikmiş yanıtların yeni ekranı ezmesi engellenir.
let charts=[], renderId=0, currentData={}, selectedPort=null;
// Görünür işlem düğmelerini role göre seçer; gerçek erişim iznini backend denetler.
const isManager=()=>session?.role==='manager';
// Hash adresinin ekran bölümünü okur; sorgu parametreleri ekran anahtarından ayrı tutulur.
const route=()=>location.hash.slice(1).split('?')[0] || 'dashboard';
// Liste filtrelerini URL sorgu bölümünden okur; filtreli görünümün paylaşılmasını sağlar.
const params=()=>new URLSearchParams(location.hash.split('?')[1] || '');
// Aynı adrese yönlendirmede de ekranı yeniler; farklı adreste hashchange akışı çalışır.
const go=path=>{ if(location.hash===`#${path}`) render(); else location.hash=path; };
// API listesinden seçim kutularının beklediği değer/etiket çiftlerini üretir.
const options=(data,value,label)=>data.map(r=>[r[value],r[label]]);
// Cihaz kodunu güvenli metin olarak ayrıntı bağlantısına yerleştirir.
const linkDevice=(id,code)=>`<a class="record-link mono" href="#device/${id}">${e(code)}</a>`;
// Sayısal arıza kimliğini gösterim için ARZ-001 biçimine dönüştürür; veritabanı kimliği değişmez.
const incidentCode=id=>`ARZ-${String(id).padStart(3,'0')}`;
// Kayıt sayısını seçili dilde kısa liste özeti olarak gösterir.
const countText=n=>msg`${n} kayıt`;
// Menü anahtarı, görünen ad ve sıra numarasını tek listede tutar.
const navItems=[['dashboard',tr('Genel bakış'),'01'],['devices',tr('Cihazlar'),'02'],['switches',tr('Switch ve portlar'),'03'],['inventory',tr('Kablo ve arayüzler'),'04'],['connections',tr('Bağlantılar'),'05'],['history',tr('Değişiklik geçmişi'),'06'],['incidents',tr('Arızalar'),'07'],['ot',tr('OT güvenlik'),'08'],['reports',tr('Raporlar'),'09'],['locations',tr('Konumlar'),'10'],['users',tr('Kullanıcılar'),'11']];

// Oturum açmış kullanıcının menüsünü ve üst çubuğunu kurar; rol bazlı görünürlük sunucudaki yetki kontrolünün yerini tutmaz.
function shell() {
  root.innerHTML=msg`<div class="app-shell"><aside class="sidebar" id="sidebar"><a class="brand" href="#dashboard"><img class="brand-logo" src="/static/assets/portatlas-logo.png" width="192" height="128" alt="PortAtlas"><small>BAĞLANTI YÖNETİMİ</small></a><div class="workspace-label">OPERASYON</div><nav aria-label="Ana menü">${navItems.filter(([key])=>key!=='users'||isManager()).map(([key,title,num])=>`<a href="#${key}" data-nav="${key}"><span class="nav-number">${num}</span>${title}</a>`).join('')}</nav><div class="sidebar-note"><span class="small-label">KAYIT TEMELLİ YÖNETİM</span><p>Her bağlantının<br>bir hafızası var.</p><small>Canlı ağ taraması yapılmaz.</small></div><div class="profile"><span class="avatar">${e(session.name.split(' ').map(s=>s[0]).slice(0,2).join(''))}</span><div><strong>${e(session.name)}</strong><small>${e(labels[session.role])}</small></div><button class="logout" data-action="logout" aria-label="Oturumu kapat" title="Oturumu kapat">↗</button></div></aside><div class="workspace"><header class="topbar"><button class="icon-button mobile-menu" data-action="menu" aria-label="Menüyü aç veya kapat" aria-controls="sidebar" aria-expanded="false">☰</button><form id="global-search" role="search"><label class="search-label"><span aria-hidden="true">⌕</span><input name="q" aria-label="Makine, switch veya kablo ara" placeholder="Makine, switch veya kablo ara…" autocomplete="off"></label><kbd>ARA ↵</kbd></form><div class="topbar-meta">${languageToggle()}<span class="demo-tag" id="demo-tag">${session.demo?tr('TEMSİLİ DEMO'):tr('ÇALIŞMA ALANI')}</span><span class="today">${new Intl.DateTimeFormat(locale(),{day:'numeric',month:'long',timeZone:'Europe/Istanbul'}).format(new Date())}</span></div></header><main id="main" tabindex="-1"></main><footer class="app-footer"><span>PortAtlas · Endüstriyel bağlantı ve müdahale yönetimi</span><span>Kayıtlı bilgi. İzlenebilir değişiklik.</span></footer></div></div>`;
  document.querySelector('#global-search').addEventListener('submit',event=>{event.preventDefault();go(`devices?q=${encodeURIComponent(new FormData(event.target).get('q'))}`);});
}

// Giriş ekranını oluşturur; başarılı API yanıtıyla oturumu kurar, başarısızlıkta form üzerinde hata gösterir.
function login(message='') {
  charts.forEach(c=>c.destroy()); charts=[];
  root.innerHTML=msg`<main class="login-layout"><section class="login-story"><header class="login-brand-row"><a class="brand" href="#"><img class="brand-logo" src="/static/assets/portatlas-logo.png" width="240" height="160" alt="PortAtlas"></a>${languageToggle()}</header><div><p class="eyebrow">ENDÜSTRİYEL BAĞLANTI YÖNETİMİ</p><h1>Bağlantıyı bulun.<br>Değişikliği izleyin.</h1><p>Makineden switch portuna uzanan bağlantı hafızası. Saha ekibiniz için tek bir çalışma alanı.</p><div class="connection-illustration" aria-hidden="true"><span>CNC-014</span><i></i><span>KBL-0087</span><i></i><span>PORT 05</span></div></div><small>Envanter · Bağlantılar · Müdahaleler</small></section><section class="login-form-area"><form id="login-form"><span class="eyebrow">EKİP ERİŞİMİ</span><h2>Çalışma alanına giriş</h2><p>Size tanımlanan kullanıcı hesabıyla devam edin.</p>${input('username',tr('Kullanıcı adı'),'', 'required autocomplete="username"')}${input('password',tr('Parola'),'', 'type="password" required autocomplete="current-password"')}<label class="checkbox-label"><input type="checkbox" id="show-password">Parolayı göster</label><p class="form-error" role="alert">${e(message)}</p><button type="submit" class="button primary">Oturum aç <span aria-hidden="true">→</span></button><small class="login-help">Hesap erişimi için IT/OT sorumlunuza başvurun.</small></form></section></main>`;
  document.querySelector('#show-password').addEventListener('change',event=>{document.querySelector('[name=password]').type=event.target.checked?'text':'password';});
  document.querySelector('#login-form').addEventListener('submit',async event=>{
    event.preventDefault(); const b=event.target.querySelector('[type=submit]'); b.disabled=true;
    try {const data=await api('/auth/login',{method:'POST',body:Object.fromEntries(new FormData(event.target))});setSession(data);setSession(await api('/auth/me'));shell();await render();}
    catch(err){event.target.querySelector('.form-error').textContent=err.message;}
    finally {b.disabled=false;}
  });
}

// Arıza satırlarını kayıt değerlerini HTML kaçışından geçirerek oluşturur; bağlantılar ayrıntı ekranına gider.
function incidentRows(list) {
  return list.map(n=>`<tr><td><a class="record-link mono" href="#incident/${n.id}">${incidentCode(n.id)}</a><small>${date(n.created_at)}</small></td><td><a class="record-link" href="#incident/${n.id}">${e(n.title)}</a><small>${e(n.asset_code)} · ${e(n.location_name)}</small></td><td>${badge(n.priority)}</td><td>${badge(n.status)}</td><td>${e(n.assignee_name || tr('Atama bekliyor'))}</td></tr>`).join('');
}
// Eski ve yeni bağlantı uçlarını yan yana gösterir; geçmiş kayıtları değiştirmeden okunur biçime getirir.
function historyRows(list) {
  return list.map(c=>`<tr><td>${date(c.created_at)}<small>${e(c.actor_name)}</small></td><td>${linkDevice(c.device_id,c.asset_code)}</td><td>${badge(c.kind)}</td><td><span class="mono">${e(c.old_switch || '—')}${c.old_port?' / '+String(c.old_port).padStart(2,'0'):''}</span><small>${e(c.old_cable || tr('Önceki bağlantı yok'))}</small></td><td><span class="mono">${e(c.new_switch || '—')}${c.new_port?' / '+String(c.new_port).padStart(2,'0'):''}</span><small>${e(c.new_cable || tr('Bağlantı sonlandırıldı'))}</small></td><td>${e(c.reason)}</td></tr>`).join('');
}
// Bağlantı envanterini cihaz, arayüz, kablo, port ve saha doğrulamasıyla tablo satırlarına dönüştürür.
function connectionRows(list) {
  return list.map(c=>`<tr><td>${linkDevice(c.device_id,c.asset_code)}<small>${e(c.interface_name)}</small></td><td class="mono">${e(c.cable_label)}</td><td><a class="record-link mono" href="#switch/${c.switch_id}">${e(c.switch_code)} / ${String(c.port_number).padStart(2,'0')}</a></td><td>${badge(c.verification)}<small>${c.verified_at?date(c.verified_at):tr('Saha kontrolü gerekli')}</small></td><td>${button(tr('İşlem'),'change',`data-interface="${c.interface_id}"`)}</td></tr>`).join('');
}

// Kayıtlı sayılarla Chart.js grafiği kurar; azaltılmış hareket tercihinde animasyonu kapatır.
function chart(id,type,labels,data,colors) {
  if(!window.Chart) return;
  const canvas=document.getElementById(id); if(!canvas)return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  charts.push(new Chart(canvas,{type,data:{labels,datasets:[{label:tr('Kayıt sayısı'),data,backgroundColor:colors,borderColor:type==='line'?'#087c7b':colors,borderWidth:type==='line'?2:0,borderRadius:type==='bar'?4:0,tension:0.25,fill:false,pointRadius:4}]},options:{responsive:true,maintainAspectRatio:false,animation:reduced?false:{duration:350},cutout:'78%',plugins:{legend:{display:false}},...(type==='doughnut'?{}:{scales:{y:{beginAtZero:true,ticks:{precision:0},grid:{color:'#edf1f3'}},x:{grid:{display:false}}}})}}));
}

// URL hash değerine göre ekran verisini API’den alır, içeriği yerleştirir ve ekrana özgü olayları/grafikleri başlatır.
async function render() {
  if(!session)return;
  // Her yüklemeye kimlik verilir; kullanıcı ekran değiştirirse eski isteğin sonucu yeni görünümü ezmemelidir.
  const id=++renderId; charts.forEach(c=>c.destroy());charts=[];
  const key=route();
  document.querySelector('.sidebar')?.classList.remove('open');
  document.querySelector('.mobile-menu')?.setAttribute('aria-expanded','false');
  document.querySelectorAll('[data-nav]').forEach(el=>{const active=key.startsWith(el.dataset.nav)|| (el.dataset.nav==='devices'&&key.startsWith('device/'))||(el.dataset.nav==='switches'&&key.startsWith('switch/'))||(el.dataset.nav==='incidents'&&key.startsWith('incident/'));el.classList.toggle('active',active);if(active)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
  const main=document.querySelector('#main'); main.innerHTML=tr('<div class="page-loading" role="status">Kayıtlar yükleniyor…</div>');
  try {
    let html=''; let after=()=>{};
    if(key==='ot'||key.startsWith('ot/')) {
    // OT genel görünüm: kapsam, ayrı SL profilleri ve açık aksiyonların özeti.
    
      const otView=await renderOt(key);html=otView.html;after=otView.after;
    } else if(key==='dashboard') {
    // Genel görünüm: envanter ve arıza sayaçları, son işlemler ve kayıt bazlı grafikler.
    
      const d=await api('/dashboard');currentData=d;
      const o=d.occupancy;
      html=msg`${heading(tr('Genel bakış'),tr('Bağlantılarınız, açık işleriniz ve son saha kayıtları.'),button(tr('+ Arıza aç'),'new-incident'))}<div class="context-strip"><span><span class="status-dot"></span>Tüm tesisler</span><span>Son görüntüleme: ${date(new Date().toISOString())}</span></div><section class="metrics" aria-label="Genel göstergeler"><a href="#devices?device_type=machine&active=true" class="metric"><span>Kullanımdaki makineler</span><strong>${d.devices.machine||0}<small>MAKİNE</small></strong><p>Envanterde kayıtlı varlıklar</p></a><a href="#switches" class="metric"><span>Kayıtlı switch'ler</span><strong>${d.devices.switch||0}<small>SWITCH</small></strong><p>${o.total} tanımlı fiziksel port</p></a><a href="#incidents?status=active" class="metric attention"><span>Açık arızalar</span><strong>${d.open_incidents}<small>AÇIK İŞ</small></strong><p>${d.my_incidents} iş size atanmış</p></a><a href="#connections?verification=pending" class="metric"><span>Doğrulama bekleyen</span><strong>${d.pending}<small>BAĞLANTI</small></strong><p>${d.mismatches?msg`${d.mismatches} bağlantıda uyuşmazlık`:tr('Saha kontrolü bekleyen kayıtlar')}</p></a></section><div class="dashboard-grid"><section class="panel"><div class="panel-heading"><div><p class="eyebrow">MÜDAHALE TAKİBİ</p><h2>Son arıza kayıtları</h2></div><a href="#incidents" class="text-link">Tümünü gör ↗</a></div>${d.incidents.length?table([tr('Kayıt'),tr('Arıza / Cihaz'),tr('Öncelik'),tr('Durum'),tr('Sorumlu')],incidentRows(d.incidents)):empty(tr('Henüz arıza kaydı bulunmuyor.'))}</section><section class="panel occupancy-panel"><div class="panel-heading"><div><p class="eyebrow">FİZİKSEL KATMAN</p><h2>Port kullanımı</h2></div><span class="muted">${o.total} port</span></div><div class="donut-wrap"><canvas id="occupancy" role="img" aria-label="Portların kayıtlı doluluk dağılımı"></canvas><div class="donut-center"><strong>${o.total?Math.round(o.used/o.total*100):'—'}<small>%</small></strong><span>KAYITLI DOLULUK</span></div></div><dl class="chart-legend"><div><dt><i class="used"></i>Kullanımda</dt><dd>${o.used}</dd></div><div><dt><i class="free"></i>Boş</dt><dd>${o.free}</dd></div></dl><p class="panel-note">${o.faulty} arızalı · ${o.disabled} devre dışı port<br>Doluluk, cihazın çevrimiçi olduğunu göstermez.</p></section><section class="panel changes-panel"><div class="panel-heading"><div><p class="eyebrow">BAĞLANTI HAFIZASI</p><h2>Son değişiklikler</h2></div><a href="#history" class="text-link">Geçmişi aç ↗</a></div>${d.changes.length?`<div class="activity-list">${d.changes.map(c=>`<div class="activity"><span class="activity-icon">↳</span><div><strong>${linkDevice(c.device_id,c.asset_code)} <span>${e(labels[c.kind])}</span></strong><p>${e(c.reason)}</p><small>${date(c.created_at)} · ${e(c.actor_name)}</small></div><span class="mono activity-port">${c.new_port?'Port '+String(c.new_port).padStart(2,'0'):tr('Sonlandırıldı')}</span></div>`).join('')}</div>`:empty(tr('Bağlantı değişikliği bulunmuyor.'))}</section><section class="panel"><div class="panel-heading"><div><p class="eyebrow">İŞ DAĞILIMI</p><h2>Arıza öncelikleri</h2></div></div><div class="bar-chart"><canvas id="priorities" role="img" aria-label="Son arızaların öncelik dağılımı"></canvas></div><div class="chart-counts">${['high','medium','low'].map(p=>`<span>${labels[p]}: <strong>${d.incidents.filter(n=>n.priority===p).length}</strong></span>`).join('')}</div><p class="panel-note">Son ${d.incidents.length} kaydın dağılımı. Tüm kayıtlar için raporları açın.</p></section></div><div class="info-line"><span>i</span>Bu görünüm kayıtlı envanter ve saha işlemlerinden hazırlanır. Canlı ağ durumu izlenmez.</div>`;
      after=()=>{chart('occupancy','doughnut',[tr('Kullanımda'),tr('Boş')],[o.used,o.free],['#087c7b','#e7eff0']);const counts=['high','medium','low'].map(p=>d.incidents.filter(n=>n.priority===p).length);chart('priorities','bar',[tr('Yüksek'),tr('Orta'),tr('Düşük')],counts,['#ba684b','#d4ab69','#5c8d89']);};
    } else if(key==='devices'||key==='switches') {
    // Cihaz/switch listesi: URL filtreleriyle arama ve dijital pasaporta erişim.
    
      const type=key==='switches'?'switch':params().get('device_type')||'';
      const [devices,locations]=await Promise.all([api(`/devices?q=${encodeURIComponent(params().get('q')||'')}&device_type=${type}&active=${params().get('active')||'all'}`),api('/locations')]);currentData={devices,locations};
      html=heading(key==='switches'?tr('Switch ve portlar'):tr('Cihaz envanteri'),key==='switches'?tr('Switch üzerinden kayıtlı portlara ve bağlı makinelere erişin.'):tr('Makine ve switch kayıtlarını bulun, bağlantı pasaportlarını açın.'),isManager()?button(tr('+ Cihaz ekle'),'new-device'):'');
      html+=msg`<section class="panel"><form class="filter-bar" id="device-filter">${input('q',tr('Cihaz ara'),params().get('q')||'',tr('placeholder="Varlık kodu, ad veya konum"'))}${select('device_type',tr('Cihaz türü'),[['',tr('Tüm türler')],['machine',tr('Makine')],['switch','Switch']],type)}${select('active',tr('Kullanım durumu'),[['all',tr('Tümü')],['true',tr('Kullanımda')],['false',tr('Kullanım dışı')]],params().get('active')||'all')}<button class="button" type="submit">Filtrele</button></form><div class="list-meta">${countText(devices.length)}</div>${devices.length?table([tr('Varlık'),tr('Cihaz adı'),tr('Tür'),tr('Konum'),tr('Kullanım'),''],devices.map(d=>msg`<tr><td><a class="record-link mono" href="#${d.device_type==='switch'?'switch':'device'}/${d.id}">${e(d.asset_code)}</a></td><td>${e(d.name)}<small>${e([d.brand,d.model].filter(Boolean).join(' · '))}</small></td><td>${e(labels[d.device_type])}</td><td>${e(d.location_name)}</td><td>${badge(d.active?tr('Kullanımda'):tr('Kullanım dışı'))}</td><td><a class="row-open" aria-label="${e(d.asset_code)} kaydını aç" href="#${d.device_type==='switch'?'switch':'device'}/${d.id}">↗</a></td></tr>`).join('')):empty(tr('Bu filtrelerle eşleşen cihaz yok.'))}</section>`;
      after=()=>document.querySelector('#device-filter').addEventListener('submit',ev=>{ev.preventDefault();go(`devices?${new URLSearchParams(new FormData(ev.target))}`);});
    } else if(key.startsWith('device/')) {
    // Cihaz pasaportu: fiziksel bağlantılar, saha kontrolleri, arızalar ve OT kaydına geçiş.
    
      const id=Number(key.split('/')[1]);const d=await api(`/devices/${id}/passport`);currentData=d;
      const device=d.device;const loc=d.locations.find(l=>l.id===device.location_id);
      html=msg`<a class="back-link" href="#devices">← Cihaz envanteri</a>${heading(device.asset_code,device.name,isManager()?button(tr('Cihazı düzenle'),'edit-device'):'')}<div class="passport-meta"><span>${e(loc?.path)}</span>${badge(device.active?tr('Kullanımda'):tr('Kullanım dışı'))}</div><section class="panel passport-panel"><div class="panel-heading"><div><p class="eyebrow">DİJİTAL BAĞLANTI PASAPORTU</p><h2>Kayıtlı bağlantılar</h2></div>${button(tr('+ Bağlantı işlemi'),'change',`data-device="${id}"`)}</div>${d.interfaces.length?d.interfaces.map(i=>{const c=d.connections.find(c=>c.interface_id===i.id);return `<article class="connection-card"><div class="connection-title"><strong>${e(i.name)}</strong>${c?badge(c.verification):badge(tr('Bağlantı kaydı yok'))}</div>${c?msg`<div class="connection-path"><span><small>MAKİNE ARAYÜZÜ</small><strong>${e(device.asset_code)}</strong><span>${e(i.name)}</span></span><i>→</i><span><small>KABLO</small><strong>${e(c.cable_label)}</strong></span><i>→</i><a href="#switch/${c.switch_id}"><small>SWITCH / PORT</small><strong>${e(c.switch_code)}</strong><span>Port ${String(c.port_number).padStart(2,'0')}</span></a></div><div class="connection-bottom"><small>${c.verified_at?`${date(c.verified_at)} · ${e(c.verifier)}`:tr('Bu bağlantı henüz sahada doğrulanmadı.')}</small><div><button class="button" data-action="verify" data-id="${c.id}">Sahada doğrula</button><button class="button" data-action="change" data-interface="${i.id}">Bağlantıyı değiştir</button></div></div>`:msg`<p class="muted">Bu arayüz için aktif bağlantı kaydı yok.</p><button class="button" data-action="change" data-interface="${i.id}">Bağlantı oluştur</button>`}</article>`;}).join(''):empty(tr('Önce kablo ve arayüzler ekranından bir ağ arayüzü tanımlayın.'))}</section><div class="two-column"><section class="panel"><div class="panel-heading"><h2>Cihaz bilgileri</h2></div><dl class="detail-list"><div><dt>Marka / Model</dt><dd>${e(device.brand || tr('Bilgi girilmedi'))} / ${e(device.model || tr('Bilgi girilmedi'))}</dd></div>${d.interfaces.map(i=>msg`<div><dt>${e(i.name)} IP / MAC</dt><dd class="mono">${e(i.ip || tr('IP girilmedi'))}<small>${e(i.mac || tr('MAC girilmedi'))}</small></dd></div>`).join('')}<div><dt>Açıklama</dt><dd>${e(device.description||tr('Bilgi girilmedi'))}</dd></div></dl></section><section class="panel"><div class="panel-heading"><h2>Arızalar</h2>${button(tr('+ Arıza aç'),'new-incident',`data-device="${id}"`)}</div>${d.incidents.length?`<div class="activity-list">${d.incidents.map(n=>`<a class="incident-summary" href="#incident/${n.id}"><div><strong>${e(n.title)}</strong><small>${incidentCode(n.id)} · ${date(n.created_at)}</small></div>${badge(n.status)}</a>`).join('')}</div>`:empty(tr('Bu cihazda arıza kaydı yok.'))}</section></div><section class="panel"><div class="panel-heading"><h2>Bağlantı geçmişi</h2></div>${d.history.length?table([tr('Zaman / Kullanıcı'),tr('Cihaz'),tr('İşlem'),tr('Önce'),tr('Sonra'),tr('Gerekçe')],historyRows(d.history)):empty(tr('Henüz değişiklik kaydı yok.'))}</section>`;
      html+=msg`<section class="panel"><div class="panel-heading"><div><p class="eyebrow">OT GÜVENLİK BAĞLAMI</p><h2>Zone, kritiklik ve kontrol kayıtları</h2></div><a class="button" href="#ot/device/${id}">Güvenlik kaydını aç ↗</a></div><p class="panel-note">Cihazın zone üyeliğini, kontrol geçmişini ve açık güvenlik bulgularını inceleyin. SL-A ve SL-T zone/conduit kapsamında takip edilir.</p></section>`;
    } else if(key.startsWith('switch/')) {
    // Switch paneli: portların kayıtlı doluluğu, uygunluğu ve seçili uç ayrıntıları.
    
      const d=await api(`/switches/${Number(key.split('/')[1])}/ports`);currentData=d;
      if(!d.ports.some(p=>p.id===selectedPort))selectedPort=d.ports[0]?.id;
      html=msg`<a class="back-link" href="#switches">← Switch listesi</a>${heading(d.device.asset_code,d.device.name,isManager()?button(tr('Cihazı düzenle'),'edit-switch'):'')}<div class="switch-summary"><span>${d.ports.length} fiziksel port</span><span>${d.ports.filter(p=>p.connection).length} kayıtlı bağlantı</span>${badge(d.device.active?tr('Kullanımda'):tr('Kullanım dışı'))}</div><section class="panel"><div class="panel-heading"><div><p class="eyebrow">GÖRSEL SWITCH PANELİ</p><h2>Fiziksel portlar</h2></div><span class="muted">Ayrıntı için bir port seçin</span></div><div class="port-grid">${d.ports.map(p=>`<button class="port ${p.connection?'occupied':''} ${p.suitability} ${p.id===selectedPort?'selected':''}" data-action="select-port" data-id="${p.id}" aria-pressed="${p.id===selectedPort}" aria-label="Port ${p.number}, ${p.connection?tr('kullanımda'):tr('boş')}, ${labels[p.suitability]}"><span class="port-number">${String(p.number).padStart(2,'0')}</span><span class="port-socket" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></span><small>${p.suitability!=='suitable'?e(labels[p.suitability]):p.connection?tr('Kullanımda'):tr('Boş')}</small></button>`).join('')}</div><div class="port-legend"><span>Turkuaz: Kullanımda</span><span>Gri: Boş</span><span>Turuncu: Devre dışı</span><span>Kırmızı: Arızalı</span></div><div id="port-detail"></div></section><section class="panel"><div class="panel-heading"><h2>Doğrudan bağlı makineler</h2></div>${d.ports.some(p=>p.connection)?table([tr('Makine / Arayüz'),tr('Kablo'),'Switch / Port',tr('Doğrulama'),tr('İşlem')],connectionRows(d.ports.filter(p=>p.connection).map(p=>p.connection))):empty(tr('Bu switch için aktif bağlantı yok.'))}</section>`;
      after=portDetail;
    } else if(key==='connections') {
    // Aktif bağlantı envanteri: arayüz-kablo-port eşleşmelerinin görünümü.
    
      let list=await api('/connections');const filter=params().get('verification');if(filter)list=list.filter(c=>c.verification===filter);currentData={connections:list};
      html=heading(tr('Bağlantılar'),tr('Arayüz, kablo ve switch portunun güncel eşleşmeleri.'),button(tr('+ Bağlantı işlemi'),'change'))+msg`<div class="tabs"><a href="#connections" class="${!filter?'active':''}">Tümü</a><a href="#connections?verification=pending" class="${filter==='pending'?'active':''}">Doğrulama bekleyen</a><a href="#connections?verification=mismatch" class="${filter==='mismatch'?'active':''}">Uyuşmazlık var</a></div><section class="panel"><div class="panel-heading"><h2>Aktif bağlantı kayıtları</h2><span>${countText(list.length)}</span></div>${list.length?table([tr('Makine / Arayüz'),tr('Kablo'),'Switch / Port',tr('Doğrulama'),tr('İşlem')],connectionRows(list)):empty(tr('Bu görünümde bağlantı yok.'))}</section>`;
    } else if(key==='history') {
    // Bağlantı değişiklik günlüğü: eski/yeni uçlar ve değişiklik gerekçeleri.
    
      const list=await api('/changes');html=heading(tr('Değişiklik geçmişi'),tr('Kim değiştirdi, ne zaman ve neden? Önceki bağlantılar korunur.'))+`<section class="panel">${list.length?table([tr('Zaman / Kullanıcı'),tr('Cihaz'),tr('İşlem'),tr('Önce'),tr('Sonra'),tr('Gerekçe')],historyRows(list)):empty(tr('Henüz bağlantı işlemi yok.'))}</section>`;
    } else if(key==='inventory') {
    // Kablo ve arayüz envanteri: fiziksel bağlantı uçlarının kayıtları.
    
      const [cables,interfaces]=await Promise.all([api('/cables'),api('/interfaces')]);currentData={cables,interfaces};
      html=heading(tr('Kablo ve ağ arayüzleri'),tr('Bağlantı uçlarını tanımlayın, kullanım ilişkilerini inceleyin.'))+msg`<div class="two-column"><section class="panel"><div class="panel-heading"><h2>Kablolar <span class="muted">${cables.length}</span></h2>${isManager()?button(tr('+ Kablo'),'new-cable'):''}</div>${cables.length?table([tr('Etiket'),tr('Tür'),tr('Kullanım')],cables.map(k=>`<tr><td class="mono">${e(k.label)}</td><td>${e(k.cable_type)}</td><td>${badge(k.connection_id?tr('Kullanımda'):tr('Boş'))}</td></tr>`).join('')):empty(tr('Kablo kaydı yok.'))}</section><section class="panel"><div class="panel-heading"><h2>Ağ arayüzleri</h2>${isManager()?button(tr('+ Arayüz'),'new-interface'):''}</div>${interfaces.length?table([tr('Cihaz / Arayüz'),tr('IP / MAC'),tr('Bağlantı')],interfaces.map(i=>`<tr><td>${linkDevice(i.device_id,i.asset_code)}<small>${e(i.name)}</small></td><td class="mono">${e(i.ip || tr('Bilgi girilmedi'))}<small>${e(i.mac)}</small></td><td>${badge(i.connection_id?tr('Kullanımda'):tr('Boş'))}</td></tr>`).join('')):empty(tr('Arayüz kaydı yok.'))}</section></div>`;
    } else if(key==='incidents') {
    // Arıza listesi: durum ve atama filtreleriyle görev takibi.
    
      const all=await api('/incidents');let list=all;const status=params().get('status');if(status==='active')list=all.filter(n=>!['resolved','cancelled'].includes(n.status));if(status==='mine')list=all.filter(n=>n.assigned_to===session.id);
      html=heading(tr('Arıza ve müdahale'),tr('Açık işleri bulun, sorumluları ve saha müdahalelerini izleyin.'),button(tr('+ Arıza aç'),'new-incident'))+msg`<div class="tabs"><a href="#incidents" class="${!status?'active':''}">Tüm kayıtlar</a><a href="#incidents?status=active" class="${status==='active'?'active':''}">Açık işler</a><a href="#incidents?status=mine" class="${status==='mine'?'active':''}">Bana atananlar</a></div><section class="panel">${list.length?table([tr('Kayıt'),tr('Arıza / Cihaz'),tr('Öncelik'),tr('Durum'),tr('Sorumlu')],incidentRows(list)):empty(tr('Bu görünümde arıza yok.'))}</section>`;
    } else if(key.startsWith('incident/')) {
    // Arıza ayrıntısı: müdahale geçmişi, sorumlu ve izinli durum geçişleri.
    
      const [detail,users]=await Promise.all([api(`/incidents/${Number(key.split('/')[1])}`),api('/users')]);currentData={...detail,users};const n=detail.incident;
      const canWork=isManager()||n.assigned_to===session.id;const active=!['resolved','cancelled'].includes(n.status);
      const timeline=[...detail.events.map(a=>({...a,title:a.action==='create'?tr('Arıza açıldı'):a.action==='assign'?tr('Sorumlu atandı'):tr('Durum güncellendi'),text:a.reason})),...detail.interventions.map(a=>({...a,title:tr('Saha müdahalesi'),text:a.note}))].sort((a,b)=>a.created_at.localeCompare(b.created_at));
      const transitions={open:['investigating','cancelled'],investigating:['waiting','resolved','cancelled'],waiting:['investigating','cancelled'],resolved:['open'],cancelled:[]};
      html=msg`<a class="back-link" href="#incidents">← Arıza listesi</a>${heading(incidentCode(n.id),n.title)}<div class="passport-meta">${badge(n.status)}${badge(n.priority)}<span>${linkDevice(n.device_id,msg`Cihaz pasaportunu aç ↗`)}</span></div><div class="two-column incident-layout"><section class="panel"><div class="panel-heading"><h2>Müdahale günlüğü</h2></div><p class="description-text">${e(n.description)}</p><div class="timeline">${timeline.map(a=>`<article><span class="timeline-dot"></span><small>${date(a.created_at)} · ${e(a.actor_name)}</small><h3>${e(a.title)}</h3><p>${e(a.text)}</p></article>`).join('')}</div>${detail.changes.map(c=>`<div class="info-line">${e(labels[c.kind])}: ${e(c.old_switch||'')} / ${c.old_port||'—'} → ${e(c.new_switch||'')} / ${c.new_port||'—'}<br>${e(c.reason)}</div>`).join('')}${canWork&&active?`<div class="panel-actions">${button(tr('+ Müdahale ekle'),'intervene')}</div>`:''}</section><section class="panel"><div class="panel-heading"><h2>İş ayrıntıları</h2></div><dl class="detail-list"><div><dt>Sorumlu</dt><dd>${e(users.find(u=>u.id===n.assigned_to)?.name||tr('Atama bekliyor'))}</dd></div><div><dt>Açılış</dt><dd>${date(n.created_at)}</dd></div><div><dt>Son çözüm</dt><dd>${date(n.resolved_at)}</dd></div>${n.resolution?msg`<div><dt>Çözüm açıklaması</dt><dd>${e(n.resolution)}</dd></div>`:''}</dl><div class="stack-actions">${isManager()&&active?button(tr('Sorumlu ata'),'assign'):''}${canWork?transitions[n.status].filter(s=>s!=='cancelled'||isManager()).map(s=>button(s==='open'?tr('Yeniden aç'):s==='resolved'?tr('Çözümü kaydet'):labels[s], 'transition',`data-status="${s}"`)).join(''):''}</div><p class="panel-note">Arıza çözümü bağlantıları otomatik olarak doğrulamaz. Bağlantı kontrolünü ayrıca pasaporttan kaydedin.</p></section></div>`;
    } else if(key==='locations') {
    // Konum ağacı: tesis, bölge, hat ve istasyonların fiziksel hiyerarşisi.
    
      const locations=await api('/locations');html=heading(tr('Konum yönetimi'),tr('Tesis, bölge, hat ve istasyon hiyerarşisi.'),isManager()?button(tr('+ Konum ekle'),'new-location'):'')+`<section class="panel location-tree">${locations.map(l=>`<div class="location-row" style="--depth:${l.depth}"><span class="location-code mono">${e(l.code)}</span><strong>${e(l.name)}</strong>${badge(labels[l.kind])}<small>${e(l.path)}</small></div>`).join('')||empty(tr('İlk tesis konumunu ekleyin.'))}</section>`;
    } else if(key==='users') {
    // Kullanıcı yönetimi: yöneticiye açık hesap oluşturma ve rol görünümü.
    
      if(!isManager())throw new Error(tr('Bu ekran için IT/OT sorumlusu yetkisi gerekiyor.'));
      const users=await api('/users');html=heading(tr('Kullanıcılar'),tr('Hesapları ve çalışma alanı rollerini yönetin.'),button(tr('+ Hesap oluştur'),'new-user'))+msg`<section class="panel">${table([tr('Ad soyad'),tr('Kullanıcı adı'),tr('Rol'),tr('Hesap durumu')],users.map(u=>`<tr><td>${e(u.name)}</td><td class="mono">${e(u.username)}</td><td>${e(labels[u.role])}</td><td>${badge(u.active?tr('Aktif'):tr('Pasif'))}</td></tr>`).join(''))}</section><div class="info-line">Hesap pasifleştirme, görev devri ve parola yenileme tam ders sürümünde tamamlanacak.</div>`;
    } else if(key==='reports') {
    // Rapor ekranı: kayıtlı dağılımlar, CSV dışa aktarma ve yazdırma görünümü.
    
      const [connections,incidents]=await Promise.all([api('/connections'),api('/incidents')]);currentData={connections,incidents};const counts=['open','investigating','waiting','resolved','cancelled'].map(s=>incidents.filter(n=>n.status===s).length);
      html=heading(tr('Raporlar'),tr('Güncel bağlantı envanteri ve kayıtlı arıza dağılımı.'),msg`<div class="heading-actions">${button(tr('CSV indir'),'export')}<button class="button" data-action="print">Yazdır / PDF</button></div>`)+msg`<div class="report-context">Bağlantı envanteri · Kapsam: Tüm tesisler · ${countText(connections.length)} · ${date(new Date().toISOString())}</div><section class="panel"><div class="panel-heading"><h2>Arızaların durum dağılımı</h2></div><div class="report-chart"><canvas id="incident-chart" role="img" aria-label="Arıza durumları dağılımı"></canvas></div><div class="report-counts">${['open','investigating','waiting','resolved','cancelled'].map((s,i)=>`<span>${labels[s]}: <strong>${counts[i]}</strong></span>`).join('')}</div></section><section class="panel"><div class="panel-heading"><h2>Güncel bağlantı envanteri</h2></div>${connections.length?table([tr('Makine / Arayüz'),tr('Kablo'),'Switch / Port',tr('Doğrulama'),tr('İşlem')],connectionRows(connections)):empty(tr('Bağlantı kaydı yok.'))}</section>`;
      after=()=>chart('incident-chart','bar',[tr('Açık'),tr('İnceleniyor'),tr('Beklemede'),tr('Çözüldü'),tr('İptal')],counts,['#b46c4e','#087c7b','#b28b4a','#587d68','#a4aeb5']);
    } else {html=heading(tr('Sayfa bulunamadı'),tr('Menüden bir çalışma alanı seçin.'));}
    // Bekleyen API yanıtı döndüğünde ekran veya oturum değişmişse bu sonuç yerleştirilmez.
    if(id!==renderId || !session)return;
    main.dataset.view=key;main.innerHTML=html;after();window.scrollTo({top:0,behavior:'instant'});document.title=`${main.querySelector('h1')?.textContent||tr('Çalışma alanı')} · PortAtlas`;
  } catch(err) {
    if(id!==renderId||!session)return;
    main.innerHTML=msg`<section class="error-state"><h1>Kayıtlar açılamadı</h1><p>${e(err.message)}</p><button class="button primary" data-action="retry">Yeniden dene</button></section>`;
  }
}

// Seçili portun kayıtlı bağlantısını ve yapılabilecek işlemleri gösterir; seçim gerçek port durumunu değiştirmez.
function portDetail() {
  const p=currentData.ports.find(p=>p.id===selectedPort);if(!p)return;
  document.querySelectorAll('.port').forEach(el=>{el.classList.toggle('selected',Number(el.dataset.id)===selectedPort);el.setAttribute('aria-pressed',String(Number(el.dataset.id)===selectedPort));});
  const c=p.connection;
  document.querySelector('#port-detail').innerHTML=msg`<div class="selected-port"><div><p class="eyebrow">SEÇİLİ PORT ${String(p.number).padStart(2,'0')}</p><h2>${c?e(c.asset_code):tr('Bağlantı kaydı yok')}</h2><p>${c?`${e(c.interface_name)} · ${e(c.cable_label)}`:tr('Bu portta kayıtlı aktif bağlantı bulunmuyor.')}</p></div><div class="selected-port-actions">${badge(c?tr('Kullanımda'):tr('Boş'))}${badge(p.suitability)}${c?msg`<a class="button" href="#device/${c.device_id}">Makine pasaportu ↗</a>`:p.suitability==='suitable'?button(tr('Bağlantı oluştur'),'change',`data-port="${p.id}"`):''}${isManager()?button(tr('Uygunluğu değiştir'),'port-status',`data-id="${p.id}"`):''}</div></div>`;
}

// Cihaz oluşturma/düzenleme formunu hazırlar; güncellemede sürüm ve gerekçe gönderir.
async function deviceForm(device=null) {
  const locations=await api('/locations');if(!locations.length)throw new Error(tr('Önce bir konum oluşturun.'));
  modal(device?tr('Cihazı düzenle'):tr('Yeni cihaz'),input('asset_code',tr('Varlık kodu'),device?.asset_code||'','required maxlength="60"')+input('name',tr('Cihaz adı'),device?.name||'','required maxlength="160"')+select('device_type',tr('Cihaz türü'),[['machine',tr('Makine')],['switch','Switch']],device?.device_type||'machine',device?'disabled':'')+select('location_id',tr('Konum'),options(locations,'id','path'),device?.location_id)+input('brand',tr('Marka'),device?.brand||'')+input('model','Model',device?.model||'')+(!device?input('port_count',tr('Switch için port sayısı'),'24','type="number" min="1" max="128"'):'')+textarea('description',tr('Açıklama'),device?.description||'')+(device?select('active',tr('Kullanım durumu'),[['true',tr('Kullanımda')],['false',tr('Kullanım dışı')]],device.active?'true':'false')+textarea('reason',tr('Değişiklik gerekçesi'),'','required minlength="3"'):''),async data=>{
    const body={...data,device_type:device?.device_type||data.device_type,location_id:Number(data.location_id),port_count:Number(data.port_count||24)};
    if(device)Object.assign(body,{version:device.version,active:data.active==='true'});
    await api(device?`/devices/${device.id}`:'/devices',{method:device?'PATCH':'POST',body});toast(tr('Cihaz kaydedildi.'));await render();
  });
}

// Uygun arayüz, switch portu ve kabloları toplar; bağlantı işlemini tekrar deneme anahtarıyla gönderir.
async function connectionForm(target) {
  const [interfaces,cables,devices,connections,incidents]=await Promise.all([api('/interfaces'),api('/cables'),api('/devices'),api('/connections'),api('/incidents')]);
  const ifaces=interfaces.filter(i=>i.active&&devices.find(d=>d.id===i.device_id)?.active&&(!target.dataset.device||i.device_id===Number(target.dataset.device)));
  if(!ifaces.length)throw new Error(tr('Önce bir makineye ağ arayüzü tanımlayın.'));
  const switchData=await Promise.all(devices.filter(d=>d.device_type==='switch'&&d.active).map(d=>api(`/switches/${d.id}/ports`)));
  const allPorts=switchData.flatMap(d=>d.ports.map(p=>({...p,switch_code:d.device.asset_code})));
  const initial=Number(target.dataset.interface)||ifaces[0].id;
  let requestKey=crypto.randomUUID(), previousPayload='';
  // Form açıldığında kullanılan veriler kayıtta beklenen bağlantı kimliğiyle sunucuda yeniden kontrol edilir.
  const dialog=modal(tr('Bağlantı işlemi'),select('interface_id',tr('Makine / Arayüz'),ifaces.map(i=>[i.id,`${i.asset_code} / ${i.name}`]),initial)+select('kind',tr('İşlem türü'),Object.entries(labels).filter(([k])=>['create','move','replace_cable','terminate'].includes(k)))+`<div class="full current-connection" id="current-connection"></div>`+select('port_id',tr('Hedef switch / Port'),[])+select('cable_id',tr('Kablo'),[])+select('incident_id',tr('İlişkili arıza (isteğe bağlı)'),[['',tr('Arıza seçilmedi')]])+textarea('reason',tr('İşlem gerekçesi'),'','required minlength="3" maxlength="2000"'),async data=>{
    const old=connections.find(c=>c.interface_id===Number(data.interface_id));
    const body={kind:data.kind,interface_id:Number(data.interface_id),expected_connection_id:old?.id||null,port_id:data.kind==='terminate'?null:Number(data.port_id),cable_id:data.kind==='terminate'?null:Number(data.cable_id),incident_id:data.incident_id?Number(data.incident_id):null,reason:data.reason};
    // Aynı içerik tekrar gönderildiğinde request_key korunur; içerik değişmişse yeni anahtar üretilir.
    const serialized=JSON.stringify(body);if(previousPayload&&previousPayload!==serialized)requestKey=crypto.randomUUID();previousPayload=serialized;
    await api('/connection-changes',{method:'POST',body:{...body,request_key:requestKey}});toast(tr('Bağlantı işlemi kaydedildi. Yeni bağlantı ayrıca saha doğrulaması bekler.'));await render();
  });
  const form=dialog.querySelector('form');
  // İşlem türüne göre seçilebilir port/kabloları ve ilişkili arızaları günceller; taşımada kablo, kablo değişiminde port sabit kalır.
  function updateOptions(resetKind=false) {
    const iface=ifaces.find(i=>i.id===Number(form.elements.interface_id.value));
    const old=connections.find(c=>c.interface_id===iface.id);
    if(resetKind)form.elements.kind.innerHTML=(old?['move','replace_cable','terminate']:['create']).map(k=>`<option value="${k}">${labels[k]}</option>`).join('');
    const kind=form.elements.kind.value;
    dialog.querySelector('#current-connection').textContent=old?msg`Mevcut kayıt: ${old.cable_label} → ${old.switch_code} / Port ${String(old.port_number).padStart(2,'0')}. İşlem sırasında bu kaydın güncelliği kontrol edilecek.`:tr('Bu arayüz için aktif bağlantı yok.');
    const ports=allPorts.filter(p=>(p.suitability==='suitable'&&(!p.connection||p.connection.interface_id===iface.id)) || (kind!=='create'&&p.id===old?.port_id));
    form.elements.port_id.innerHTML=ports.map(p=>`<option value="${p.id}">${e(p.switch_code)} / Port ${String(p.number).padStart(2,'0')}${p.suitability==='suitable'?'':' ('+e(labels[p.suitability])+')'}</option>`).join('');
    if(kind==='replace_cable'||kind==='terminate')form.elements.port_id.value=old?.port_id||'';
    else if(target.dataset.port)form.elements.port_id.value=target.dataset.port;
    else if(kind==='move')form.elements.port_id.value=ports.find(p=>p.id!==old.port_id&&p.suitability==='suitable')?.id||'';
    form.elements.port_id.disabled=['replace_cable','terminate'].includes(kind);
    const available=cables.filter(c=>c.active&&(!c.connection_id||c.id===old?.cable_id));
    form.elements.cable_id.innerHTML=available.map(c=>`<option value="${c.id}">${e(c.label)}</option>`).join('');
    if(old&&kind!=='replace_cable')form.elements.cable_id.value=old.cable_id;
    if(kind==='replace_cable')form.elements.cable_id.value=available.find(c=>c.id!==old.cable_id)?.id||'';
    form.elements.cable_id.disabled=['move','terminate'].includes(kind);
    const previousIncident=form.elements.incident_id.value;
    form.elements.incident_id.innerHTML=tr('<option value="">Arıza seçilmedi</option>')+incidents.filter(n=>n.device_id===iface.device_id&&!['resolved','cancelled'].includes(n.status)).map(n=>`<option value="${n.id}">${incidentCode(n.id)} · ${e(n.title)}</option>`).join('');
    form.elements.incident_id.value=previousIncident;
  }
  // Devre dışı select alanları FormData dışında kalır; sabit port/kablo değerleri de gönderilmek zorundadır.
  form.addEventListener('submit',()=>form.querySelectorAll('select:disabled').forEach(s=>s.disabled=false),{capture:true});
  form.elements.interface_id.addEventListener('change',()=>updateOptions(true));
  form.elements.kind.addEventListener('change',()=>updateOptions());updateOptions(true);
}

// Aktif cihazlardan seçim yaparak yeni arıza formunu açar ve kaydı ayrıntı ekranına yönlendirir.
async function incidentForm(target) {
  const devices=(await api('/devices?active=true'));if(!devices.length)throw new Error(tr('Önce bir cihaz tanımlayın.'));
  modal(tr('Yeni arıza kaydı'),select('device_id',tr('İlgili cihaz'),devices.map(d=>[d.id,`${d.asset_code} · ${d.name}`]),target.dataset.device)+input('title',tr('Kısa başlık'),'','required minlength="3" maxlength="180"')+select('priority',tr('Öncelik'),[['medium',tr('Orta')],['high',tr('Yüksek')],['low',tr('Düşük')]])+textarea('description',tr('Sorun açıklaması'),'','required minlength="3" maxlength="4000"'),async data=>{
    const result=await api('/incidents',{method:'POST',body:{...data,device_id:Number(data.device_id)}});toast(tr('Arıza açıldı.'));go(`incident/${result.id}`);
  });
}

const actions={
  // Mobil yan menüyü açıp kapatır ve erişilebilir aria-expanded durumunu günceller.
  menu:()=>{const open=document.querySelector('.sidebar').classList.toggle('open');document.querySelector('.mobile-menu').setAttribute('aria-expanded',String(open));},
  // Hatalı ekran yüklemesini aynı render akışıyla tekrar dener.
  retry:render,
  // Sunucu oturumunu kapatır; yerel kullanıcı durumunu temizleyerek giriş ekranına döner.
  logout:async()=>{await api('/auth/logout',{method:'POST'});setSession(null);login();},
  // Boş cihaz formunu açar.
  'new-device':()=>deviceForm(),
  // Mevcut cihaz verisiyle düzenleme formunu açar.
  'edit-device':()=>deviceForm(currentData.device),
  // Switch düzenlemesini ortak cihaz formu üzerinden yürütür.
  'edit-switch':()=>deviceForm(currentData.device),
  // Seçilen cihaz için arıza oluşturma akışını başlatır.
  'new-incident':incidentForm,
  // Bağlantı oluşturma, taşıma, kablo değiştirme veya sonlandırma formunu açar.
  change:connectionForm,
  // Seçili port kimliğini günceller ve ayrıntısını gösterir; veri yazmaz.
  'select-port':target=>{selectedPort=Number(target.dataset.id);portDetail();},
  // Port uygunluğunu gerekçe ve sürüm bilgisiyle değiştirir.
  'port-status':target=>{const p=currentData.ports.find(p=>p.id===Number(target.dataset.id));modal(msg`Port ${String(p.number).padStart(2,'0')} kullanım uygunluğu`,select('suitability',tr('Uygunluk'),[['suitable',tr('Uygun')],['faulty',tr('Arızalı')],['disabled',tr('Devre dışı')]],p.suitability)+textarea('reason',tr('Gerekçe'),'','required minlength="3"'),async data=>{await api(`/ports/${p.id}`,{method:'PATCH',body:{...data,version:p.version}});toast(tr('Port uygunluğu kaydedildi.'));await render();});},
  // Bağlantı için saha kontrol sonucunu ve gözlem notunu kaydeder.
  verify:target=>modal(tr('Saha doğrulaması'),select('result',tr('Kontrol sonucu'),[['verified',tr('Bağlantı kayıtla tutarlı')],['mismatch',tr('Sahada farklı bağlantı var')]])+textarea('note',tr('Kontrol açıklaması'),'','required minlength="3"'),async data=>{await api(`/connections/${target.dataset.id}/verifications`,{method:'POST',body:data});toast(tr('Saha kontrolü kaydedildi.'));await render();}),
  // Arıza günlüğüne yapılan kontrolü ve sonucunu ekler.
  intervene:()=>modal(tr('Müdahale ekle'),textarea('note',tr('Yapılan kontrol ve gözlenen sonuç'),'','required minlength="3"'),async data=>{await api(`/incidents/${currentData.incident.id}/interventions`,{method:'POST',body:data});toast(tr('Müdahale kaydedildi.'));await render();}),
  // Arıza sorumlusunu güncel kayıt sürümüyle atar.
  assign:()=>modal(tr('Arıza sorumlusu ata'),select('user_id',tr('Sorumlu'),options(currentData.users.filter(u=>u.active),'id','name'),currentData.incident.assigned_to),async data=>{await api(`/incidents/${currentData.incident.id}/assign`,{method:'POST',body:{user_id:Number(data.user_id),version:currentData.incident.version}});toast(tr('Sorumlu atandı.'));await render();}),
  // Arıza durumunu gerekçeyle değiştirir; çözümde saha onayı ister.
  transition:target=>{const status=target.dataset.status;modal(labels[status],textarea('reason',status==='resolved'?tr('Çözüm açıklaması'):tr('İşlem gerekçesi'),'','required minlength="3"')+(status==='resolved'?tr('<label class="checkbox-label full"><input type="checkbox" name="verified" required> Sorunun giderildiğini sahada kontrol ettim.</label>'):''),async data=>{await api(`/incidents/${currentData.incident.id}/transitions`,{method:'POST',body:{status,version:currentData.incident.version,reason:data.reason,verified:data.verified==='on'}});toast(tr('Arıza durumu güncellendi.'));await render();});},
  // Benzersiz etiketli yeni kablo formunu açar.
  'new-cable':()=>modal(tr('Yeni kablo'),input('label',tr('Kablo etiketi'),'','required')+input('cable_type',tr('Kablo türü'),'CAT6','required'),async data=>{await api('/cables',{method:'POST',body:data});toast(tr('Kablo eklendi.'));await render();}),
  // Aktif makinelerden seçilen cihaza ağ arayüzü ekler.
  'new-interface':async()=>{const devices=(await api('/devices?device_type=machine&active=true'));if(!devices.length)throw new Error(tr('Önce bir makine ekleyin.'));modal(tr('Yeni ağ arayüzü'),select('device_id',tr('Makine'),devices.map(d=>[d.id,`${d.asset_code} · ${d.name}`]))+input('name',tr('Arayüz adı'),'Ethernet-1','required')+input('ip',tr('Kayıtlı IP (isteğe bağlı)'))+input('mac',tr('MAC adresi (isteğe bağlı)')),async data=>{await api('/interfaces',{method:'POST',body:{...data,device_id:Number(data.device_id)}});toast(tr('Arayüz eklendi.'));await render();});},
  // Üst konum ve tür seçimiyle hiyerarşiye yeni düğüm ekler.
  'new-location':async()=>{const locations=await api('/locations');modal(tr('Yeni konum'),input('code',tr('Konum kodu'),'','required')+input('name',tr('Konum adı'),'','required')+select('kind',tr('Konum türü'),[['facility',tr('Tesis')],['area',tr('Bölge')],['line',tr('Hat')],['station',tr('İstasyon')]])+select('parent_id',tr('Üst konum'),[['',tr('Üst konum yok')],...options(locations,'id','path')]),async data=>{await api('/locations',{method:'POST',body:{...data,parent_id:data.parent_id?Number(data.parent_id):null}});toast(tr('Konum eklendi.'));await render();});},
  // Yönetici için başlangıç parolası ve rol içeren hesap formunu açar.
  'new-user':()=>modal(tr('Yeni ekip hesabı'),input('name',tr('Ad soyad'),'','required minlength="3"')+input('username',tr('Kullanıcı adı'),'','required minlength="3" autocomplete="off"')+input('password',tr('İlk parola'),'','type="password" required minlength="10" autocomplete="new-password"')+select('role',tr('Rol'),[['technician',tr('Saha teknisyeni')],['manager',tr('IT/OT sorumlusu')]]),async data=>{await api('/users',{method:'POST',body:data});toast(tr('Hesap oluşturuldu.'));await render();}),
  // Tarayıcının yazdır/PDF akışını açar; baskı CSS’i işlem düğmelerini gizler.
  print:()=>window.print(),
  // Görünen bağlantı verisinden CSV üretir; formül başlangıçlarını etkisizleştirir ve Türkçe karakterler için BOM ekler.
  export:()=>{const records=currentData.connections;const cell=v=>'"'+String(v??'').replace(/^[=+@\-\t\r]/,"'$&").replaceAll('"','""')+'"';const lines=[[tr('Makine'),tr('Arayüz'),tr('Kablo'),'Switch','Port',tr('Doğrulama'),tr('Son kontrol')],...records.map(c=>[c.asset_code,c.interface_name,c.cable_label,c.switch_code,c.port_number,labels[c.verification],c.verified_at?date(c.verified_at):tr('Bilgi girilmedi')])];const blob=new Blob([tr('\uFEFFBağlantı envanteri;Kapsam: Tüm tesisler;')+date(new Date().toISOString())+'\r\n'+lines.map(r=>r.map(cell).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8;'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=document.documentElement.lang==='en'?'portatlas-connection-inventory.csv':'portatlas-baglanti-envanteri.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);},
};
// OT modülünün yenileme/yönlendirme ihtiyaçları ana uygulamanın işlevlerine bağlanır.
configureOt({refresh:render,navigate:go});
// Tek olay dinleyicisi data-action üzerinden çekirdek veya OT işlemine yönlendirir; hatalar ortak bildirimde gösterilir.
document.addEventListener('click',async event=>{const target=event.target.closest('[data-action]');if(!target)return;const action=actions[target.dataset.action]||otActions[target.dataset.action];if(!action)return;try{await action(target);}catch(err){toast(err.message);}});
// Adres değişimleri yeni ekranı yükler; oturum bitişi açık formu kapatıp giriş ekranını gösterir.
window.addEventListener('hashchange',render);
window.addEventListener('session-expired',()=>{setSession(null);document.querySelector('#modal').close();login(tr('Oturumunuz sona erdi. Tekrar giriş yapın.'));});
// Sayfa açılışında sunucudaki oturum sorgulanır; tarayıcıdaki eski kullanıcı bilgisine güvenilmez.
try {setSession(await api('/auth/me'));shell();await render();}catch{login();}
