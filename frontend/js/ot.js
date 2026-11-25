// OT arayüzü: SUC, zone/conduit, SL-A/SL-T, kontroller ve bulgu formları.
import { t as tr, msg } from './i18n.js?v=i18n-1';
import {api,session} from './api.js?v=i18n-1';
import {e,date,badge,empty,heading,button,select,input,textarea,table,modal,toast,labels} from './ui.js?v=i18n-1';

Object.assign(labels,{draft:tr('Taslak'),approved:tr('Onaylı'),pending_review:tr('Kapsam dışı onayı bekliyor'),completed:tr('Tamamlandı'),unknown:tr('Bilinmiyor'),unsuitable:tr('Uygun değil'),not_applicable:tr('Uygulanamaz'),in_progress:tr('İşlemde'),awaiting_verification:tr('Doğrulama bekliyor'),closed:tr('Kapalı')});
let data={},detail={},scope=null,refresh=()=>{},navigate=()=>{};
// OT düğmelerini kullanıcı rolüne göre gösterir; sunucu yetkilendirmesi ayrıca uygulanır.
const manager=()=>session?.role==='manager';
// OT seçim alanlarında API kayıtlarını değer/etiket çiftlerine çevirir.
const optionPairs=(items,value,label)=>items.map(i=>[i[value],i[label]]);
// Bulgu kimliğini OT-001 biçiminde gösterir; bu yalnızca görünen kayıt kodudur.
const code=id=>`OT-${String(id).padStart(3,'0')}`;
// OT işlemlerini ot- önekiyle ana uygulamanın işlem adlarından ayırır.
const action=(text,name,attrs='')=>button(text,`ot-${name}`,attrs);
// OT alt ekranlarına güvenli görünen metinle bağlantı kurar.
const otLink=(url,text,cls='text-link')=>`<a class="${cls}" href="#ot/${url}">${e(text)}</a>`;
// Eksik profili belirlenmedi olarak, bilinmeyen vektör elemanını soru işaretiyle gösterir.
const profileSummary=p=>!p?tr('Belirlenmedi'):p.vector.map(v=>v??'?').join(' · ');
// Taslak/onay durumuna ek olarak kapsam değişmişse inceleme uyarısı üretir.
const profileStatus=p=>!p?badge(tr('Değerlendirilmedi')):`${badge(p.status)}${p.stale?badge(tr('Gözden geçirme gerekli')):''}`;
// OT ekranlarında mevcut/hedef ve sertifikasyon sınırını açıklayan ortak bilgilendirme metnidir.
const note=tr('<div class="info-line">SL-A kayıtlı mevcut değerlendirmedir; SL-T hedeftir. Seviyeler otomatik hesaplanmaz. Kontrol sonuçları standart uygunluğu veya sertifikasyon sonucu değildir.</div>');
// OT modülüne ekran yenileme ve yönlendirme işlevlerini dışarıdan verir; modül ana uygulamaya doğrudan bağımlı olmaz.
export function configureOt(config){refresh=config.refresh;navigate=config.navigate;}

// OT alt ekranlarının gezinme bağlantılarını üretir; mevcut ekranı seçili olarak işaretler.
function tabs(key){
  return msg`<nav class="tabs ot-tabs" aria-label="OT çalışma alanları">${[['',tr('Genel görünüm')],['zones',tr('Zone’lar')],['conduits',tr('Conduit’ler')],['assessments',tr('Kontroller')],['findings',tr('Bulgular')],['history',tr('OT geçmişi')]].map(([path,title])=>`<a href="#ot${path?'/'+path:''}" class="${key===(path?`ot/${path}`:'ot')?'active':''}">${title}</a>`).join('')}</nav>`;
}

// Zone listesini ayrı mevcut/hedef profil özetleriyle gösterir; değerlendirilmemiş kapsamı güvenli saymaz.
function zonesTable(zones){
  return zones.length?table([tr('Zone / Sistem'),tr('Sorumlu'),tr('Varlık'),tr('SL-A · Mevcut'),tr('SL-T · Hedef')],zones.map(z=>`<tr><td>${otLink(`zone/${z.id}`,z.code,'record-link mono')}<small>${e(z.name)} · ${e(z.system_name)}</small></td><td>${e(z.owner_name)}</td><td>${z.member_count}</td><td><span class="mono">${profileSummary(z.levels.latest.achieved)}</span><small>${profileStatus(z.levels.latest.achieved)}</small></td><td><span class="mono">${profileSummary(z.levels.latest.target)}</span><small>${profileStatus(z.levels.latest.target)}</small></td></tr>`).join('')):empty(tr('Henüz zone yok. Önce sistem kapsamını ve güvenlik sınırlarını tanımlayın.'));
}

// Bulguları öncelik kararı, sorumlu, tarih ve durumuyla listeler; kayıt yokluğu değerlendirme sonucu değildir.
function findingsTable(findings){
  return findings.length?table([tr('Bulgu / Kapsam'),tr('Öncelik'),tr('Sorumlu'),tr('Hedef tarih'),tr('Durum')],findings.map(f=>`<tr><td>${otLink(`finding/${f.id}`,`${code(f.id)} · ${f.title}`,'record-link')}<small>${e(f.scope_code)}${f.control_code?' · '+e(f.control_code):''}${f.fr_code?' · '+e(f.fr_code):''}</small></td><td>${f.priority_reviewed?badge(f.priority):badge(tr('Öncelik bekliyor'))}</td><td>${e(f.assignee_name||tr('Atama bekliyor'))}</td><td>${e(f.due_date||tr('Tarih bekliyor'))}${f.overdue?`<small>${badge(tr('Gecikti'))}</small>`:''}</td><td>${badge(f.status)}</td></tr>`).join('')):empty(tr('Bu görünümde bulgu kaydı yok. Bu ifade kontrolün yapıldığını veya güvenli olduğunu göstermez.'));
}

