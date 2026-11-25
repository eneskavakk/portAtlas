# Regresyon testleri: geçici verilerle iş kuralları, yetkiler ve API sözleşmesi doğrulanır.
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.db.database import closing_connection,initialize,now
from scripts.manage import seed_demo
from test_core import login,change


# OT testlerine izole demo veritabanı ve uygulama örneği sağlar.
@pytest.fixture
def ot_app(tmp_path):
    path=tmp_path/'ot.db'
    seed_demo(path)
    return create_app(path)


# OT test istemcisini yönetici hesabıyla oturum açmış olarak hazırlar.
@pytest.fixture
def c(ot_app):
    with TestClient(ot_app) as client:
        login(client)
        yield client


# OT oluşturma yanıtının başarılı olduğunu doğrular ve yeni kayıt kimliğini döndürür.
def create(c,url,body):
    response=c.post('/api/ot'+url,json=body)
    assert response.status_code==201,response.text
    return response.json()['id']


# Testte kullanılacak sınırları belirli örnek SUC kaydını oluşturur.
def system(c,code='SYS-01'):
    return create(c,'/systems',{'code':code,'name':'Üretim kontrol sistemi','boundary':'Hat 2 ve bakım erişimi; kurumsal IT kapsam dışı.','owner_id':1})


# Belirtilen sistem için örnek güvenlik zone’u oluşturur.
def zone(c,sid,code='Z-01'):
    return create(c,'/zones',{'system_id':sid,'code':code,'name':'Hat kontrol bölgesi','purpose':'Ortak kontrol güvenliği ihtiyacı','boundary':'Üretim kontrol varlıkları','owner_id':1})


# İki zone arasındaki conduit isteğini üretir; geçersiz uç testleri alanları değiştirebilir.
def conduit(c,sid,z1,z2,**extra):
    return {'system_id':sid,'code':'C-01','name':'Bakım erişim yolu','source_zone_id':z1,'target_zone_id':z2,
            'direction':'one_way','protocols':'HTTPS / TCP 443','purpose':'Yetkili bakım erişimi','controls':'Ara sunucu ve erişim onay süreci','owner_id':1,**extra}


# Seviye testleri için gerekçeli ve referanslı örnek profil isteğini üretir.
def level(zid,kind='target',**extra):
    return {'zone_id':zid,'sl_type':kind,'vector':[2,2,2,1,2,1,2],'rationale':'Kapsam için kayıtlı risk değerlendirmesi gerekçesi',
            'reference':'RA-2026-001 / 31.10.2026','scope_version':1,'status':'approved',**extra}


# Sekiz kontrol sorusuna temel cevap seti üretir; tek tek sonuçlar test ihtiyacına göre değiştirilebilir.
def answers(**changes):
    return [{'code':f'OT{i:02}','result':'suitable','note':'Etiket ve gözlem kaydı yeterli.','evidence':'SAHA-01',**changes.get(f'OT{i:02}',{})} for i in range(1,9)]


# API genel görünümünden ilgili zone’u seçer; test doğrudan veritabanı yerine görünen sözleşmeyi okur.
def get_zone(c,id):
    return next(z for z in c.get('/api/ot/overview').json()['zones'] if z['id']==id)


# Cihaza bağlı temel güvenlik bulgusu oluşturur; testlerde kontrol veya hedef ilişkisi eklenebilir.
def finding(c,**extra):
    return create(c,'/findings',{'device_id':1,'title':'Bakım erişim sorumlusu belirsiz','observation':'Yetkili erişim kaydı ve sorumluluk gözden geçirilmeli.',**extra})


# Eksik güvenlik kayıtları için sistem seviye, kritiklik veya uygun kontrol sonucu uydurmamalıdır.
def test_no_invented_levels_criticality_or_checks(c):
    d=c.get('/api/ot/overview').json()
    assert d['counts']['unzoned']==7
    assert d['counts']['unknown_criticality']==7
    sid=system(c);zid=zone(c,sid)
    assert get_zone(c,zid)['levels']['latest']=={'achieved':None,'target':None}
    assert get_zone(c,zid)['levels']['gaps']==[None]*7
    device=c.get('/api/ot/devices/1').json()
    assert device['security']['criticality']=='unknown'
    assert device['assessments']==[]


