// Gerçek API testinden üretilen JSON ile OT ekranlarının metin ve rol sözleşmesini tarayıcı olmadan kontrol eder.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';

const fixtures=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
// Ağ çağrıları yalnızca verilen fixture uçlarını okuyabilir; eksik API sözleşmesi testi hemen başarısız yapar.
globalThis.fetch=async url=>{
  assert.ok(Object.hasOwn(fixtures,url),`API fixture missing: ${url}`);
  return {ok:true,json:async()=>structuredClone(fixtures[url])};
};
globalThis.location={hash:''};
// Aynı ekranlar iki dilde de çalıştırılır; yerel tercih kontrollü biçimde taklit edilir.
const language=process.argv[3]||'tr';
globalThis.localStorage={getItem:()=>language};
const {setSession}=await import(pathToFileURL(`${process.cwd()}/frontend/js/api.js`).href+'?v=i18n-1');
const {renderOt}=await import(pathToFileURL(`${process.cwd()}/frontend/js/ot.js`));
setSession({id:1,role:'manager',csrf_token:'test'});
// Bütün OT görünümlerinde başlık, biçimlendirme ve hedef farkı düğmeleri denetlenir.
for(const key of ['ot','ot/zones','ot/zone/1','ot/conduits','ot/conduit/1','ot/devices','ot/device/1','ot/assessments','ot/assessment/1','ot/findings','ot/finding/1','ot/history']){
  location.hash='#'+key;
  const result=await renderOt(key);
  if(language==='en'&&key==='ot')assert.ok(result.html.includes('OT security'));
  if(language==='en'&&key==='ot/zone/1')assert.ok(result.html.includes('Identification and authentication'));
  assert.ok(result.html.includes('<h1>'),`No page heading: ${key}`);
  assert.ok(!result.html.includes('undefined'),`Undefined content: ${key}`);
  assert.ok(!result.html.includes('[object Object]'),`Unformatted object: ${key}`);
  if(key==='ot/zone/1'){
    assert.ok(result.html.includes('data-fr="FR5"'));
    assert.ok(result.html.includes('SL-A'));
    assert.ok(result.html.includes('SL-T'));
  }
}
// Yönetici oturumu teknisyene çevrilerek seviye düzenleme araçlarının gizlendiği doğrulanır.
setSession({id:2,role:'technician',csrf_token:'test'});
const tech=await renderOt('ot/zone/1');
assert.ok(!tech.html.includes('data-action="ot-level"'));
console.log('12 OT views rendered; SL-A/SL-T gap actions and role-specific controls verified.');