// Kontrol kayıtlarını şablon sürümü ve güncellik uyarılarıyla gösterir; eski sonuçları gizlemez.
function assessmentTable(records){
  return records.length?table([tr('Kontrol'),tr('Cihaz'),tr('Şablon'),tr('Durum'),tr('Tarih')],records.map(a=>`<tr><td>${otLink(`assessment/${a.id}`,`KNT-${a.id}`,'record-link mono')}</td><td>${otLink(`device/${a.device_id}`,data.devices.find(d=>d.id===a.device_id)?.asset_code||a.device_id)}</td><td>${e(a.template_version)}</td><td>${badge(a.status)}${a.stale_items.length?msg`<small>${e(a.stale_items.join(', '))} yeniden değerlendirilmeli</small>`:''}</td><td>${date(a.completed_at||a.created_at)}</td></tr>`).join('')):empty(tr('Henüz kontrol yapılmadı. Cihazlar değerlendirilmedi olarak izlenir.'));
}

// SL-A mevcut durum ile SL-T hedefi FR1–FR7 sırasında gösterir; fark ve geçmiş revizyonlar API sonucundan okunur.
function levelPanel(s){
  const a=s.levels.latest.achieved,t=s.levels.latest.target;
  return msg`<section class="panel sl-panel"><div class="panel-heading"><div><p class="eyebrow">GÜVENLİK SEVİYESİ PROFİLİ</p><h2>Mevcut durum ve hedef</h2></div>${manager()?`<div class="heading-actions">${action(tr('SL-A kaydet'),'level','data-type="achieved"')}${action(tr('SL-T kaydet'),'level','data-type="target"')}</div>`:''}</div><div class="sl-profile-head"><div><strong>SL-A <small>Mevcut değerlendirilen seviye</small></strong>${profileStatus(a)}<p>${e(a?.reference||tr('Kanıt referansı kaydedilmedi'))}</p></div><div><strong>SL-T <small>Hedef güvenlik seviyesi</small></strong>${profileStatus(t)}<p>${e(t?.reference||tr('Risk değerlendirmesi referansı kaydedilmedi'))}</p></div></div>${table([tr('Temel gereksinim'),'SL-A','SL-T',tr('Hedef farkı')],data.frs.map((fr,i)=>`<tr><td><strong>${e(fr.code)}</strong> ${e(tr(fr.name))}</td><td class="sl-value">${a?.vector[i]??'—'}</td><td class="sl-value">${t?.vector[i]??'—'}</td><td>${s.levels.gaps[i]===null?tr('Hesaplanmadı'):s.levels.gaps[i]===0?tr('Hedef altında değil'):msg`${s.levels.gaps[i]} seviye fark ${action(tr('Aksiyon aç'),'finding',`data-scope="${s.member_count!==undefined?'zone':'conduit'}:${s.id}" data-fr="${fr.code}" data-profile="${t.id}"`)}`}</td></tr>`).join(''))}<p class="panel-note">Sıra: FR1–FR7. “Belirlenmedi” seviye 0 değildir. Fark yalnızca iki onaylı ve güncel değerlendirme arasında hesaplanır; uygunluk kararı değildir.</p>${a||t?`<div class="sl-rationales">${a?msg`<div><strong>SL-A değerlendirme notu</strong><p>${e(a.rationale)}</p><small>${e(a.author_name)} · ${date(a.created_at)}</small></div>`:''}${t?msg`<div><strong>SL-T risk gerekçesi</strong><p>${e(t.rationale)}</p><small>${e(t.author_name)} · ${date(t.created_at)}</small></div>`:''}</div>`:''}</section><section class="panel"><div class="panel-heading"><h2>Seviye revizyonları</h2></div>${s.levels.history.length?table([tr('Profil'),tr('Vektör'),tr('Durum'),tr('Dayanak'),tr('Kaydeden / Tarih')],s.levels.history.map(p=>`<tr><td>${p.sl_type==='achieved'?'SL-A':'SL-T'} · R${p.revision}</td><td class="mono">${profileSummary(p)}</td><td>${profileStatus(p)}</td><td>${e(p.reference||tr('Referans yok'))}<small>${e(p.rationale)}</small></td><td>${e(p.author_name)}<small>${date(p.created_at)}${p.approver_name?tr(' · Onay: ')+e(p.approver_name):''}</small></td></tr>`).join('')):empty(tr('Seviye değerlendirmesi kaydedilmedi.'))}</section>`;
}