# Zone üyeliği fiziksel konumdan bağımsız olmalı; tek birincil üyelik ve sürüm kuralları korunmalıdır.
def test_zone_membership_independent_of_location_and_unique(c):
    sid=system(c);z1=zone(c,sid);z2=zone(c,sid,'Z-02')
    assert c.put(f'/api/ot/zones/{z1}/members',json={'device_ids':[1,3],'version':1,'reason':'Ortak güvenlik ihtiyacı'}).status_code==200
    assert c.get('/api/devices/1/passport').json()['device']['location_id']==4
    assert c.get('/api/devices/3/passport').json()['device']['location_id']==6
    assert c.put(f'/api/ot/zones/{z2}/members',json={'device_ids':[1],'version':1,'reason':'Çifte üyelik'}).status_code==409
    assert c.put(f'/api/ot/zones/{z1}/members',json={'device_ids':[],'version':1,'reason':'Eski sürüm'}).status_code==409
    assert get_zone(c,z1)['member_count']==2


# Conduit farklı zone uçlarına ve aynı sistem kapsamına bağlı olmalıdır.
def test_conduits_require_distinct_zones_in_same_system(c):
    sid=system(c);z1=zone(c,sid);z2=zone(c,sid,'Z-02');other=zone(c,system(c,'SYS-02'),'Z-03')
    assert c.post('/api/ot/conduits',json=conduit(c,sid,z1,z1)).status_code==422
    assert c.post('/api/ot/conduits',json=conduit(c,sid,z1,other)).status_code==409
    cid=create(c,'/conduits',conduit(c,sid,z1,z2))
    d=c.get('/api/ot/overview').json()['conduits'][0]
    assert d['id']==cid
    assert d['levels']['latest']['achieved'] is None


# SL-A/SL-T ayrı tutulmalı, FR farkları doğru hesaplanmalı ve önceki revizyonlar değişmemelidir.
def test_separate_sl_a_and_t_gap_and_immutable_revisions(c,ot_app):
    zid=zone(c,system(c))
    aid=create(c,'/levels',level(zid,'achieved',vector=[1,2,1,0,1,1,2],reference='EVID-01 test ve inceleme referansı'))
    tid=create(c,'/levels',level(zid))
    levels=get_zone(c,zid)['levels']
    assert levels['gaps']==[1,0,1,1,1,0,0]
    assert levels['latest']['achieved']['id']==aid
    assert levels['latest']['target']['id']==tid
    new_id=create(c,'/levels',level(zid,expected_profile_id=tid,vector=[3]*7))
    assert c.post('/api/ot/levels',json=level(zid,expected_profile_id=tid)).status_code==409
    history=get_zone(c,zid)['levels']['history']
    assert len(history)==3
    assert next(p for p in history if p['id']==tid)['vector']==[2,2,2,1,2,1,2]
    assert get_zone(c,zid)['levels']['latest']['target']['id']==new_id


# Yanlış uzunluk, aralık dışı değer, bool veya eksik değer içeren onaylı profil reddedilmelidir.
@pytest.mark.parametrize('vector',[[None]*7,[1]*6,[1]*8,[5]*7,[True]*7])
def test_invalid_or_incomplete_approved_level_is_rejected(c,vector):
    zid=zone(c,system(c))
    assert c.post('/api/ot/levels',json=level(zid,vector=vector)).status_code==422


# Bilinmeyen değer seviye 0 sayılmamalı; referanssız profil onaylanmamalıdır.
def test_unknown_is_not_level_zero_and_no_reference_no_approval(c):
    zid=zone(c,system(c))
    assert c.post('/api/ot/levels',json=level(zid,reference='')).status_code==422
    id=create(c,'/levels',level(zid,vector=[0,None,0,None,None,None,None],status='draft',reference=''))
    p=get_zone(c,zid)['levels']
    assert p['latest']['target']['vector']==[0,None,0,None,None,None,None]
    assert p['gaps']==[None]*7


