# Regresyon testleri: geçici verilerle iş kuralları, yetkiler ve API sözleşmesi doğrulanır.
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.db.database import closing_connection, initialize
from scripts.manage import seed_demo


# Her test için ayrı geçici veritabanı oluşturur; gerçek proje kayıtları testlerden etkilenmez.
@pytest.fixture
def app(tmp_path):
    path=tmp_path/"test.db"
    seed_demo(path)
    return create_app(path)


# Test kullanıcısıyla giriş yapar ve sonraki yazma isteklerine CSRF başlığını ekler.
def login(client,username="admin"):
    r=client.post("/api/auth/login",json={"username":username,"password":"PortAtlas2026!"})
    assert r.status_code==200,r.text
    client.headers["X-CSRF-Token"]=r.json()["csrf_token"]


# Test istemcisini yönetici oturumuyla hazırlar; istekler gerçek FastAPI uygulama akışından geçer.
@pytest.fixture
def client(app):
    with TestClient(app) as client:
        login(client)
        yield client


# Bağlantı taşıma senaryosu için geçerli temel istek üretir; testler ilgili alanları değiştirir.
def change(**overrides):
    return {"kind":"move","interface_id":1,"expected_connection_id":1,"port_id":8,
            "cable_id":1,"reason":"Eski portta fiziksel hasar", "request_key":str(uuid.uuid4()),**overrides}


# Oturumsuz erişim, eksik CSRF ve teknisyenin yönetici işlemi yapması reddedilmelidir.
def test_authentication_csrf_and_technician_authorization(app):
    with TestClient(app) as c:
        assert c.get('/api/devices').status_code==401
        login(c,'teknisyen')
        assert c.post('/api/cables',json={"label":"NEW"}).status_code==403
        c.headers.pop('X-CSRF-Token')
        assert c.post('/api/connection-changes',json=change()).status_code==403


# Gösterge sayıları veritabanından gelmeli; farklı switch port sayıları doğru görünmelidir.
def test_demo_has_real_metrics_and_variable_port_counts(client):
    dashboard=client.get('/api/dashboard').json()
    assert dashboard['devices']=={'machine':5,'switch':2}
    assert dashboard['occupancy']['total']==40
    assert dashboard['occupancy']['used']==5
    assert len(client.get('/api/switches/6/ports').json()['ports'])==16


# Taşıma geçmişi korunmalı, yeni bağlantı yeniden doğrulama beklemeli ve tekrar istek ikinci işlem üretmemelidir.
def test_move_history_verification_and_retry(client):
    assert client.post('/api/connections/1/verifications',json={"result":"verified","note":"İlk saha kontrolü"}).status_code==201
    data=change()
    first=client.post('/api/connection-changes',json=data)
    assert first.status_code==200,first.text
    assert client.post('/api/connection-changes',json=data).json()==first.json()
    passport=client.get('/api/devices/1/passport').json()
    assert passport['connections'][0]['port_number']==8
    assert passport['connections'][0]['verification']=='pending'
    assert passport['history'][0]['old_port']==5
    assert passport['history'][0]['new_port']==8
    assert len(passport['history'])==2
    assert client.post('/api/connection-changes',json={**data,'reason':'Başka bir işlem'}).status_code==409
    assert client.post('/api/connections/1/verifications',json={"result":"verified","note":"Eski bağlantı"}).status_code==409


# Dolu, arızalı veya devre dışı hedef reddedilirken mevcut bağlantı korunmalıdır.
@pytest.mark.parametrize('port_id,cable_id',[(3,1),(12,1),(24,1),(8,2)])
def test_unavailable_target_does_not_end_old_connection(client,port_id,cable_id):
    data=change(port_id=port_id,cable_id=cable_id)
    # create on unconnected Ethernet-2 to exercise cable uniqueness independently of move semantics.
    if cable_id==2:
        data=change(kind='create',interface_id=6,expected_connection_id=None,port_id=8,cable_id=2)
    response=client.post('/api/connection-changes',json=data)
    assert response.status_code==409,response.text
    passport=client.get('/api/devices/1/passport').json()
    assert passport['connections'][0]['port_number']==5
    assert len(passport['history'])==1