// OT genel görünüm, kapsam, profil, cihaz kontrolü ve bulgu ekranlarını ortak API sözleşmesi üzerinden üretir.
export async function renderOt(key){
  data=await api('/ot/overview');scope=null;detail={};
  const path=key.split('/');const id=Number(path[2]);
  let html='';
  if(key==='ot'){
    // OT genel görünüm: kapsam, ayrı SL profilleri ve açık aksiyonların özeti.
    
    const c=data.counts;
    html=heading(tr('OT güvenlik'),tr('Zone sınırlarından doğrulanmış aksiyonlara uzanan çalışma alanı.'),action(tr('+ Bulgu aç'),'finding'))+tabs(key)+msg`<section class="ot-intro"><div><span class="eyebrow">ZONE & CONDUIT YAKLAŞIMI</span><h2>Önce kapsamı tanımlayın.<br>Mevcut seviyeyi hedefle karşılaştırın.</h2><p>Varlıkları güvenlik ihtiyacına göre gruplayın, zone’lar arası iletişimi kaydedin ve açıkları sorumlusu belli aksiyonlarla takip edin.</p></div><div class="ot-flow"><span>01 <strong>Sistem kapsamı</strong></span><span>02 <strong>Zone / Conduit</strong></span><span>03 <strong>SL-A ↔ SL-T</strong></span><span>04 <strong>Kontrol / Aksiyon</strong></span></div></section><section class="metrics ot-metrics"><a href="#ot/zones" class="metric"><span>Tanımlı zone</span><strong>${c.zones}</strong><p>${c.conduits} kayıtlı conduit</p></a><a href="#ot/devices?filter=unzoned" class="metric"><span>Zone atanmamış varlık</span><strong>${c.unzoned}</strong><p>Aktif envanter içinde</p></a><a href="#ot/findings?filter=active" class="metric attention"><span>Açık güvenlik bulgusu</span><strong>${c.open_findings}</strong><p>Aksiyon ve doğrulama sürecinde</p></a><a href="#ot/findings?filter=overdue" class="metric attention"><span>Geciken aksiyon</span><strong>${c.overdue}</strong><p>Hedef tarihi geçmiş açık kayıtlar</p></a></section><section class="panel"><div class="panel-heading"><h2>Zone güvenlik profilleri</h2>${otLink('zones',tr('Zone’ları yönet ↗'))}</div>${zonesTable(data.zones)}</section><section class="panel"><div class="panel-heading"><h2>Açık bulgular</h2>${otLink('findings',tr('Tüm bulgular ↗'))}</div>${findingsTable(data.findings.filter(f=>!['closed','cancelled'].includes(f.status)))}</section><div class="info-line">${c.unknown_criticality} aktif cihazın kritikliği bilinmiyor. ${otLink('devices',tr('Cihaz güvenlik kayıtlarını aç ↗'))}</div>`+note;
  }else if(key==='ot/zones'){
    // SUC ve zone yönetimi: güvenlik sınırları fiziksel konumdan ayrı tanımlanır.
    
    html=heading(tr('Güvenlik zone’ları'),tr('Fiziksel konumdan bağımsız, ortak güvenlik ihtiyaçlarına göre varlık grupları.'),manager()?`<div class="heading-actions">${action(tr('+ Sistem kapsamı'),'system')}${action(tr('+ Zone oluştur'),'zone')}</div>`:'')+tabs(key)+msg`<section class="panel"><div class="panel-heading"><h2>Sistem kapsamları (SUC)</h2></div>${data.systems.length?`<div class="scope-list">${data.systems.map(s=>msg`<article><span class="mono">${e(s.code)}</span><h3>${e(s.name)}</h3><p>${e(s.boundary)}</p><small>Sorumlu: ${e(s.owner_name)}</small></article>`).join('')}</div>`:empty(tr('İlk zone için önce sistemin kapsamını ve sınırlarını tanımlayın.'))}</section><section class="panel"><div class="panel-heading"><h2>Zone envanteri</h2>${otLink('devices?filter=unzoned',tr('Atanmamış varlıklar ↗'))}</div>${zonesTable(data.zones)}</section>`;
  }else if(path[1]==='zone'){
    // Zone ayrıntısı: üyeler, seviye revizyonları, ilişkili conduit ve bulgular.
    
    scope=data.zones.find(z=>z.id===id);if(!scope)throw new Error(tr('Zone bulunamadı.'));
    const members=data.devices.filter(d=>d.zone_id===id);
    html=heading(scope.code,scope.name,manager()?`<div class="heading-actions">${action(tr('Zone düzenle'),'zone',`data-id="${id}"`)}${action(tr('Üyeleri düzenle'),'members')}</div>`:'')+tabs(key)+msg`<div class="ot-scope-summary"><div><span class="small-label">SİSTEM</span><strong>${e(scope.system_name)}</strong></div><div><span class="small-label">SORUMLU</span><strong>${e(scope.owner_name)}</strong></div><div><span class="small-label">SINIR / AMAÇ</span><p>${e(scope.boundary)}</p><p>${e(scope.purpose)}</p></div></div>`+levelPanel(scope)+msg`<section class="panel"><div class="panel-heading"><h2>Zone varlıkları</h2>${action(tr('+ Bulgu aç'),'finding',`data-scope="zone:${id}"`)}</div>${deviceTable(members)}</section><section class="panel"><div class="panel-heading"><h2>İlişkili conduit’ler</h2></div>${conduitTable(data.conduits.filter(c=>c.source_zone_id===id||c.target_zone_id===id))}</section><section class="panel"><div class="panel-heading"><h2>Zone bulguları</h2></div>${findingsTable(data.findings.filter(f=>f.zone_id===id))}</section>`+note;
  }else if(key==='ot/conduits'){
    // Conduit listesi: zone’lar arası iletişim kapsamının belgeleri.
    
    html=heading(tr('Güvenlik conduit’leri'),tr('Zone’lar arasındaki kayıtlı iletişim kapsamı, yönü ve koruma önlemleri.'),manager()?action(tr('+ Conduit oluştur'),'conduit'):'')+tabs(key)+`<section class="panel">${conduitTable(data.conduits)}</section>`+note;
  }else if(path[1]==='conduit'){
    // Conduit ayrıntısı: uçlar, yön, önlemler, profiller ve ilişkili bulgular.
    
    scope=data.conduits.find(c=>c.id===id);if(!scope)throw new Error(tr('Conduit bulunamadı.'));
    html=heading(scope.code,scope.name,manager()?action(tr('Conduit düzenle'),'conduit',`data-id="${id}"`):'')+tabs(key)+msg`<section class="panel"><div class="conduit-route">${otLink(`zone/${scope.source_zone_id}`,scope.source_code,'conduit-end')}<span>${scope.direction==='bidirectional'?'↔':'→'}</span>${otLink(`zone/${scope.target_zone_id}`,scope.target_code,'conduit-end')}</div><dl class="detail-list"><div><dt>Protokol / Port</dt><dd>${e(scope.protocols)}</dd></div><div><dt>İletişim amacı</dt><dd>${e(scope.purpose)}</dd></div><div><dt>Kayıtlı önlemler</dt><dd>${e(scope.controls)}</dd></div><div><dt>Sorumlu</dt><dd>${e(scope.owner_name)}</dd></div></dl><p class="panel-note">Bu kayıt iletişimin dokümantasyonudur. Ağ trafiği izlenmez ve firewall kuralı uygulanmaz.</p></section>`+levelPanel(scope)+msg`<section class="panel"><div class="panel-heading"><h2>Conduit bulguları</h2>${action(tr('+ Bulgu aç'),'finding',`data-scope="conduit:${id}"`)}</div>${findingsTable(data.findings.filter(f=>f.conduit_id===id))}</section>`+note;
  }else if(key==='ot/devices'){
    // Cihaz güvenlik listesi: zone üyeliği, kritiklik ve kontrol durumları.
    
    const filter=new URLSearchParams(location.hash.split('?')[1]||'').get('filter');
    html=heading(tr('Cihaz güvenlik kayıtları'),tr('Kritiklik, zone üyeliği ve tamamlanan kontrol kayıtları.'))+tabs(key)+msg`<div class="tabs"><a href="#ot/devices">Tüm cihazlar</a><a href="#ot/devices?filter=unzoned">Zone atanmamış</a></div><section class="panel">${deviceTable(data.devices.filter(d=>d.active&&(!filter||filter!=='unzoned'||!d.zone_id)))}</section>`;
  }else if(path[1]==='device'){
    // Cihaz pasaportu: fiziksel bağlantılar, saha kontrolleri, arızalar ve OT kaydına geçiş.
    
    const device=data.devices.find(d=>d.id===id);if(!device)throw new Error(tr('Cihaz bulunamadı.'));
    detail=await api(`/ot/devices/${id}`);
    html=heading(`${device.asset_code} · OT`,device.name,`<div class="heading-actions">${action(tr('Kontrol başlat'),'assessment',`data-device="${id}"`)}${manager()?action(tr('Kritiklik belirle'),'criticality',`data-device="${id}"`):''}</div>`)+tabs(key)+msg`<section class="panel"><div class="panel-heading"><h2>Güvenlik bağlamı</h2><a href="#device/${id}" class="text-link">Bağlantı pasaportu ↗</a></div><dl class="detail-list"><div><dt>Operasyonel kritiklik</dt><dd>${badge(device.criticality)}</dd></div><div><dt>Değerlendirme gerekçesi</dt><dd>${e(device.rationale||tr('Kaydedilmedi'))}</dd></div><div><dt>Zone üyeliği</dt><dd>${device.zone_id?otLink(`zone/${device.zone_id}`,device.zone_code):tr('Zone atanmadı')}</dd></div></dl><p class="panel-note">Kritiklik üretim etkisini ifade eder. SL-A ve SL-T zone/conduit kapsamındadır; cihaz kritikliği bir güvenlik seviyesi değildir.</p></section><section class="panel"><div class="panel-heading"><h2>Kontrol geçmişi</h2></div>${assessmentTable(detail.assessments)}</section><section class="panel"><div class="panel-heading"><h2>Cihaz bulguları</h2>${action(tr('+ Bulgu aç'),'finding',`data-scope="device:${id}"`)}</div>${findingsTable(detail.findings)}</section>`;
  }else if(key==='ot/assessments'){
    // Kontrol listesi: şablon sürümleriyle değerlendirme kayıtları.
    
    html=heading(tr('Cihaz güvenlik kontrolleri'),tr('Sürümlü kontrol listesiyle gözlem, sonuç ve kanıt kaydı.'),action(tr('+ Kontrol başlat'),'assessment'))+tabs(key)+msg`<div class="info-line">${e(data.template_version)} · PortAtlas başlangıç kontrol soruları. IEC standardının resmi kontrol listesi değildir.</div><section class="panel">${assessmentTable(data.assessments)}</section>`;
  }else if(path[1]==='assessment'){
    // Kontrol ayrıntısı: saklanan soru/yanıtlar, kanıtlar ve değişen bağlam uyarıları.
    
    detail=await api(`/ot/assessments/${id}`);
    const device=data.devices.find(d=>d.id===detail.device_id);
    html=heading(`KNT-${id}`,`${device?.asset_code} · ${detail.template_version}`,detail.status==='draft'&&(manager()||detail.author_id===session.id)?action(tr('Taslağa devam et'),'assessment',`data-id="${id}"`):detail.status==='pending_review'&&manager()?action(tr('Uygulanamaz seçimlerini onayla'),'approve-applicability'):'')+tabs(key)+`<div class="passport-meta">${badge(detail.status)}<span>${date(detail.completed_at||detail.created_at)}</span>${otLink(`device/${detail.device_id}`,tr('Cihaz güvenlik kaydı ↗'))}</div>${detail.stale_items.length?msg`<div class="info-line">Bağlam değişti: ${e(detail.stale_items.join(', '))} yeniden değerlendirme bekliyor. Eski sonuçlar korunur.</div>`:''}<section class="panel">${table([tr('Kontrol'),tr('Sonuç'),tr('Açıklama / Kanıt'),tr('İşlem')],detail.template.map(item=>{const r=detail.results.find(r=>r.code===item.code);return `<tr><td><strong>${e(item.code)}</strong><small>${e(tr(item.question))}</small></td><td>${r?.result?badge(r.result):badge(tr('Seçilmedi'))}</td><td>${e(r?.note||tr('Açıklama yok'))}<small>${e(r?.evidence||tr('Kanıt referansı yok'))}</small></td><td>${detail.status!=='draft'&&['unsuitable','unknown'].includes(r?.result)?action(tr('Bulgu aç'),'finding',`data-scope="device:${detail.device_id}" data-assessment="${id}" data-control="${item.code}"`):''}</td></tr>`;}).join(''))}</section>${detail.approval_note?msg`<div class="info-line">Uygulanamaz onayı: ${e(detail.approval_note)}</div>`:''}`;
  }else if(key==='ot/findings'){
    // Bulgu listesi: açık, gecikmiş veya kullanıcıya atanmış aksiyonların takibi.
    
    const filter=new URLSearchParams(location.hash.split('?')[1]||'').get('filter');
    const list=data.findings.filter(f=>filter==='overdue'?f.overdue:filter==='active'?!['closed','cancelled'].includes(f.status):filter==='mine'?f.assigned_to===session.id:true);
    html=heading(tr('Güvenlik bulguları'),tr('Gözlemden düzeltmeye, ayrı doğrulamayla kapanan aksiyonlar.'),action(tr('+ Bulgu aç'),'finding'))+tabs(key)+msg`<div class="tabs"><a href="#ot/findings">Tümü</a><a href="#ot/findings?filter=active">Açık</a><a href="#ot/findings?filter=overdue">Geciken</a><a href="#ot/findings?filter=mine">Bana atanan</a></div><section class="panel">${findingsTable(list)}</section>`;
  }else if(path[1]==='finding'){
    // Bulgu ayrıntısı: plan, uygulama, doğrulama ve denetim geçmişi.
    
    detail=await api(`/ot/findings/${id}`);const f=detail.finding;
    const active=!['closed','cancelled'].includes(f.status);
    const canWork=manager()||f.assigned_to===session.id;
    const history=[...detail.events.map(a=>({...a,title:a.action==='plan'?tr('Aksiyon planı güncellendi'):a.action==='create'?tr('Bulgu açıldı'):tr('Durum güncellendi'),text:a.reason})),...detail.actions.map(a=>({...a,title:{work:tr('Uygulama'),submit:tr('Doğrulamaya gönderildi'),verify:tr('Kapanış doğrulaması'),return:tr('İşleme döndürüldü'),cancel:tr('İptal'),reopen:tr('Yeniden açıldı')}[a.kind],text:a.note}))].sort((a,b)=>a.created_at.localeCompare(b.created_at));
    html=heading(`${code(id)} · ${f.scope_code}`,f.title,manager()&&active&&f.status!=='awaiting_verification'?action(tr('Aksiyon planla'),'plan'):'')+tabs(key)+msg`<div class="passport-meta">${badge(f.status)}${f.priority_reviewed?badge(f.priority):badge(tr('Öncelik bekliyor'))}${f.overdue?badge(tr('Gecikti')):''}</div><div class="two-column incident-layout"><section class="panel"><div class="panel-heading"><h2>Gözlem ve aksiyon geçmişi</h2></div><p class="description-text">${e(f.observation)}</p><div class="timeline">${history.map(a=>`<article><span class="timeline-dot"></span><small>${date(a.created_at)} · ${e(a.actor_name)}</small><h3>${e(a.title)}</h3><p>${e(a.text)}</p>${a.evidence?msg`<small>Kanıt: ${e(a.evidence)}</small>`:''}</article>`).join('')}</div></section><section class="panel"><div class="panel-heading"><h2>Aksiyon ayrıntıları</h2></div><dl class="detail-list"><div><dt>Sorumlu</dt><dd>${e(f.assignee_name||tr('Atama bekliyor'))}</dd></div><div><dt>Hedef tarih</dt><dd>${e(f.due_date||tr('Tarih bekliyor'))}</dd></div><div><dt>Kapsam</dt><dd>${otLink(`${f.device_id?'device':f.zone_id?'zone':'conduit'}/${f.device_id||f.zone_id||f.conduit_id}`,f.scope_code)}</dd></div>${f.target_profile_id?msg`<div><dt>Hedef profili</dt><dd>SL-T #${f.target_profile_id} · ${e(f.fr_code)}</dd></div>`:''}${f.assessment_id?msg`<div><dt>İlgili kontrol</dt><dd>${otLink(`assessment/${f.assessment_id}`,`KNT-${f.assessment_id} / ${f.control_code}`)}</dd></div>`:''}</dl><div class="stack-actions">${canWork&&['open','in_progress'].includes(f.status)?action(tr('Aksiyon güncelle'),'finding-action','data-kind="work"'):''}${canWork&&f.status==='in_progress'?action(tr('Doğrulamaya gönder'),'finding-action','data-kind="submit"'):''}${manager()&&f.status==='awaiting_verification'?action(tr('Doğrula ve kapat'),'finding-action','data-kind="verify"')+action(tr('İşleme döndür'),'finding-action','data-kind="return"'):''}${manager()&&active?action(tr('Gerekçeyle iptal'),'finding-action','data-kind="cancel"'):''}${manager()&&f.status==='closed'?action(tr('Yeniden aç'),'finding-action','data-kind="reopen"'):''}</div><p class="panel-note">Yüksek öncelikli bulguda uygulayan ve doğrulayan farklı kişiler olmalıdır. Arızanın çözülmesi bu bulguyu kapatmaz.</p></section></div>`;
  }else if(key==='ot/history'){
    // OT denetim görünümü: kapsam değişiklikleri, revizyonlar ve bulgu işlemleri.
    
    const history=await api('/ot/history');html=heading(tr('OT değişiklik geçmişi'),tr('Zone üyeliği, seviye revizyonları, atamalar ve kapanış kayıtları.'))+tabs(key)+`<section class="panel">${history.length?table([tr('Tarih / Kullanıcı'),tr('Kayıt'),tr('İşlem'),tr('Gerekçe'),tr('Önce / Sonra')],history.map(a=>msg`<tr><td>${date(a.created_at)}<small>${e(a.actor_name)}</small></td><td class="mono">${e(a.entity_type)} #${a.entity_id}</td><td>${e(a.action)}</td><td>${e(a.reason)}</td><td><details><summary>Değişikliği aç</summary><pre>${e(JSON.stringify({once:JSON.parse(a.before_json||'null'),sonra:JSON.parse(a.after_json||'null')},null,2))}</pre></details></td></tr>`).join('')):empty(tr('Henüz OT değişikliği yok.'))}</section>`;
  }else{throw new Error(tr('OT sayfası bulunamadı.'));}
  return {html,after:()=>{}};
}