# Zone üyeliği değişince eski kapsamın profilleri güncelliğini kaybetmelidir.
def test_membership_change_marks_profiles_outdated(c):
    zid=zone(c,system(c))
    create(c,'/levels',level(zid))
    assert c.put(f'/api/ot/zones/{zid}/members',json={'device_ids':[1],'version':1,'reason':'Yeni varlık eklendi'}).status_code==200
    assert get_zone(c,zid)['levels']['latest']['target']['stale'] is True
    assert c.post('/api/ot/levels',json=level(zid)).status_code==409


# Bağlantı ve port değişimi kapsam görüntüsünü değiştirerek profil inceleme uyarısı üretmelidir.
def test_connection_and_port_change_mark_profiles_outdated(c):
    zid=zone(c,system(c))
    c.put(f'/api/ot/zones/{zid}/members',json={'device_ids':[1],'version':1,'reason':'Kontrol kapsamı'})
    create(c,'/levels',level(zid,scope_version=2))
    assert c.patch('/api/ports/5',json={'suitability':'faulty','version':1,'reason':'Fiziksel hasar'}).status_code==200
    assert get_zone(c,zid)['levels']['latest']['target']['stale']


# Eksik kontrol tamamlanmamalı; bilinmeyen sonuç uygun yerine geçmemelidir.
def test_assessment_missing_answers_and_unknown_not_suitable(c):
    assert c.post('/api/ot/assessments',json={'device_id':1,'results':[],'finalize':True}).status_code==422
    result=answers(OT01={'result':'unknown','note':''})
    assert c.post('/api/ot/assessments',json={'device_id':1,'results':result,'finalize':True}).status_code==422
    id=create(c,'/assessments',{'device_id':1,'results':answers(OT01={'result':'unknown','note':'Sorumlu bilgisi henüz alınmadı'}),'finalize':True})
    assessment=c.get(f'/api/ot/assessments/{id}').json()
    assert assessment['results'][0]['result']=='unknown'
    assert assessment['status']=='completed'
    assert c.put(f'/api/ot/assessments/{id}',json={'device_id':1,'version':1,'results':answers()}).status_code==409


# Teknisyenin taslak sahipliği korunmalı; uygulanamaz cevabı yönetici onayına gitmelidir.
def test_technician_draft_ownership_and_na_manager_approval(c,ot_app):
    draft=create(c,'/assessments',{'device_id':1,'results':[]})
    with TestClient(ot_app) as tech:
        login(tech,'teknisyen')
        assert tech.put(f'/api/ot/assessments/{draft}',json={'device_id':1,'version':1,'results':answers()}).status_code==403
        id=create(tech,'/assessments',{'device_id':1,'results':answers(OT04={'result':'not_applicable','note':'Bu cihazda uzaktan erişim fonksiyonu bulunmuyor'}),'finalize':True})
        assert tech.post(f'/api/ot/assessments/{id}/approve-applicability',json={'version':1,'note':'Onay denemesi'}).status_code==403
    assert c.get(f'/api/ot/assessments/{id}').json()['status']=='pending_review'
    assert c.post(f'/api/ot/assessments/{id}/approve-applicability',json={'version':1,'note':'Kapsam dışı gerekçesi gözden geçirildi.'}).status_code==200
    a=c.get(f'/api/ot/assessments/{id}').json()
    assert a['status']=='completed' and a['approved_by']==1


# Port değişimi bütün sonuçları silmeden yalnızca ilgili kontrol maddelerini yeniden incelemeye işaretlemelidir.
def test_port_move_only_invalidates_related_controls(c):
    id=create(c,'/assessments',{'device_id':1,'results':answers(),'finalize':True})
    assert c.post('/api/connection-changes',json=change()).status_code==200
    a=c.get(f'/api/ot/assessments/{id}').json()
    assert a['stale_items']==['OT02','OT06']
    assert a['results']==answers()
    assert a['status']=='completed'


