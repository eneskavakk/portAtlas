# OT sorgularını zenginleştiren ve değerlendirmelerin güncelliğini hesaplayan iş mantığı.
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from backend.db.database import rows
from backend.errors import require

# FR (Foundational Requirement) sırası, yedi elemanlı SL vektörünün hangi güvenlik alanını temsil ettiğini belirler.
FRS = [
    {'code':'FR1','name':'Kimlik tanımlama ve doğrulama'},
    {'code':'FR2','name':'Kullanım kontrolü'},
    {'code':'FR3','name':'Sistem bütünlüğü'},
    {'code':'FR4','name':'Veri gizliliği'},
    {'code':'FR5','name':'Kısıtlı veri akışı'},
    {'code':'FR6','name':'Olaylara zamanında yanıt'},
    {'code':'FR7','name':'Kaynak kullanılabilirliği'},
]
# Bu sekiz soru PortAtlas başlangıç kontrol listesidir; IEC standardının resmi denetim listesi değildir.
CONTROLS = [
    {'code':'OT01','question':'Cihazın operasyonel sorumlusu belirli mi?'},
    {'code':'OT02','question':'Makine, port ve kablo etiketleri kayıtla tutarlı mı?'},
    {'code':'OT03','question':'Kullanılmayan portların amacı ve uygunluğu gözden geçirildi mi?'},
    {'code':'OT04','question':'Uzaktan erişim durumu ve yetkili sorumlusu biliniyor mu?'},
    {'code':'OT05','question':'Güvenlik bölgesi ve operasyonel kritiklik gözden geçirildi mi?'},
    {'code':'OT06','question':'Son bağlantı değişikliğinin gerekçesi ve yapan kişisi kayıtlı mı?'},
    {'code':'OT07','question':'Ayar yedekleme ve geri dönüş sorumluluğu biliniyor mu?'},
    {'code':'OT08','question':'Cihaza ve ağ dolabına fiziksel erişim kontrolü gözden geçirildi mi?'},
]
# Tamamlanan kontroller şablon kopyası ve sürümüyle saklanır; yeni sorular eski değerlendirmeyi değiştirmez.
TEMPLATE_VERSION='PortAtlas-OT-v1'


# Son tarih karşılaştırmalarında kullanılacak günü İstanbul saat diliminde üretir.
def today():
    return datetime.now(ZoneInfo('Europe/Istanbul')).date().isoformat()


# Cihazın aktif bağlantılarını, zone üyeliğini ve kritiklik sürümünü değerlendirme bağlamı olarak toplar.
def device_context(db,id):
    member=db.execute('SELECT zone_id FROM zone_members WHERE device_id=?',(id,)).fetchone()
    security=db.execute('SELECT * FROM device_security WHERE device_id=?',(id,)).fetchone()
    return {'connections':[r['id'] for r in rows(db,'SELECT c.id FROM connections c JOIN network_interfaces i ON i.id=c.interface_id WHERE i.device_id=? AND c.ended_at IS NULL ORDER BY c.id',(id,))],
            'zone_id':member['zone_id'] if member else None,'criticality_version':security['version'] if security else 0}


# Zone üyelerini ve bağlantı yollarını; conduit için iki uç zone’un bağlamını anlık görüntü olarak toplar.
def scope_context(db,zone_id=None,conduit_id=None):
    if zone_id:
        members=rows(db,'SELECT d.id,d.version,d.active,COALESCE(s.version,0) criticality_version FROM devices d JOIN zone_members m ON m.device_id=d.id LEFT JOIN device_security s ON s.device_id=d.id WHERE m.zone_id=? ORDER BY d.id',(zone_id,))
        # Bağlantı veya port durumu değişince kayıtlı profilin dayandığı bağlam değişmiş olabilir.
        paths=rows(db,'SELECT c.id,c.port_id,p.version FROM connections c JOIN switch_ports p ON p.id=c.port_id JOIN network_interfaces i ON i.id=c.interface_id LEFT JOIN zone_members a ON a.device_id=i.device_id LEFT JOIN zone_members b ON b.device_id=p.device_id WHERE c.ended_at IS NULL AND (a.zone_id=? OR b.zone_id=?) ORDER BY c.id',(zone_id,zone_id))
        return {'members':members,'paths':paths}
    conduit=db.execute('SELECT * FROM security_conduits WHERE id=?',(conduit_id,)).fetchone()
    return {'source':scope_context(db,zone_id=conduit['source_zone_id']), 'target':scope_context(db,zone_id=conduit['target_zone_id']),
            'zone_versions':[r['version'] for r in rows(db,'SELECT version FROM security_zones WHERE id IN (?,?) ORDER BY id',(conduit['source_zone_id'],conduit['target_zone_id']))]}