// Cihazın zone, kritiklik ve değerlendirme durumunu özetler; bunları tek bir güvenlik puanına dönüştürmez.
function deviceTable(devices){
  return devices.length?table([tr('Varlık'),'Zone',tr('Kritiklik'),tr('Kontrol durumu')],devices.map(d=>{const assessments=data.assessments.filter(a=>a.device_id===d.id);const completed=assessments.find(a=>a.status==='completed');return `<tr><td>${otLink(`device/${d.id}`,d.asset_code,'record-link mono')}<small>${e(d.name)}</small></td><td>${d.zone_id?otLink(`zone/${d.zone_id}`,d.zone_code):tr('Zone atanmadı')}</td><td>${badge(d.criticality)}</td><td>${completed?`${badge('completed')}${completed.stale_items.length?tr('<small>Yeniden değerlendirme gerekli</small>'):''}`:badge(tr('Değerlendirilmedi'))}</td></tr>`;}).join('')):empty(tr('Bu kapsamda varlık yok.'));
}
// Conduit listesini iki uç zone, yön, protokol ve ayrı seviye profilleriyle gösterir.
function conduitTable(conduits){
  return conduits.length?table(['Conduit',tr('Zone ilişkisi'),tr('Protokol / Port'),'SL-A','SL-T'],conduits.map(c=>`<tr><td>${otLink(`conduit/${c.id}`,c.code,'record-link mono')}<small>${e(c.name)}</small></td><td>${e(c.source_code)} ${c.direction==='bidirectional'?'↔':'→'} ${e(c.target_code)}</td><td>${e(c.protocols)}</td><td>${profileSummary(c.levels.latest.achieved)}<small>${profileStatus(c.levels.latest.achieved)}</small></td><td>${profileSummary(c.levels.latest.target)}<small>${profileStatus(c.levels.latest.target)}</small></td></tr>`).join('')):empty(tr('Henüz conduit kaydı yok.'));
}

