# OT API: SUC, zone/conduit, SL-A/SL-T, kontroller ve doğrulanabilir bulgu iş akışı.
import json
from fastapi import APIRouter, Depends
from backend.api.routes import database, authenticated, manager, get_record, audit
from backend.db.database import now, rows, transaction
from backend.errors import require
from backend.ot_schemas import (SystemInput,ZoneInput,ZoneUpdate,MembershipInput,ConduitInput,ConduitUpdate,
    LevelInput,CriticalityInput,AssessmentInput,ApprovalInput,FindingInput,FindingPlan,FindingAction)
from backend.services import ot

router=APIRouter(prefix='/api/ot',tags=['OT security'])


# Atama veya sahiplik için seçilen hesabın var ve aktif olduğunu doğrular.
def active_user(db,id):
    user=get_record(db,'users',id)
    require(user['active'],'Pasif kullanıcı seçilemez.')
    return user


# İstekteki sürümü son kayıtla karşılaştırır; eski ekranın daha yeni verinin üzerine yazmasını önlemeye yardımcı olur.
def check_version(old,version):
    require(old['version']==version,'Kayıt değişti. Güncel bilgileri açıp tekrar deneyin.')


# OT kapsamlarını, profilleri, cihaz güvenlik bilgilerini ve bulgu sayaçlarını tek genel görünüm yanıtında toplar.
@router.get('/overview')
def overview(user=Depends(authenticated),db=Depends(database)):
    zones=rows(db,'SELECT z.*,s.name system_name,u.name owner_name,(SELECT COUNT(*) FROM zone_members WHERE zone_id=z.id) member_count FROM security_zones z JOIN security_systems s ON s.id=z.system_id JOIN users u ON u.id=z.owner_id ORDER BY z.code')
    conduits=rows(db,'SELECT c.*,a.code source_code,b.code target_code,u.name owner_name FROM security_conduits c JOIN security_zones a ON a.id=c.source_zone_id JOIN security_zones b ON b.id=c.target_zone_id JOIN users u ON u.id=c.owner_id ORDER BY c.code')
    for z in zones:
        z['levels']=ot.profiles(db,zone_id=z['id'])
    for c in conduits:
        c['levels']=ot.profiles(db,conduit_id=c['id'])
    fs=ot.findings(db)
    # Kritiklik kaydı olmayan cihazlar unknown kalır; eksik veriye otomatik düşük risk atanmaz.
    devices=rows(db,'''SELECT d.id,d.asset_code,d.name,d.active,m.zone_id,z.code zone_code,
        COALESCE(s.criticality,'unknown') criticality,COALESCE(s.version,0) security_version,
        COALESCE(s.rationale,'') rationale FROM devices d LEFT JOIN zone_members m ON m.device_id=d.id
        LEFT JOIN security_zones z ON z.id=m.zone_id LEFT JOIN device_security s ON s.device_id=d.id ORDER BY d.asset_code''')
    assessments=[ot.assessment(db,r) for r in rows(db,'SELECT a.*,d.asset_code,u.name author_name FROM ot_assessments a JOIN devices d ON d.id=a.device_id JOIN users u ON u.id=a.author_id ORDER BY a.id DESC')]
    return {'systems':rows(db,'SELECT s.*,u.name owner_name FROM security_systems s JOIN users u ON u.id=s.owner_id ORDER BY s.code'),
        'zones':zones,'conduits':conduits,'devices':devices,'findings':fs,'assessments':assessments,'frs':ot.FRS,
        'controls':ot.CONTROLS,'template_version':ot.TEMPLATE_VERSION,'today':ot.today(),
        'counts':{'zones':len(zones),'conduits':len(conduits),
            'unzoned':sum(d['active'] and not d['zone_id'] for d in devices),
            'open_findings':sum(f['status'] not in ('closed','cancelled') for f in fs),
            'overdue':sum(f['overdue'] for f in fs),
            'unknown_criticality':sum(d['active'] and d['criticality']=='unknown' for d in devices)}}