# Mükerrer açık bulgu ve farklı cihaza ait değerlendirme ilişkisi reddedilmelidir.
def test_findings_duplicate_and_assessment_device_binding(c):
    aid=create(c,'/assessments',{'device_id':1,'results':answers(OT01={'result':'unsuitable'}),'finalize':True})
    fid=finding(c,assessment_id=aid,control_code='OT01')
    assert c.post('/api/ot/findings',json={'device_id':2,'title':'Yanlış cihaz','observation':'Bağlantı denemesi','assessment_id':aid,'control_code':'OT01'}).status_code==409
    assert c.post('/api/ot/findings',json={'device_id':1,'title':'Mükerrer bulgu','observation':'Aynı kontrol maddesi','assessment_id':aid,'control_code':'OT01'}).status_code==409
    assert c.get(f'/api/ot/findings/{fid}').json()['finding']['priority_reviewed']==0


# Bulgu planlama isteğini testin istediği alanlarla oluşturur.
def plan(c,id,**extra):
    return c.patch(f'/api/ot/findings/{id}/plan',json={'priority':'high','assigned_to':2,'due_date':'2026-01-01','reason':'Acil iyileştirme ve sorumlu ataması','version':1,**extra})


# Bulgu işlem isteğinde tür ve beklenen sürümü ortak biçimde gönderir.
def act(c,id,kind,version,**extra):
    return c.post(f'/api/ot/findings/{id}/actions',json={'kind':kind,'version':version,'note':'İşlem ve kontrol açıklaması','evidence':'EVID-2026-01',**extra})


# Bulgu uygulama ve doğrulama adımlarından geçmeli; yüksek öncelikte farklı kişi doğrulaması aranmalıdır.
def test_finding_verified_lifecycle_and_high_priority_separation(c,ot_app):
    fid=finding(c)
    assert plan(c,fid).status_code==200
    assert act(c,fid,'verify',2).status_code==409
    with TestClient(ot_app) as tech:
        login(tech,'teknisyen')
        assert act(tech,fid,'work',2).status_code==200
        assert act(tech,fid,'submit',3,evidence='').status_code==422
        assert act(tech,fid,'submit',3).status_code==200
        assert act(tech,fid,'verify',4).status_code==403
    assert c.get(f'/api/ot/findings/{fid}').json()['finding']['status']=='awaiting_verification'
    assert act(c,fid,'verify',4).status_code==200
    assert act(c,fid,'reopen',5).status_code==200
    assert len(c.get(f'/api/ot/findings/{fid}').json()['actions'])==4


# Yönetici bile yüksek öncelikli kendi uygulamasını doğrulayamamalıdır.
def test_manager_who_implemented_high_finding_cannot_verify(c):
    fid=finding(c)
    assert plan(c,fid,assigned_to=1).status_code==200
    assert act(c,fid,'work',2).status_code==200
    assert act(c,fid,'submit',3).status_code==200
    assert act(c,fid,'verify',4).status_code==403


# Plan değişiklikleri geçmişte kalmalı; gecikme açık kayıtların hedef tarihinden hesaplanmalıdır.
def test_due_date_and_assignee_history_and_overdue(c):
    fid=finding(c)
    assert plan(c,fid).status_code==200
    assert c.get(f'/api/ot/findings/{fid}').json()['finding']['overdue']
    assert plan(c,fid,version=2,due_date='2099-01-01',reason='Planlı duruş tarihine taşındı').status_code==200
    d=c.get(f'/api/ot/findings/{fid}').json()
    plans=[e for e in d['events'] if e['action']=='plan']
    assert json.loads(plans[-1]['before_json'])['due_date']=='2026-01-01'
    assert json.loads(plans[-1]['after_json'])['due_date']=='2099-01-01'
    assert not d['finding']['overdue']


# Teknisyen kapsam, seviye ve öncelik gibi yönetici kararlarını değiştirememelidir.
def test_technician_cannot_configure_scope_levels_or_priority(c,ot_app):
    zid=zone(c,system(c));fid=finding(c)
    with TestClient(ot_app) as tech:
        login(tech,'teknisyen')
        assert tech.post('/api/ot/levels',json=level(zid)).status_code==403
        assert tech.put(f'/api/ot/zones/{zid}/members',json={'device_ids':[1],'version':1,'reason':'Yetkisiz atama'}).status_code==403
        assert tech.put('/api/ot/devices/1/criticality',json={'criticality':'high','rationale':'Yüksek üretim etkisi','version':0}).status_code==403
        assert plan(tech,fid).status_code==403
        assert act(tech,fid,'work',1).status_code==409