// Atama ve sahiplik seçimlerinde yalnızca aktif kullanıcıları sunar; sunucu atamayı ayrıca doğrular.
async function users(){return (await api('/users')).filter(u=>u.active);}
// Bulgu formunda cihaz, zone ve conduit seçimlerini tür:kimlik biçiminde birleştirir.
function scopeOptions(){return [...data.devices.filter(d=>d.active).map(d=>[`device:${d.id}`,msg`Cihaz · ${d.asset_code}`]),...data.zones.map(z=>[`zone:${z.id}`,`Zone · ${z.code}`]),...data.conduits.map(c=>[`conduit:${c.id}`,`Conduit · ${c.code}`])];}
// SUC seçimine bağlı zone formunu açar; düzenlemede eski sürümü ve değişiklik gerekçesini gönderir.
async function zoneForm(target){
  if(!data.systems.length)throw new Error(tr('Önce sistem kapsamı oluşturun.'));
  const z=data.zones.find(z=>z.id===Number(target.dataset.id));const people=await users();
  modal(z?tr('Zone düzenle'):tr('Zone oluştur'),select('system_id',tr('Sistem kapsamı'),optionPairs(data.systems,'id','name'),z?.system_id)+input('code',tr('Zone kodu'),z?.code||'','required maxlength="60"')+input('name',tr('Zone adı'),z?.name||'','required minlength="3"')+select('owner_id',tr('Sorumlu'),optionPairs(people,'id','name'),z?.owner_id)+textarea('purpose',tr('Ortak güvenlik amacı'),z?.purpose||'','required minlength="3"')+textarea('boundary',tr('Kapsam sınırı ve hariç tutulanlar'),z?.boundary||'','required minlength="3"')+(z?textarea('reason',tr('Değişiklik gerekçesi'),'','required minlength="3"'):''),async form=>{
    const body={...form,system_id:Number(form.system_id),owner_id:Number(form.owner_id),...(z?{version:z.version}:{})};const result=await api(`/ot/zones${z?'/'+z.id:''}`,{method:z?'PATCH':'POST',body});toast(tr('Zone kaydedildi.'));navigate(`ot/zone/${result.id}`);await refresh();
  });
}