# Değerlendirilen sistemin (SUC) sınırını ve sahibini oluşturur; güvenlik seviyesi atamaz.
@router.post('/systems',status_code=201)
def create_system(data:SystemInput,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        active_user(db,data.owner_id)
        id=db.execute('INSERT INTO security_systems(code,name,boundary,owner_id,created_at) VALUES (?,?,?,?,?)',(data.code,data.name,data.boundary,data.owner_id,now())).lastrowid
        audit(db,'security_system',id,'create',None,data.model_dump(),'Sistem kapsamı oluşturuldu',user['id'])
    return {'id':id}


# Var olan sistem içinde ortak güvenlik ihtiyacını temsil eden zone oluşturur; fiziksel konumdan bağımsızdır.
@router.post('/zones',status_code=201)
def create_zone(data:ZoneInput,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        get_record(db,'security_systems',data.system_id)
        active_user(db,data.owner_id)
        id=db.execute('INSERT INTO security_zones(system_id,code,name,purpose,boundary,owner_id,created_at) VALUES (?,?,?,?,?,?,?)',
            (data.system_id,data.code,data.name,data.purpose,data.boundary,data.owner_id,now())).lastrowid
        audit(db,'security_zone',id,'create',None,data.model_dump(),'Zone oluşturuldu',user['id'])
    return {'id':id}


# Zone tanımını sürüm ve sistem aidiyeti kontrolüyle günceller; kapsam sürümünü artırır.
@router.patch('/zones/{id}')
def update_zone(id:int,data:ZoneUpdate,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        old=get_record(db,'security_zones',id)
        check_version(old,data.version)
        require(old['system_id']==data.system_id,'Zone başka sisteme taşınamaz; yeni kapsam oluşturun.')
        active_user(db,data.owner_id)
        db.execute('UPDATE security_zones SET code=?,name=?,purpose=?,boundary=?,owner_id=?,version=version+1 WHERE id=?',
            (data.code,data.name,data.purpose,data.boundary,data.owner_id,id))
        audit(db,'security_zone',id,'update',old,data.model_dump(),data.reason,user['id'])
    return {'id':id}


# Aktif cihaz üyeliklerini tek birincil zone kuralıyla değiştirir; eski/yeni üyeleri ve gerekçeyi geçmişe kaydeder.
@router.put('/zones/{id}/members')
def set_members(id:int,data:MembershipInput,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        zone=get_record(db,'security_zones',id)
        check_version(zone,data.version)
        require(len(set(data.device_ids))==len(data.device_ids),'Aynı cihaz iki kez seçilemez.',422)
        for device_id in data.device_ids:
            require(get_record(db,'devices',device_id)['active'],'Kullanım dışı cihaz zone içine atanamaz.')
            other=db.execute('SELECT zone_id FROM zone_members WHERE device_id=? AND zone_id<>?',(device_id,id)).fetchone()
            require(other is None,'Cihaz başka zone içinde. Önce eski üyeliğini gerekçeyle kaldırın.')
        # Üyelik listesi transaction içinde bütünüyle yenilenir; kapsam sürümü arttığı için eski profiller inceleme gerektirebilir.
        old=[m['device_id'] for m in rows(db,'SELECT device_id FROM zone_members WHERE zone_id=? ORDER BY device_id',(id,))]
        db.execute('DELETE FROM zone_members WHERE zone_id=?',(id,))
        db.executemany('INSERT INTO zone_members(device_id,zone_id,assigned_by,assigned_at) VALUES (?,?,?,?)',[(d,id,user['id'],now()) for d in data.device_ids])
        db.execute('UPDATE security_zones SET version=version+1 WHERE id=?',(id,))
        audit(db,'security_zone',id,'membership',old,sorted(data.device_ids),data.reason,user['id'])
    return {'id':id}


# Conduit uçlarının farklı zone’lar olduğunu ve aynı SUC içinde kaldığını doğrular.
def conduit_scope(db,data):
    get_record(db,'security_systems',data.system_id)
    source=get_record(db,'security_zones',data.source_zone_id)
    target=get_record(db,'security_zones',data.target_zone_id)
    require(source['id']!=target['id'],'Conduit iki farklı zone arasında olmalıdır.',422)
    require(source['system_id']==target['system_id']==data.system_id,'Conduit uçları aynı sistem kapsamında olmalıdır.')
    active_user(db,data.owner_id)


# Zone’lar arası iletişim gereksinimini belgeler; gerçek ağ trafiğini veya firewall kurallarını değiştirmez.
@router.post('/conduits',status_code=201)
def create_conduit(data:ConduitInput,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        conduit_scope(db,data)
        id=db.execute('INSERT INTO security_conduits(system_id,code,name,source_zone_id,target_zone_id,direction,protocols,purpose,controls,owner_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            (data.system_id,data.code,data.name,data.source_zone_id,data.target_zone_id,data.direction,data.protocols,data.purpose,data.controls,data.owner_id,now())).lastrowid
        audit(db,'security_conduit',id,'create',None,data.model_dump(),'Conduit oluşturuldu',user['id'])
    return {'id':id}


# İletişim kapsamını sürüm kontrolüyle günceller; conduit’i başka sisteme taşımaya izin vermez.
@router.patch('/conduits/{id}')
def update_conduit(id:int,data:ConduitUpdate,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        old=get_record(db,'security_conduits',id)
        check_version(old,data.version)
        require(data.system_id==old['system_id'],'Conduit başka sisteme taşınamaz.')
        conduit_scope(db,data)
        db.execute('UPDATE security_conduits SET code=?,name=?,source_zone_id=?,target_zone_id=?,direction=?,protocols=?,purpose=?,controls=?,owner_id=?,version=version+1 WHERE id=?',
            (data.code,data.name,data.source_zone_id,data.target_zone_id,data.direction,data.protocols,data.purpose,data.controls,data.owner_id,id))
        audit(db,'security_conduit',id,'update',old,data.model_dump(),data.reason,user['id'])
    return {'id':id}


# SL-A veya SL-T için yeni revizyon ekler; mevcut revizyonu ezmeden kapsam anlık görüntüsünü ve onay bilgisini saklar.
@router.post('/levels',status_code=201)
def create_level(data:LevelInput,user=Depends(manager),db=Depends(database)):
    column,id=('zone_id',data.zone_id) if data.zone_id else ('conduit_id',data.conduit_id)
    table='security_zones' if data.zone_id else 'security_conduits'
    with transaction(db):
        scope=get_record(db,table,id)
        require(scope['version']==data.scope_version,'Kapsam değişti. Güncel zone/conduit kaydını açın.')
        # Son profil kimliği, form açıldıktan sonra başka bir revizyon kaydedilip kaydedilmediğini denetlemek için karşılaştırılır.
        previous=db.execute(f'SELECT * FROM security_level_profiles WHERE {column}=? AND sl_type=? ORDER BY revision DESC LIMIT 1',(id,data.sl_type)).fetchone()
        require((previous['id'] if previous else None)==data.expected_profile_id,'SL profili değişti. Son değerlendirmeyi açın.')
        # Revizyon numarası artar; önceki seviye profili güncellenerek yok edilmez.
        revision=previous['revision']+1 if previous else 1
        approved=data.status=='approved'
        stamp=now()
        # Kayıt anındaki kapsam görüntüsü saklanır; daha sonraki okumada güncel bağlamla karşılaştırılır.
        profile_id=db.execute('''INSERT INTO security_level_profiles(zone_id,conduit_id,sl_type,revision,vector_json,rationale,reference,scope_version,source_context_json,status,created_by,created_at,approved_by,approved_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(data.zone_id,data.conduit_id,data.sl_type,revision,json.dumps(data.vector),data.rationale,data.reference,data.scope_version,
            json.dumps(ot.scope_context(db,data.zone_id,data.conduit_id)),data.status,user['id'],stamp,user['id'] if approved else None,stamp if approved else None)).lastrowid
        audit(db,'security_level',profile_id,'approve' if approved else 'draft',dict(previous) if previous else None,data.model_dump(),data.rationale,user['id'])
    return {'id':profile_id,'revision':revision}


# Cihaz kritikliğini, kontrol geçmişini ve bulgularını getirir; eksik kritiklik unknown olarak gösterilir.
@router.get('/devices/{id}')
def device_security(id:int,user=Depends(authenticated),db=Depends(database)):
    get_record(db,'devices',id)
    member=db.execute('SELECT z.* FROM zone_members m JOIN security_zones z ON z.id=m.zone_id WHERE m.device_id=?',(id,)).fetchone()
    security=db.execute('SELECT * FROM device_security WHERE device_id=?',(id,)).fetchone()
    return {'zone':dict(member) if member else None,'security':dict(security) if security else {'criticality':'unknown','version':0,'rationale':''},
        'levels':ot.profiles(db,zone_id=member['id']) if member else None,
        'assessments':[ot.assessment(db,r) for r in rows(db,'SELECT a.*,u.name author_name FROM ot_assessments a JOIN users u ON u.id=a.author_id WHERE a.device_id=? ORDER BY a.id DESC',(id,))],
        'findings':[f for f in ot.findings(db) if f['device_id']==id]}


# Operasyonel etki değerlendirmesini gerekçesiyle kaydeder; bu değer otomatik SL-A/SL-T üretmez.
@router.put('/devices/{id}/criticality')
def set_criticality(id:int,data:CriticalityInput,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        get_record(db,'devices',id)
        old=db.execute('SELECT * FROM device_security WHERE device_id=?',(id,)).fetchone()
        require((old['version'] if old else 0)==data.version,'Kritiklik değişti. Kaydı yenileyin.')
        db.execute('''INSERT INTO device_security(device_id,criticality,rationale,version,updated_by,updated_at) VALUES (?,?,?,?,?,?)
        ON CONFLICT(device_id) DO UPDATE SET criticality=excluded.criticality,rationale=excluded.rationale,version=excluded.version,updated_by=excluded.updated_by,updated_at=excluded.updated_at''',
        (id,data.criticality,data.rationale,data.version+1,user['id'],now()))
        audit(db,'device_security',id,'criticality',dict(old) if old else None,data.model_dump(),data.rationale,user['id'])
    return {'id':id}


# Kontrol cevaplarını doğrular; taslak sahipliğini korur ve uygulanamaz sonuçları yönetici onayına yönlendirir.
def save_assessment(db,data,user,id=None):
    with transaction(db):
        device=get_record(db,'devices',data.device_id)
        require(device['active'],'Kullanım dışı cihaza yeni değerlendirme yapılamaz.')
        ot.validate_results(data)
        previous=None
        if id:
            previous=get_record(db,'ot_assessments',id)
            check_version(previous,data.version)
            require(previous['status']=='draft','Tamamlanan veya onay bekleyen değerlendirme değiştirilemez. Yeni değerlendirme başlatın.')
            require(previous['device_id']==data.device_id,'Değerlendirme cihazı değiştirilemez.')
            require(user['role']=='manager' or previous['author_id']==user['id'],'Başkasının taslağını düzenleyemezsiniz.',403)
        status='draft'
        # Uygulanamaz seçeneği varsa doğrudan tamamlamak yerine sorumlu onayı bekleyen duruma geçilir.
        if data.finalize:
            status='pending_review' if any(r.result=='not_applicable' for r in data.results) else 'completed'
        stamp=now()
        result_json=json.dumps([r.model_dump() for r in data.results],ensure_ascii=False)
        # Kontrolün hangi bağlantı, zone ve kritiklik bağlamında yapıldığı cevaplarla birlikte saklanır.
        context=json.dumps(ot.device_context(db,data.device_id))
        if id:
            db.execute('UPDATE ot_assessments SET results_json=?,context_json=?,status=?,completed_at=?,version=version+1 WHERE id=?',
                (result_json,context,status,stamp if status=='completed' else None,id))
        else:
            id=db.execute('INSERT INTO ot_assessments(device_id,template_version,template_json,results_json,context_json,status,author_id,created_at,completed_at) VALUES (?,?,?,?,?,?,?,?,?)',
                (data.device_id,ot.TEMPLATE_VERSION,json.dumps(ot.CONTROLS,ensure_ascii=False),result_json,context,status,user['id'],stamp,stamp if status=='completed' else None)).lastrowid
        audit(db,'ot_assessment',id,'save',previous,{'status':status},'Kontrol sonuçları kaydedildi',user['id'])
    return {'id':id,'status':status}


# Yeni cihaz kontrolünü ortak kayıt akışı üzerinden oluşturur.
@router.post('/assessments',status_code=201)
def create_assessment(data:AssessmentInput,user=Depends(authenticated),db=Depends(database)):
    return save_assessment(db,data,user)


# Mevcut kontrol taslağını ortak kayıt akışına gönderir; tamamlanmış değerlendirmeler bu yoldan değiştirilemez.
@router.put('/assessments/{id}')
def update_assessment(id:int,data:AssessmentInput,user=Depends(authenticated),db=Depends(database)):
    return save_assessment(db,data,user,id)


# Kontrol kaydını, saklanmış şablonu ve yeniden değerlendirme gerektiren maddeleri birlikte döndürür.
@router.get('/assessments/{id}')
def get_assessment(id:int,user=Depends(authenticated),db=Depends(database)):
    return ot.assessment(db,get_record(db,'ot_assessments',id))


# Uygulanamaz cevaplarının kapsam gerekçesini yönetici notuyla onaylayarak değerlendirmeyi tamamlar.
@router.post('/assessments/{id}/approve-applicability')
def approve_applicability(id:int,data:ApprovalInput,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        old=get_record(db,'ot_assessments',id)
        check_version(old,data.version)
        require(old['status']=='pending_review','Değerlendirme kapsam dışı onayı beklemiyor.')
        db.execute("UPDATE ot_assessments SET status='completed',completed_at=?,approved_by=?,approval_note=?,version=version+1 WHERE id=?",(now(),user['id'],data.note,id))
        audit(db,'ot_assessment',id,'applicability_approval',{'status':old['status']},{'status':'completed'},data.note,user['id'])
    return {'id':id}


# Cihaz/zone/conduit için bulgu açar; kontrol ve hedef profil bağlarını doğrular, mükerrer açık aksiyonu engeller.
@router.post('/findings',status_code=201)
def create_finding(data:FindingInput,user=Depends(authenticated),db=Depends(database)):
    with transaction(db):
        column,id=next((k,v) for k,v in [('device_id',data.device_id),('zone_id',data.zone_id),('conduit_id',data.conduit_id)] if v is not None)
        table={'device_id':'devices','zone_id':'security_zones','conduit_id':'security_conduits'}[column]
        get_record(db,table,id)
        # Hedef farkı bulgusu rastgele profile bağlanamaz; seçilen onaylı SL-T aynı zone/conduit kapsamına ait olmalıdır.
        if data.target_profile_id:
            profile=get_record(db,'security_level_profiles',data.target_profile_id)
            require(column in ('zone_id','conduit_id') and profile[column]==id and profile['sl_type']=='target' and profile['status']=='approved','Hedef profili aynı zone/conduit kapsamına ait onaylı SL-T olmalıdır.')
            require(data.fr_code is not None,'Hedef farkı bulgusunda temel gereksinim seçin.',422)
            duplicate=db.execute(f"SELECT id FROM security_findings WHERE {column}=? AND target_profile_id=? AND fr_code=? AND status NOT IN ('closed','cancelled')",(id,data.target_profile_id,data.fr_code)).fetchone()
            require(duplicate is None,f"Bu hedef ve FR için açık aksiyon var: OT-{duplicate['id'] if duplicate else ''}.")
        # Kontrolden açılan bulguda cihaz eşleşmesi ve uygun olmayan/bilinmeyen madde sonucu aranır.
        if data.assessment_id:
            a=get_record(db,'ot_assessments',data.assessment_id)
            require(data.device_id==a['device_id'],'Kontrol ve bulgu aynı cihaza ait olmalıdır.')
            require(a['status']!='draft','Önce kontrol sonuçlarını tamamlayın.')
            answers=json.loads(a['results_json'])
            require(any(r['code']==data.control_code and r['result'] in ('unsuitable','unknown') for r in answers),'Bulgu için uygun olmayan veya bilinmeyen bir kontrol maddesi seçin.',422)
        # Aynı kapsam ve kontrol için açık bulgu varsa yeni bir kopya oluşturulmaz.
        if data.control_code:
            require(data.control_code in {c['code'] for c in ot.CONTROLS},'Kontrol kodu geçersiz.',422)
            duplicate=db.execute(f"SELECT id FROM security_findings WHERE {column}=? AND control_code=? AND status NOT IN ('closed','cancelled')",(id,data.control_code)).fetchone()
            require(duplicate is None,f"Bu kapsam ve kontrol için açık bulgu var: OT-{duplicate['id'] if duplicate else ''}. Mevcut kaydı kullanın.")
        fid=db.execute('INSERT INTO security_findings(device_id,zone_id,conduit_id,assessment_id,control_code,fr_code,target_profile_id,title,observation,priority,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (data.device_id,data.zone_id,data.conduit_id,data.assessment_id,data.control_code,data.fr_code,data.target_profile_id,data.title,data.observation,'medium',user['id'],now())).lastrowid
        audit(db,'security_finding',fid,'create',None,data.model_dump(),'Bulgu açıldı; öncelik sorumlu değerlendirmesini bekliyor',user['id'])
    return {'id':fid}


# Bulgunun mevcut durumunu uygulama adımları ve denetim olaylarıyla birlikte döndürür.
@router.get('/findings/{id}')
def finding_detail(id:int,user=Depends(authenticated),db=Depends(database)):
    get_record(db,'security_findings',id)
    finding=next(f for f in ot.findings(db) if f['id']==id)
    return {'finding':finding,'actions':rows(db,'SELECT a.*,u.name actor_name FROM security_finding_actions a JOIN users u ON u.id=a.actor_id WHERE a.finding_id=? ORDER BY a.id',(id,)),
        'events':rows(db,"SELECT a.*,u.name actor_name FROM audit_events a JOIN users u ON u.id=a.actor_id WHERE a.entity_type='security_finding' AND a.entity_id=? ORDER BY a.id",(id,))}


# Öncelik, atanan kişi ve hedef tarihi yönetici kararıyla günceller; önceki plan değerlerini geçmişte korur.
@router.patch('/findings/{id}/plan')
def plan_finding(id:int,data:FindingPlan,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        old=get_record(db,'security_findings',id)
        check_version(old,data.version)
        require(old['status'] not in ('closed','cancelled'),'Kapalı bulgunun planı değiştirilemez.')
        require(old['status']!='awaiting_verification','Doğrulama bekleyen bulguyu önce işleme döndürün.')
        if data.assigned_to:
            active_user(db,data.assigned_to)
        db.execute('UPDATE security_findings SET priority=?,assigned_to=?,due_date=?,priority_reviewed=1,version=version+1 WHERE id=?',
            (data.priority,data.assigned_to,data.due_date.isoformat() if data.due_date else None,id))
        audit(db,'security_finding',id,'plan',old,data.model_dump(mode='json'),data.reason,user['id'])
    return {'id':id}


# Bulgu yaşam döngüsünü, kanıt gerekliliğini ve yüksek öncelikte uygulayan/doğrulayan ayrımını uygular.
@router.post('/findings/{id}/actions')
def action_finding(id:int,data:FindingAction,user=Depends(authenticated),db=Depends(database)):
    with transaction(db):
        old=get_record(db,'security_findings',id)
        check_version(old,data.version)
        kind=data.kind
        # Kapatma, geri gönderme, iptal ve yeniden açma yönetici işlemidir; uygulama yalnızca yetkili sorumluya açıktır.
        if kind in ('verify','return','cancel','reopen'):
            require(user['role']=='manager','Bu işlem sorumlu yetkisi gerektirir.',403)
        else:
            require(old['assigned_to'] is not None,'Önce bir aksiyon sorumlusu atayın.')
            require(user['role']=='manager' or old['assigned_to']==user['id'],'Yalnızca size atanan aksiyonu güncelleyebilirsiniz.',403)
        # Her aksiyon yalnızca izinli başlangıç durumlarında çalışır; örneğin açık bulgu doğrudan kapatılamaz.
        allowed={'work':{'open','in_progress'},'submit':{'in_progress'},'verify':{'awaiting_verification'},
            'return':{'awaiting_verification'},'cancel':{'open','in_progress','awaiting_verification'},'reopen':{'closed'}}
        require(old['status'] in allowed[kind],'Bu durumda seçilen işlem uygulanamaz.')
        # Tamamlamaya gönderme ve doğrulamada kanıt referansı zorunludur; uygulama belgenin içeriğini otomatik denetlemez.
        if kind in ('submit','verify'):
            require(len(data.evidence)>=3,'Tamamlama ve doğrulama için kanıt notu veya belge referansı ekleyin.',422)
        # Yüksek öncelikte işi yapan veya doğrulamaya gönderen kişi kendi çalışmasını doğrulayamaz.
        if kind=='verify' and old['priority']=='high':
            did_work=db.execute("SELECT 1 FROM security_finding_actions WHERE finding_id=? AND actor_id=? AND kind IN ('work','submit')",(id,user['id'])).fetchone()
            require(did_work is None,'Yüksek öncelikte aksiyonu uygulayan kişi doğrulama yapamaz.',403)
        # Yeni durum, aksiyon kaydı ve denetim olayı aynı transaction içinde kalıcılaştırılır.
        status={'work':'in_progress','submit':'awaiting_verification','verify':'closed','return':'in_progress','cancel':'cancelled','reopen':'in_progress'}[kind]
        db.execute('UPDATE security_findings SET status=?,version=version+1 WHERE id=?',(status,id))
        db.execute('INSERT INTO security_finding_actions(finding_id,kind,note,evidence,actor_id,created_at) VALUES (?,?,?,?,?,?)',
            (id,kind,data.note,data.evidence,user['id'],now()))
        audit(db,'security_finding',id,kind,{'status':old['status']},{'status':status},data.note,user['id'])
    return {'id':id,'status':status}


# OT kapsamı, profil, kontrol ve bulgu olaylarını en yeni kayıt başta olacak şekilde listeler.
@router.get('/history')
def ot_history(user=Depends(authenticated),db=Depends(database)):
    return rows(db,"SELECT a.*,u.name actor_name FROM audit_events a JOIN users u ON u.id=a.actor_id WHERE entity_type IN ('security_system','security_zone','security_conduit','security_level','device_security','ot_assessment','security_finding') ORDER BY a.id DESC LIMIT 500")