# SL-A/SL-T geçmişini okur; kapsamı değişmiş profilleri işaretler ve yalnızca onaylı/güncel profillerin FR farklarını hesaplar.
def profiles(db,zone_id=None,conduit_id=None):
    column,id=('zone_id',zone_id) if zone_id else ('conduit_id',conduit_id)
    records=rows(db,f'SELECT p.*,u.name author_name,a.name approver_name FROM security_level_profiles p JOIN users u ON u.id=p.created_by LEFT JOIN users a ON a.id=p.approved_by WHERE p.{column}=? ORDER BY p.id DESC',(id,))
    table='security_zones' if zone_id else 'security_conduits'
    version=db.execute(f'SELECT version FROM {table} WHERE id=?',(id,)).fetchone()['version']
    context=scope_context(db,zone_id,conduit_id)
    for p in records:
        p['vector']=json.loads(p.pop('vector_json'))
        p['stale']=p['scope_version']!=version or json.loads(p.pop('source_context_json'))!=context
    # Mevcut (achieved/SL-A) ve hedef (target/SL-T) revizyonları birbirinden bağımsız seçilir.
    latest={kind:next((p for p in records if p['sl_type']==kind),None) for kind in ('achieved','target')}
    a,t=latest['achieved'],latest['target']
    # Taslak veya eski kapsamdan kalan profil karşılaştırılmaz; bilinmeyen değer güvenli kabul edilmez.
    comparable=bool(a and t and a['status']=='approved' and t['status']=='approved' and not a['stale'] and not t['stale'])
    # FR bazında negatif fark sıfıra çekilir; bu fark bir güvenlik yüzdesi veya sertifikasyon puanı değildir.
    gaps=[None if not comparable or a['vector'][i] is None or t['vector'][i] is None else max(0,t['vector'][i]-a['vector'][i]) for i in range(7)]
    return {'latest':latest,'history':records,'gaps':gaps,'comparable':comparable}


# Bulguya görünen kapsam kodunu ve gecikme bilgisini ekler; kapalı/iptal kayıtları gecikmiş saymaz.
def findings(db):
    data=rows(db,'''SELECT f.*,u.name assignee_name,d.asset_code device_code,z.code zone_code,c.code conduit_code
    FROM security_findings f LEFT JOIN users u ON u.id=f.assigned_to LEFT JOIN devices d ON d.id=f.device_id
    LEFT JOIN security_zones z ON z.id=f.zone_id LEFT JOIN security_conduits c ON c.id=f.conduit_id ORDER BY f.id DESC''')
    for f in data:
        f['scope_code']=f['device_code'] or f['zone_code'] or f['conduit_code']
        f['overdue']=bool(f['due_date'] and f['due_date']<today() and f['status'] not in ('closed','cancelled'))
    return data


# Saklanan şablon ve cevapları açar; bağlantı veya zone/kritiklik değişimine göre ilgili maddeleri yeniden incelemeye işaretler.
def assessment(db,record):
    result=dict(record)
    result['template']=json.loads(result.pop('template_json'))
    result['results']=json.loads(result.pop('results_json'))
    old=json.loads(result.pop('context_json'))
    current=device_context(db,result['device_id'])
    result['stale_items']=[]
    # Geçmiş cevaplar korunur; yalnızca değişen bağlantı/zone bağlamıyla ilgili kontrol kodları işaretlenir.
    if result['status']!='draft':
        if old['connections']!=current['connections']:
            result['stale_items']+=['OT02','OT06']
        if (old['zone_id'],old['criticality_version'])!=(current['zone_id'],current['criticality_version']):
            result['stale_items']+=['OT05']
    return result


# Kontrol kodlarının tekil ve geçerli olmasını denetler; tamamlamada sekiz yanıt ve gerekli açıklamaları zorunlu tutar.
def validate_results(data):
    codes=[r.code for r in data.results]
    allowed={c['code'] for c in CONTROLS}
    require(len(codes)==len(set(codes)) and set(codes)<=allowed,'Kontrol kodları geçersiz veya mükerrer.',422)
    # Taslak eksik kalabilir; tamamlama isteğinde her maddeye sonuç ve gerekli gözlem açıklaması gerekir.
    if data.finalize:
        require(set(codes)==allowed and all(r.result is not None for r in data.results),'Tamamlamak için sekiz maddenin sonucunu seçin.',422)
        for r in data.results:
            require(r.result=='suitable' or len(r.note)>=3,f'{r.code}: uygun olmayan, bilinmeyen veya uygulanamaz sonuç açıklama gerektirir.',422)