// Seçilen sistemin zone’larından iletişim uçlarını oluşturur; protokol ve önlemleri belge olarak kaydeder.
async function conduitForm(target){
  if(data.zones.length<2)throw new Error(tr('Conduit için aynı sistemde en az iki zone oluşturun.'));
  const c=data.conduits.find(c=>c.id===Number(target.dataset.id));const people=await users();
  const dialog=modal(c?tr('Conduit düzenle'):tr('Conduit oluştur'),select('system_id',tr('Sistem kapsamı'),optionPairs(data.systems,'id','name'),c?.system_id)+input('code',tr('Conduit kodu'),c?.code||'','required')+input('name',tr('Conduit adı'),c?.name||'','required minlength="3"')+select('owner_id',tr('Sorumlu'),optionPairs(people,'id','name'),c?.owner_id)+select('source_zone_id',tr('Kaynak zone'),[])+select('target_zone_id',tr('Hedef zone'),[])+select('direction',tr('İletişim yönü'),[['one_way',tr('Kaynak → Hedef')],['bidirectional',tr('Çift yönlü')]],c?.direction)+input('protocols',tr('Protokoller ve portlar'),c?.protocols||'',tr('required minlength="3" placeholder="Örn. HTTPS / TCP 443"'))+textarea('purpose',tr('İletişim amacı'),c?.purpose||'','required minlength="3"')+textarea('controls',tr('Koruma önlemleri ve doğrulanma durumu'),c?.controls||'','required minlength="3"')+(c?textarea('reason',tr('Değişiklik gerekçesi'),'','required minlength="3"'):''),async form=>{
    const body={...form,system_id:Number(form.system_id),owner_id:Number(form.owner_id),source_zone_id:Number(form.source_zone_id),target_zone_id:Number(form.target_zone_id),...(c?{version:c.version}:{})};const result=await api(`/ot/conduits${c?'/'+c.id:''}`,{method:c?'PATCH':'POST',body});toast(tr('Conduit kaydedildi.'));navigate(`ot/conduit/${result.id}`);await refresh();
  });
  const form=dialog.querySelector('form');
  const update=()=>{const zs=data.zones.filter(z=>z.system_id===Number(form.elements.system_id.value));for(const key of ['source_zone_id','target_zone_id']){form.elements[key].innerHTML=zs.map(z=>`<option value="${z.id}">${e(z.code)} · ${e(z.name)}</option>`).join('');form.elements[key].value=c?.[key]||zs[key==='target_zone_id'?1:0]?.id||'';}};
  form.elements.system_id.addEventListener('change',update);update();
}