# Cihaz kritikliği belirlemek otomatik SL profili oluşturmamalıdır.
def test_criticality_does_not_assign_security_level(c):
    zid=zone(c,system(c))
    c.put(f'/api/ot/zones/{zid}/members',json={'device_ids':[1],'version':1,'reason':'Kapsam üyeliği'})
    assert c.put('/api/ot/devices/1/criticality',json={'criticality':'high','rationale':'Üretim hattının durması etkisi','version':0}).status_code==200
    assert get_zone(c,zid)['levels']['latest']=={'achieved':None,'target':None}


# FR farkından açılan bulgu aynı kapsamın ilgili hedef revizyonuna bağlanmalıdır.
def test_gap_finding_links_to_matching_target_revision(c):
    sid=system(c);z1=zone(c,sid);z2=zone(c,sid,'Z-02')
    tid=create(c,'/levels',level(z1))
    aid=create(c,'/levels',level(z1,'achieved'))
    body={'zone_id':z1,'title':'FR5 hedef farkı','observation':'Akış kısıtlama önlemleri değerlendirilecek.','fr_code':'FR5','target_profile_id':tid}
    fid=create(c,'/findings',body)
    f=c.get(f'/api/ot/findings/{fid}').json()['finding']
    assert (f['fr_code'],f['target_profile_id'])==('FR5',tid)
    assert c.post('/api/ot/findings',json=body).status_code==409
    assert c.post('/api/ot/findings',json={**body,'zone_id':z2}).status_code==409
    assert c.post('/api/ot/findings',json={**body,'target_profile_id':aid}).status_code==409


# Eski şema OT göçleriyle yükseltilirken mevcut envanter korunmalıdır.
def test_v1_database_upgrades_without_resetting_inventory(tmp_path):
    path=tmp_path/'v1.db'
    path.parent.mkdir(exist_ok=True)
    with closing_connection(path) as db:
        db.execute('CREATE TABLE schema_migrations(version TEXT PRIMARY KEY,applied_at TEXT NOT NULL)')
        db.executescript(Path('backend/db/migrations/001_core.sql').read_text())
        db.execute('INSERT INTO schema_migrations VALUES (?,?)',('001_core.sql',now()))
        db.execute("INSERT INTO users(username,name,password_hash,role,created_at) VALUES ('retained','Korunan hesap','not-used','manager',?)",(now(),))
    initialize(path)
    initialize(path)
    with closing_connection(path) as db:
        assert db.execute("SELECT name FROM users WHERE username='retained'").fetchone()[0]=='Korunan hesap'
        assert db.execute('SELECT COUNT(*) FROM schema_migrations').fetchone()[0]==3
        assert db.execute('SELECT COUNT(*) FROM security_zones').fetchone()[0]==0


# Gerçek API yanıtları Türkçe ve İngilizce OT ekranlarında işlenmeli; rol bazlı işlemler doğru görünmelidir.
@pytest.mark.parametrize('language',['tr','en'])
def test_ot_frontend_renders_real_api_contract(c,tmp_path,language):
    import shutil
    import subprocess
    if not shutil.which('node'):
        pytest.skip('Node is only needed for frontend contract verification.')
    sid=system(c);z1=zone(c,sid);z2=zone(c,sid,'Z-02')
    create(c,'/conduits',conduit(c,sid,z1,z2))
    create(c,'/levels',level(z1,'achieved',vector=[1]*7))
    create(c,'/levels',level(z1,vector=[2]*7))
    create(c,'/assessments',{'device_id':1,'results':answers(),'finalize':True})
    finding(c)
    endpoints=['/api/ot/overview','/api/ot/devices/1','/api/ot/assessments/1','/api/ot/findings/1','/api/ot/history']
    payload={}
    for path in endpoints:
        response=c.get(path)
        assert response.status_code==200,response.text
        payload[path]=response.json()
    fixture=tmp_path/'ot-contract.json'
    fixture.write_text(json.dumps(payload))
    result=subprocess.run(['node','tests/ot_render.mjs',str(fixture),language],text=True,capture_output=True)
    assert result.returncode==0,result.stdout+result.stderr