# İşlem ortasında hata oluşursa eski bağlantının kapanması da geri alınmalıdır.
def test_failure_after_old_connection_closed_rolls_back(app,client):
    # Fail the history write after the service has closed/inserted connections.
    with closing_connection(app.state.db_path) as db:
        db.execute("CREATE TRIGGER fail_change BEFORE INSERT ON connection_changes BEGIN SELECT RAISE(ABORT,'injected failure'); END")
    assert client.post('/api/connection-changes',json=change()).status_code==409
    p=client.get('/api/devices/1/passport').json()
    assert p['connections'][0]['id']==1
    assert p['connections'][0]['port_number']==5
    with closing_connection(app.state.db_path) as db:
        assert db.execute('SELECT COUNT(*) FROM connections').fetchone()[0]==5
        assert db.execute('SELECT COUNT(*) FROM request_keys').fetchone()[0]==0


# İki eşzamanlı yazıcı aynı porta bağlanmaya çalıştığında en fazla biri başarılı olmalıdır.
def test_two_writers_competing_for_same_port(app):
    # Ayrı oturum ve bağlantıyla aynı hedef porta eşzamanlı yazma denemesi yapar.
    def attempt(payload):
        with TestClient(app) as c:
            login(c)
            return c.post('/api/connection-changes',json=payload).status_code
    payloads=[change(),change(interface_id=2,expected_connection_id=2,cable_id=2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(attempt,payloads))
    assert sorted(results)==[200,409]
    with closing_connection(app.state.db_path) as db:
        assert db.execute('SELECT COUNT(*) FROM connections WHERE ended_at IS NULL').fetchone()[0]==5
        assert db.execute('SELECT COUNT(*) FROM connections WHERE ended_at IS NULL AND port_id=8').fetchone()[0]==1


# Eski bağlantı kimliği ve zaten bağlı arayüzle gelen çakışmalı istekler reddedilmelidir.
def test_stale_connection_and_occupied_interface_rejected(client):
    assert client.post('/api/connection-changes',json=change(expected_connection_id=999)).status_code==409
    assert client.post('/api/connection-changes',json=change(kind='create')).status_code==409


# Kablo değişimi ve sonlandırma türleri geçmişi koruyarak doğru bağlantı durumunu üretmelidir.
def test_replace_cable_and_terminate(client):
    r=client.post('/api/connection-changes',json=change(kind='replace_cable',port_id=5,cable_id=6))
    assert r.status_code==200,r.text
    next_id=r.json()['connection_id']
    r=client.post('/api/connection-changes',json=change(kind='terminate',expected_connection_id=next_id,port_id=None,cable_id=None))
    assert r.status_code==200,r.text
    assert client.get('/api/devices/1/passport').json()['connections']==[]


# Aktif bağlantı arşivlemeyi engellemeli; cihaz kodu büyük/küçük harf farkıyla tekrarlanamamalıdır.
def test_device_archive_and_case_insensitive_unique_code(client):
    device=client.get('/api/devices/1/passport').json()['device']
    data={k:device[k] for k in ('asset_code','name','device_type','location_id','brand','model','description','version')}
    assert client.patch('/api/devices/1',json={**data,'active':False,'reason':'Kullanım dışı'}).status_code==409
    assert client.post('/api/devices',json={'asset_code':'cnc-014','name':'Tekrarlı','device_type':'machine','location_id':4}).status_code==409


# Port arızalı olarak işaretlenince kayıtlı fiziksel bağlantı kendiliğinden silinmemelidir.
def test_occupied_faulty_port_keeps_connection(client):
    assert client.patch('/api/ports/5',json={'suitability':'faulty','version':1,'reason':'Fiziksel hasar'}).status_code==200
    port=client.get('/api/switches/5/ports').json()['ports'][4]
    assert port['suitability']=='faulty'
    assert port['connection']['asset_code']=='CNC-014'


# Arıza yaşam döngüsü ve atanan teknisyenin işlem sınırı birlikte doğrulanır.
def test_incident_full_lifecycle_and_assignee_boundary(app,client):
    with TestClient(app) as technician:
        login(technician,'teknisyen')
        # Manager-assigned incident cannot be manipulated by another technician.
        assert technician.post('/api/incidents/3/transitions',json={'status':'open','version':1,'reason':'Tekrar görüldü'}).status_code==403
        n=technician.get('/api/incidents/1').json()['incident']
        assert technician.post('/api/incidents/1/transitions',json={'status':'investigating','version':n['version'],'reason':'İnceleme başladı'}).status_code==200
        assert technician.post('/api/incidents/1/interventions',json={'note':'Kablo ve port sahada incelendi'}).status_code==201
        assert technician.post('/api/incidents/1/transitions',json={'status':'resolved','version':2,'reason':'Port değişti','verified':False}).status_code==422
        assert technician.post('/api/incidents/1/transitions',json={'status':'resolved','version':2,'reason':'Port değişti ve doğrulandı','verified':True}).status_code==200
        assert technician.post('/api/incidents/1/transitions',json={'status':'open','version':3,'reason':'Sorun tekrar görüldü'}).status_code==200
    detail=client.get('/api/incidents/1').json()
    assert detail['incident']['status']=='open'
    assert detail['incident']['resolution']=='Port değişti ve doğrulandı'
    assert len(detail['interventions'])==1
    assert len(detail['events'])==3
    assert client.get('/api/devices/1/passport').json()['connections'][0]['verification']=='pending'


# Başka cihazın arızası bağlantı değişimine bağlanamamalıdır.
def test_wrong_device_incident_cannot_link_to_connection(client):
    assert client.post('/api/connection-changes',json=change(incident_id=2)).status_code==409


# Konum, envanter ve isteğe bağlı IP alanlarının oluşturma/doğrulama akışı kontrol edilir.
def test_inventory_location_and_optional_ip(client):
    assert client.post('/api/locations',json={'code':'BAD','name':'Yanlış','kind':'station','parent_id':1}).status_code==409
    result=client.post('/api/devices',json={'asset_code':'NEW-001','name':'Yeni makine','device_type':'machine','location_id':4})
    assert result.status_code==201
    id=result.json()['id']
    assert client.post('/api/interfaces',json={'device_id':id,'name':'Ethernet-1'}).status_code==201
    assert client.post('/api/interfaces',json={'device_id':id,'name':'Ethernet-1'}).status_code==409
    assert client.post('/api/interfaces',json={'device_id':id,'name':'Ethernet-2','ip':'not-ip'}).status_code==422


# Çıkış sonrası eski oturum çerezi API erişimi sağlayamamalıdır.
def test_logout_revokes_session(client):
    assert client.post('/api/auth/logout').status_code==200
    assert client.get('/api/auth/me').status_code==401


# Şema hazırlığı tekrarlanabilir olmalı; alınan yedek geçerli ve tutarlı SQLite veritabanı olmalıdır.
def test_migrations_idempotent_and_backup_valid(app,tmp_path):
    initialize(app.state.db_path)
    dest=tmp_path/'backup.db'
    with closing_connection(app.state.db_path) as db,sqlite3.connect(dest) as backup:
        db.backup(backup)
        assert backup.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert backup.execute('SELECT COUNT(*) FROM devices').fetchone()[0]==7


# Paralel okuma istekleri ve kablo etiketiyle arama ortak sözleşmeyi korumalıdır.
def test_parallel_browser_reads_and_cable_search(app):
    with TestClient(app) as c:
        login(c)
        # Aynı oturumla farklı uçlara eşzamanlı okuma isteği göndererek paralel tarayıcı yüklemesini taklit eder.
        def read(path):
            response=c.get(path)
            assert response.status_code==200,response.text
            return response.json()
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(read,['/api/devices?q=KBL-0087','/api/locations','/api/interfaces','/api/cables']))
        assert [d['asset_code'] for d in results[0]]==['CNC-014']


# Pasif hesaba ait önceden açılmış oturum da erişim sağlayamamalıdır.
def test_passive_user_existing_session_is_denied(app,client):
    with closing_connection(app.state.db_path) as db:
        db.execute('UPDATE users SET active=0 WHERE id=1')
    assert client.get('/api/devices').status_code==401