// Sürümlü kontrol şablonundan cevap alanları üretir; taslak ve tamamlama işlemlerini aynı API akışına gönderir.
async function assessmentForm(target){
  const previous=target.dataset.id?await api(`/ot/assessments/${target.dataset.id}`):null;
  const devices=data.devices.filter(d=>d.active);if(!devices.length)throw new Error(tr('Önce cihaz ekleyin.'));
  const content=select('device_id',tr('İlgili cihaz'),devices.map(d=>[d.id,`${d.asset_code} · ${d.name}`]),previous?.device_id||target.dataset.device)+select('finalize',tr('Kayıt işlemi'),[['false',tr('Taslak kaydet')],['true',tr('Değerlendirmeyi tamamla')]])+msg`<p class="full muted">${e(previous?.template_version||data.template_version)} · Seçilmemiş sonuç uygun sayılmaz. Uygulanamaz sonuçları ayrıca sorumlu onayı bekler.</p>`+(previous?.template||data.controls).map(item=>{const r=previous?.results.find(r=>r.code===item.code);return `<fieldset class="ot-check full"><legend>${e(item.code)} · ${e(tr(item.question))}</legend>${select(`${item.code}_result`,tr('Kontrol sonucu'),[['',tr('Seçiniz')],['suitable',tr('Uygun')],['unsuitable',tr('Uygun değil')],['unknown',tr('Bilinmiyor')],['not_applicable',tr('Uygulanamaz')]],r?.result||'')}${textarea(`${item.code}_note`,tr('Gözlem / Gerekçe'),r?.note||'')}${input(`${item.code}_evidence`,tr('Kanıt notu veya belge referansı'),r?.evidence||'')}</fieldset>`;}).join('');
  const dialog=modal(previous?tr('Kontrol taslağını düzenle'):tr('Cihaz güvenlik kontrolü'),content,async form=>{
    // Boş cevap null olarak gönderilir; bilinmeyen veya seçilmemiş sonuç uygun sonuca çevrilmez.
    const body={device_id:previous?.device_id||Number(form.device_id),version:previous?.version||0,finalize:form.finalize==='true',results:(previous?.template||data.controls).map(c=>({code:c.code,result:form[`${c.code}_result`]||null,note:form[`${c.code}_note`],evidence:form[`${c.code}_evidence`]}))};
    const result=await api(`/ot/assessments${previous?'/'+previous.id:''}`,{method:previous?'PUT':'POST',body});toast(result.status==='pending_review'?tr('Uygulanamaz seçimleri sorumlu onayını bekliyor.'):tr('Kontrol kaydedildi.'));navigate(`ot/assessment/${result.id}`);await refresh();
  });
  dialog.classList.add('ot-wide-dialog');dialog.addEventListener('close',()=>dialog.classList.remove('ot-wide-dialog'),{once:true});
  if(previous)dialog.querySelector('[name=device_id]').disabled=true;
}

export const otActions={
  // Değerlendirilen sistemin sınırı ve sorumlusunu kaydeder.
  'ot-system':async()=>{const people=await users();modal(tr('Sistem kapsamı (SUC)'),input('code',tr('Sistem kodu'),'','required')+input('name',tr('Sistem adı'),'','required minlength="3"')+select('owner_id',tr('Sorumlu'),optionPairs(people,'id','name'))+textarea('boundary',tr('Sistem sınırı, varlık kapsamı ve hariç tutulanlar'),'','required minlength="3"'),async form=>{await api('/ot/systems',{method:'POST',body:{...form,owner_id:Number(form.owner_id)}});toast(tr('Sistem kapsamı oluşturuldu.'));await refresh();});},
  // Yeni veya mevcut zone formunu açar.
  'ot-zone':zoneForm,
  // İki zone arasındaki belgelenmiş iletişim kapsamını düzenler.
  'ot-conduit':conduitForm,
  // Zone üyeliği formunu açar; diğer zone’a atanmış cihazları seçimden çıkarır.
  'ot-members':()=>{
    const zone=scope;const available=data.devices.filter(d=>d.active&&(!d.zone_id||d.zone_id===zone.id));
    const dialog=modal(msg`${zone.code} · Varlık üyeliği`,msg`<p class="full muted">Bir cihazın bu sürümde tek bir birincil zone üyeliği bulunur. Başka zone üyeliği önce eski zone’dan kaldırılmalıdır.</p><div class="full member-options">${available.map(d=>`<label class="checkbox-label"><input type="checkbox" name="member_${d.id}" ${d.zone_id===zone.id?'checked':''}>${e(d.asset_code)} · ${e(d.name)}</label>`).join('')}</div>`+textarea('reason',tr('Üyelik değişikliği gerekçesi'),'','required minlength="3"'),async form=>{
      await api(`/ot/zones/${zone.id}/members`,{method:'PUT',body:{device_ids:available.filter(d=>form[`member_${d.id}`]==='on').map(d=>d.id),version:zone.version,reason:form.reason}});toast(tr('Üyelik kaydedildi. Güvenlik profilleri gözden geçirme bekleyebilir.'));await refresh();
    });return dialog;
  },
  // Yedi FR değerini, gerekçeyi ve referansı yeni SL-A/SL-T revizyonu olarak gönderir.
  'ot-level':target=>{
    // SL formu açılırken kapsam ve son profil tutulur; kayıtta bu sürümler backend tarafından kontrol edilir.
    const currentScope=scope;const kind=target.dataset.type;const previous=currentScope.levels.latest[kind];
    const choices=[['',tr('Belirlenmedi')],...[0,1,2,3,4].map(n=>[n,msg`Seviye ${n}`])];
    modal(`${kind==='achieved'?tr('SL-A · Mevcut değerlendirme'):tr('SL-T · Hedef seviye')} · ${currentScope.code}`,msg`<p class="full muted">${kind==='achieved'?tr('Mevcut kapsam için kanıtla desteklediğiniz seviyeleri kaydedin. Kontrol sayısından seviye türetilmez.'):tr('Hedef seviyeleri risk değerlendirmesine dayanarak belirleyin. Cihaz kritikliği otomatik SL-T oluşturmaz.')} FR1–FR7 sırası korunur.</p>`+data.frs.map((fr,i)=>select(`fr_${i}`,`${fr.code} · ${tr(fr.name)}`,choices,previous?.vector[i]??'')).join('')+select('status',tr('Kayıt durumu'),[['draft',tr('Taslak')],['approved',tr('Değerlendirmeyi onayla')]])+textarea('rationale',kind==='achieved'?tr('Mevcut durum değerlendirmesi ve gerekçe'):tr('Risk değerlendirmesi ve hedef gerekçesi'),'','required minlength="3"')+textarea('reference',kind==='achieved'?tr('Kanıt / Değerlendirme referansı'):tr('Risk değerlendirmesi / Karar referansı'),'',tr('placeholder="Belge numarası, sürüm, tarih veya kanıt notu"')),async form=>{
      const isZone=Boolean(currentScope.member_count!==undefined);await api('/ot/levels',{method:'POST',body:{zone_id:isZone?currentScope.id:null,conduit_id:isZone?null:currentScope.id,sl_type:kind,vector:data.frs.map((_,i)=>form[`fr_${i}`]===''?null:Number(form[`fr_${i}`])),rationale:form.rationale,reference:form.reference,status:form.status,scope_version:currentScope.version,expected_profile_id:previous?.id||null}});toast(tr('Yeni güvenlik seviyesi revizyonu kaydedildi.'));await refresh();
    });
  },
  // Cihazın operasyonel etkisini gerekçesiyle kaydeder; seviye profili üretmez.
  'ot-criticality':target=>{
    const d=data.devices.find(d=>d.id===Number(target.dataset.device));modal(msg`${d.asset_code} · Operasyonel kritiklik`,select('criticality',tr('Kritiklik'),[['unknown',tr('Bilinmiyor')],['low',tr('Düşük')],['medium',tr('Orta')],['high',tr('Yüksek')]],d.criticality)+textarea('rationale',tr('Üretim, güvenlik, çevre veya kalite etkisi gerekçesi'),d.rationale,'required minlength="3"'),async form=>{await api(`/ot/devices/${d.id}/criticality`,{method:'PUT',body:{...form,version:d.security_version}});toast(tr('Kritiklik kaydedildi.'));await refresh();});
  },
  // Cihaz kontrolünü başlatır veya yetkili olunan taslağı sürdürür.
  'ot-assessment':assessmentForm,
  // Uygulanamaz cevaplarının gerekçesini yönetici onayına bağlar.
  'ot-approve-applicability':()=>{const a=detail;modal(tr('Uygulanamaz seçimlerini onayla'),textarea('note',tr('Kapsam dışı seçimlerin gerekçelerine ilişkin onay notu'),'','required minlength="3"'),async form=>{await api(`/ot/assessments/${a.id}/approve-applicability`,{method:'POST',body:{version:a.version,note:form.note}});toast(tr('Uygulanamaz seçimleri onaylandı.'));await refresh();});},
  // Kontrol veya hedef farkından bulgu açar; aynı açık bulgu varsa mevcut kayda yönlenir.
  'ot-finding':target=>{
    const scopes=scopeOptions();if(!scopes.length)throw new Error(tr('Önce bir cihaz veya zone oluşturun.'));
    const fixed=target.dataset.scope;const assessment=target.dataset.assessment;const ctrl=target.dataset.control;const fr=target.dataset.fr;const targetProfile=target.dataset.profile;
    // Aynı kontrol/hedef revizyonu için açık bulgu varsa arayüz mevcut kayda yönlenir; sunucu da mükerrerliği denetler.
    const existing=data.findings.find(f=>!['closed','cancelled'].includes(f.status)&&((ctrl&&f.device_id===Number(fixed?.split(':')[1])&&f.control_code===ctrl)||(fr&&targetProfile&&f.fr_code===fr&&f.target_profile_id===Number(targetProfile))));
    if(existing){navigate(`ot/finding/${existing.id}`);toast(tr('Bu maddeye ait mevcut açık bulgu açıldı.'));return;}
    const dialog=modal(tr('Güvenlik bulgusu oluştur'),select('scope',tr('İlgili kapsam'),scopes,fixed)+input('title',tr('Kısa başlık'),ctrl?msg`${ctrl} · Kontrol eksikliği`:fr?msg`${fr} · Hedef güvenlik seviyesi farkı`:'','required minlength="3"')+textarea('observation',tr('Gözlem ve beklenen düzeltme'),'','required minlength="3"')+msg`<p class="full muted">Öncelik, sorumlu ve hedef tarih IT/OT sorumlusu tarafından aksiyon planında belirlenir.</p>`,async form=>{
      const [kind,id]=(fixed||form.scope).split(':');const result=await api('/ot/findings',{method:'POST',body:{[`${kind}_id`]:Number(id),title:form.title,observation:form.observation,assessment_id:assessment?Number(assessment):null,control_code:ctrl||null,fr_code:fr||null,target_profile_id:targetProfile?Number(targetProfile):null}});toast(tr('Bulgu oluşturuldu.'));navigate(`ot/finding/${result.id}`);await refresh();
    });if(fixed)dialog.querySelector('[name=scope]').disabled=true;
  },
  // Öncelik, atama ve son tarihi gerekçeli aksiyon planı olarak kaydeder.
  'ot-plan':async()=>{
    const f=detail.finding;const people=await users();modal(msg`${code(f.id)} · Aksiyon planı`,select('priority',tr('Öncelik'),[['low',tr('Düşük')],['medium',tr('Orta')],['high',tr('Yüksek')]],f.priority)+select('assigned_to',tr('Aksiyon sorumlusu'),[['',tr('Atama bekliyor')],...optionPairs(people,'id','name')],f.assigned_to||'')+input('due_date',tr('Hedef tarih'),f.due_date||'','type="date"')+textarea('reason',tr('Öncelik, atama ve tarih gerekçesi'),'','required minlength="3"'),async form=>{await api(`/ot/findings/${f.id}/plan`,{method:'PATCH',body:{...form,assigned_to:form.assigned_to?Number(form.assigned_to):null,due_date:form.due_date||null,version:f.version}});toast(tr('Aksiyon planı güncellendi; önceki değerler geçmişte korundu.'));await refresh();});
  },
  // İşlem türüne göre uygulama, doğrulamaya gönderme veya kapatma formunu açar; kanıtı API’ye iletir.
  'ot-finding-action':target=>{
    const f=detail.finding,kind=target.dataset.kind;const titles={work:tr('Aksiyon güncelle'),submit:tr('Doğrulamaya gönder'),verify:tr('Doğrula ve kapat'),return:tr('İşleme döndür'),cancel:tr('Bulguyu iptal et'),reopen:tr('Bulguyu yeniden aç')};
    modal(titles[kind],textarea('note',kind==='verify'?tr('Doğrulama sonucu'):tr('İşlem açıklaması ve gerekçe'),'','required minlength="3"')+textarea('evidence',tr('Kanıt notu veya belge referansı'),'',['submit','verify'].includes(kind)?'required minlength="3"':''),async form=>{await api(`/ot/findings/${f.id}/actions`,{method:'POST',body:{...form,kind,version:f.version}});toast(tr('Bulgu işlemi kaydedildi.'));await refresh();});
  },
};
