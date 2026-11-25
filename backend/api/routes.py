# Çekirdek API: oturum, envanter, bağlantı, saha doğrulaması, arıza ve rapor verileri.
from datetime import datetime, timedelta, timezone
import hmac
import ipaddress
import json
import re
import secrets
from fastapi import APIRouter, Depends, Request, Response
from backend.db.database import connect, now, rows, transaction
from backend.errors import require
from backend.security import hash_password, verify_password, token_hash
from backend.schemas import (Login, DeviceInput, DeviceUpdate, LocationInput, InterfaceInput,
    CableInput, ConnectionInput, VerificationInput, PortInput, IncidentInput,
    TransitionInput, AssignmentInput, NoteInput, UserInput)
from backend.services import queries
from backend.services.connections import change_connection

router = APIRouter(prefix="/api")


# İstek boyunca kullanılan bağlantıyı açar; FastAPI bağımlılığı sona erdiğinde finally ile kapatır.
def database(request: Request):
    db = connect(request.app.state.db_path)
    try:
        yield db
    finally:
        db.close()


# Çerezdeki oturumu, süresini ve aktif hesabı doğrular; veri değiştiren isteklerde ayrıca CSRF belirtecini kontrol eder.
def authenticated(request: Request, db=Depends(database)):
    token = request.cookies.get("portatlas_session", "")
    session = db.execute("""SELECT u.id,u.username,u.name,u.role,s.csrf_token FROM sessions s
        JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>? AND u.active=1""", (token_hash(token), now())).fetchone()
    require(session is not None, "Oturum açmanız gerekiyor.", 401, "unauthorized")
    # Okuma isteklerinde oturum yeterlidir; yazma isteklerinde çerez yanında bağımsız CSRF doğrulaması aranır.
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        require(hmac.compare_digest(request.headers.get("X-CSRF-Token", ""), session["csrf_token"]), "Oturum doğrulaması başarısız. Sayfayı yenileyin.", 403, "csrf_failed")
    return dict(session)


# Oturum doğrulamasının üzerine yönetici rolü kontrolü ekler; arayüzde düğmeyi gizlemek tek başına yetkilendirme değildir.
def manager(user=Depends(authenticated)):
    require(user["role"] == "manager", "Bu işlem için IT/OT sorumlusu yetkisi gerekiyor.", 403, "forbidden")
    return user


# Sunucunun belirlediği tablodan kimlikle kayıt okur; bulunamayan kayıtları ortak 404 hatasına dönüştürür.
def get_record(db, table, id):
    # Tablo adları yalnızca sunucu sabitlerinden gelir; istek verisi tablo adı olarak kullanılmaz.
    record = db.execute(f"SELECT * FROM {table} WHERE id=?", (id,)).fetchone()
    require(record is not None, "Kayıt bulunamadı.", 404, "not_found")
    return dict(record)


# Değişikliğin önceki/sonraki değerlerini, gerekçesini ve yapan kişiyi aynı işlem akışında denetim günlüğüne ekler.
def audit(db, entity, id, action, before, after, reason, actor):
    db.execute("INSERT INTO audit_events(entity_type,entity_id,action,before_json,after_json,reason,actor_id,created_at) VALUES (?,?,?,?,?,?,?,?)",
               (entity, id, action, json.dumps(before, ensure_ascii=False), json.dumps(after, ensure_ascii=False), reason, actor, now()))


# Giriş denemelerini sınırlar, parolayı doğrular ve süreli oturumla CSRF belirteci üretir.
@router.post("/auth/login")
def login(data: Login, request: Request, response: Response, db=Depends(database)):
    scope = request.client.host if request.client else "local"
    # Son beş dakikadaki giriş denemeleri istemci adresi bazında sayılır; başarısız denemeler de sayaca dahildir.
    threshold = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    with transaction(db):
        db.execute("DELETE FROM login_attempts WHERE attempted_at<?", (threshold,))
        require(db.execute("SELECT COUNT(*) FROM login_attempts WHERE scope=?", (scope,)).fetchone()[0] < 15, "Çok fazla giriş denemesi. Beş dakika sonra tekrar deneyin.", 429, "rate_limited")
        db.execute("INSERT INTO login_attempts(scope,attempted_at) VALUES (?,?)", (scope, now()))
    user = db.execute("SELECT * FROM users WHERE username=? AND active=1", (data.username,)).fetchone()
    # Olmayan hesapta da scrypt çalıştırılır; yanıt süresinden hesabın varlığını anlamak zorlaştırılır.
    valid = verify_password(data.password, user["password_hash"] if user else request.app.state.dummy_hash)
    require(user is not None and valid, "Giriş bilgilerinizi kontrol edin.", 401, "invalid_credentials")
    # Oturum ve CSRF için birbirinden bağımsız rastgele değerler üretilir; sunucuda oturumun özeti tutulur.
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()
    with transaction(db):
        db.execute("DELETE FROM sessions WHERE expires_at<?", (now(),))
        db.execute("INSERT INTO sessions VALUES (?,?,?,?)", (token_hash(token), user["id"], csrf, expires))
    # HttpOnly JavaScript erişimini, SameSite çapraz site gönderimini sınırlar; Secure seçeneği HTTPS kurulumuna bağlıdır.
    response.set_cookie("portatlas_session", token, httponly=True, samesite="strict", secure=request.app.state.secure_cookie, max_age=28800)
    return {"id": user["id"], "name": user["name"], "role": user["role"], "csrf_token": csrf}


# Sunucudaki oturum kaydını siler ve tarayıcı çerezini kaldırır; eski belirteç tekrar kullanılamaz.
@router.post("/auth/logout")
def logout(request: Request, response: Response, user=Depends(authenticated), db=Depends(database)):
    db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash(request.cookies.get("portatlas_session", "")),))
    response.delete_cookie("portatlas_session")
    return {"ok": True}


# Geçerli kullanıcıyı ve demo işaretini döndürür; sayfa yenilendiğinde arayüz oturumunu buradan kurar.
@router.get("/auth/me")
def me(user=Depends(authenticated), db=Depends(database)):
    demo = db.execute("SELECT value FROM settings WHERE key='demo' AND value='true'").fetchone()
    return {**user, "demo": bool(demo)}


# Konum ağacını giriş yapmış kullanıcılara sunar.
@router.get("/locations")
def list_locations(user=Depends(authenticated), db=Depends(database)):
    return queries.locations(db)


# Üst konumla tür sırasını doğrular; tesis → bölge → hat → istasyon hiyerarşisini korur.
@router.post("/locations", status_code=201)
def create_location(data: LocationInput, user=Depends(manager), db=Depends(database)):
    with transaction(db):
        levels = ["facility", "area", "line", "station"]
        if data.parent_id:
            parent = get_record(db, "locations", data.parent_id)
            require(levels.index(data.kind) == levels.index(parent["kind"]) + 1, "Konum sırası tesis, bölge, hat, istasyon olmalıdır.")
        else:
            require(data.kind == "facility", "En üst konum tesis olmalıdır.")
        id = db.execute("INSERT INTO locations(code,name,kind,parent_id) VALUES (?,?,?,?)", (data.code, data.name, data.kind, data.parent_id)).lastrowid
        audit(db, "location", id, "create", None, data.model_dump(), "Konum oluşturuldu", user["id"])
    return {"id": id}


# Arama, cihaz türü, konum ve kullanım filtrelerinden parametreli sorgu oluşturur.
@router.get("/devices")
def list_devices(q: str = "", device_type: str = "", location_id: int | None = None, active: str = "all", user=Depends(authenticated), db=Depends(database)):
    data = rows(db, """SELECT d.*,l.name location_name,
    (SELECT COUNT(*) FROM network_interfaces i JOIN connections c ON c.interface_id=i.id AND c.ended_at IS NULL WHERE i.device_id=d.id) connection_count
    FROM devices d JOIN locations l ON l.id=d.location_id ORDER BY d.asset_code""")
    ids = None
    if location_id:
        ids = {r["id"] for r in rows(db, "WITH RECURSIVE tree AS (SELECT id FROM locations WHERE id=? UNION ALL SELECT l.id FROM locations l JOIN tree ON l.parent_id=tree.id) SELECT id FROM tree", (location_id,))}
    matching_cables = set()
    if q:
        matching_cables = {c["device_id"] for c in queries.connections(db) if q.casefold() in c["cable_label"].casefold()}
    return [d for d in data if (not q or q.casefold() in (d["asset_code"]+d["name"]+d["location_name"]).casefold() or d["id"] in matching_cables) and (not device_type or d["device_type"] == device_type) and (ids is None or d["location_id"] in ids) and (active == "all" or d["active"] == (active == "true"))]


# Cihazı oluşturur; switch seçilmişse belirtilen sayıda fiziksel portu da aynı transaction içinde ekler.
@router.post("/devices", status_code=201)
def create_device(data: DeviceInput, user=Depends(manager), db=Depends(database)):
    with transaction(db):
        get_record(db, "locations", data.location_id)
        stamp = now()
        id = db.execute("INSERT INTO devices(asset_code,name,device_type,location_id,brand,model,description,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)", (data.asset_code, data.name, data.device_type, data.location_id, data.brand, data.model, data.description, stamp, stamp)).lastrowid
        if data.device_type == "switch":
            db.executemany("INSERT INTO switch_ports(device_id,number) VALUES (?,?)", [(id, n) for n in range(1, data.port_count+1)])
        audit(db, "device", id, "create", None, data.model_dump(), "Cihaz oluşturuldu", user["id"])
    return {"id": id}


# Sürüm eşleşmesini kontrol ederek cihazı günceller; konum değişimini geçmişe yazar, aktif bağlantılı cihazı arşivlemez.
@router.patch("/devices/{id}")
def update_device(id: int, data: DeviceUpdate, user=Depends(manager), db=Depends(database)):
    with transaction(db):
        old = get_record(db, "devices", id)
        require(old["version"] == data.version, "Cihaz değişti. Güncel kaydı açın.")
        require(old["device_type"] == data.device_type, "Cihaz türü sonradan değiştirilemez.")
        get_record(db, "locations", data.location_id)
        if not data.active:
            require(not db.execute("SELECT 1 FROM connections c LEFT JOIN network_interfaces i ON i.id=c.interface_id LEFT JOIN switch_ports p ON p.id=c.port_id WHERE c.ended_at IS NULL AND (i.device_id=? OR p.device_id=?)", (id,id)).fetchone(), "Aktif bağlantısı olan cihaz kullanım dışına alınamaz.")
        if old["location_id"] != data.location_id:
            db.execute("INSERT INTO device_location_events(device_id,old_location_id,new_location_id,actor_id,reason,created_at) VALUES (?,?,?,?,?,?)", (id,old["location_id"],data.location_id,user["id"],data.reason,now()))
        db.execute("UPDATE devices SET asset_code=?,name=?,location_id=?,brand=?,model=?,description=?,active=?,version=version+1,updated_at=? WHERE id=?", (data.asset_code,data.name,data.location_id,data.brand,data.model,data.description,int(data.active),now(),id))
        audit(db,"device",id,"update",old,data.model_dump(),data.reason,user["id"])
    return {"id": id}


# Cihazın arayüzlerini, bağlantılarını, arızalarını ve geçmişini tek dijital pasaport yanıtında toplar.
@router.get("/devices/{id}/passport")
def passport(id: int, user=Depends(authenticated), db=Depends(database)):
    device = get_record(db, "devices", id)
    return {"device": device, "locations": queries.locations(db),
            "interfaces": rows(db,"SELECT * FROM network_interfaces WHERE device_id=?",(id,)),
            "connections": queries.connections(db,"i.device_id=? AND c.ended_at IS NULL",(id,)),
            "history": queries.history(db,id),
            "incidents": [n for n in queries.incidents(db) if n["device_id"]==id]}


# Arayüzleri bağlı oldukları cihaz koduyla listeler; fiziksel bağlantı için seçilebilir uçları sağlar.
@router.get("/interfaces")
def interfaces(user=Depends(authenticated), db=Depends(database)):
    return rows(db,"SELECT i.*,d.asset_code,c.id connection_id FROM network_interfaces i JOIN devices d ON d.id=i.device_id LEFT JOIN connections c ON c.interface_id=i.id AND c.ended_at IS NULL ORDER BY d.asset_code,i.name")


# Arayüzün aktif makineye ait olduğunu kontrol eder; IP ve MAC biçimlerini doğruladıktan sonra kaydeder.
@router.post("/interfaces",status_code=201)
def create_interface(data: InterfaceInput, user=Depends(manager), db=Depends(database)):
    with transaction(db):
        device = get_record(db,"devices",data.device_id)
        require(device["device_type"]=="machine" and device["active"],"Arayüz kullanımda olan bir makineye ait olmalıdır.")
        if data.ip:
            try:
                ipaddress.ip_address(data.ip)
            except ValueError:
                require(False,"Geçerli bir IP adresi girin.",422)
        mac = data.mac.upper().replace("-",":")
        require(not mac or bool(re.fullmatch(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}",mac)),"Geçerli bir MAC adresi girin.",422)
        id = db.execute("INSERT INTO network_interfaces(device_id,name,ip,mac) VALUES (?,?,?,?)",(data.device_id,data.name,data.ip,mac)).lastrowid
        audit(db,"interface",id,"create",None,data.model_dump(),"Arayüz oluşturuldu",user["id"])
    return {"id":id}


# Kabloları mevcut kullanım bilgileriyle listeler; arayüzün uygun kablo seçimini destekler.
@router.get("/cables")
def cables(user=Depends(authenticated),db=Depends(database)):
    return rows(db,"SELECT k.*,c.id connection_id FROM cables k LEFT JOIN connections c ON c.cable_id=k.id AND c.ended_at IS NULL ORDER BY k.label")


# Benzersiz etiketli kablo kaydı oluşturur ve oluşturma olayını denetim günlüğüne ekler.
@router.post("/cables",status_code=201)
def create_cable(data:CableInput,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        id=db.execute("INSERT INTO cables(label,cable_type) VALUES (?,?)",(data.label,data.cable_type)).lastrowid
        audit(db,"cable",id,"create",None,data.model_dump(),"Kablo oluşturuldu",user["id"])
    return {"id":id}


# Cihazın switch olduğunu doğrular; portları kayıtlı aktif bağlantılarıyla eşleştirir.
@router.get("/switches/{id}/ports")
def ports(id:int,user=Depends(authenticated),db=Depends(database)):
    device=get_record(db,"devices",id)
    require(device["device_type"]=="switch","Bu cihaz bir switch değil.",422)
    connected={c["port_id"]:c for c in queries.connections(db,"p.device_id=? AND c.ended_at IS NULL",(id,))}
    return {"device":device,"ports":[{**p,"connection":connected.get(p["id"])} for p in rows(db,"SELECT * FROM switch_ports WHERE device_id=? ORDER BY number",(id,))]}


# Portun uygunluk durumunu sürüm kontrolüyle günceller; mevcut fiziksel bağlantıyı kendiliğinden sonlandırmaz.
@router.patch("/ports/{id}")
def update_port(id:int,data:PortInput,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        old=get_record(db,"switch_ports",id)
        require(old["version"]==data.version,"Port bilgisi değişti. Paneli yenileyin.")
        db.execute("UPDATE switch_ports SET suitability=?,version=version+1 WHERE id=?",(data.suitability,id))
        audit(db,"port",id,"suitability",old,data.model_dump(),data.reason,user["id"])
    return {"id":id}


# Bağlantıları cihaz, kablo, port ve son saha doğrulamasıyla birleştirir; filtre değerleri parametre olarak bağlanır.
@router.get("/connections")
def connections(user=Depends(authenticated),db=Depends(database)):
    return queries.connections(db)


# Bağlantı işlem isteğini ortak servise aktarır; kurallar ve atomik güncelleme servis katmanında uygulanır.
@router.post("/connection-changes")
def change(data:ConnectionInput,user=Depends(authenticated),db=Depends(database)):
    return change_connection(db,data,user)


# Bağlantı değişim günlüğünü eski/yeni uç bilgileriyle listeler.
@router.get("/changes")
def changes(user=Depends(authenticated),db=Depends(database)):
    return queries.history(db)


# Yalnızca sonlandırılmamış bağlantıya yeni saha doğrulaması ekler; önceki kontrol sonuçlarını silmez.
@router.post("/connections/{id}/verifications",status_code=201)
def verify(id:int,data:VerificationInput,user=Depends(authenticated),db=Depends(database)):
    with transaction(db):
        c=get_record(db,"connections",id)
        require(c["ended_at"] is None,"Sonlandırılmış bağlantı doğrulanamaz. Güncel bağlantıyı açın.")
        db.execute("INSERT INTO field_verifications(connection_id,result,note,actor_id,created_at) VALUES (?,?,?,?,?)",(id,data.result,data.note,user["id"],now()))
    return {"ok":True}


# Arıza listesini kayıtlı cihaz ve sorumlu bilgileriyle döndürür.
@router.get("/incidents")
def list_incidents(user=Depends(authenticated),db=Depends(database)):
    return queries.incidents(db)


# Aktif cihaz için arıza açar ve ilk oluşturma olayını kaydeder.
@router.post("/incidents",status_code=201)
def create_incident(data:IncidentInput,user=Depends(authenticated),db=Depends(database)):
    with transaction(db):
        device=get_record(db,"devices",data.device_id)
        require(device["active"],"Kullanım dışı cihaz için arıza açılamaz.")
        id=db.execute("INSERT INTO incidents(device_id,title,description,priority,created_by,created_at) VALUES (?,?,?,?,?,?)",(data.device_id,data.title,data.description,data.priority,user["id"],now())).lastrowid
        audit(db,"incident",id,"create",None,data.model_dump(),"Arıza açıldı",user["id"])
    return {"id":id}


# Arıza kaydını müdahaleler, denetim olayları ve ilişkili bağlantı değişimleriyle birlikte getirir.
@router.get("/incidents/{id}")
def incident_detail(id:int,user=Depends(authenticated),db=Depends(database)):
    incident=get_record(db,"incidents",id)
    return {"incident":incident,"interventions":rows(db,"SELECT n.*,u.name actor_name FROM interventions n JOIN users u ON u.id=n.actor_id WHERE incident_id=? ORDER BY n.id",(id,)),
            "events":rows(db,"SELECT a.*,u.name actor_name FROM audit_events a JOIN users u ON u.id=a.actor_id WHERE entity_type='incident' AND entity_id=? ORDER BY a.id",(id,)),
            "changes":[c for c in queries.history(db) if c["incident_id"]==id]}


# Aktif kullanıcıya görev atar; sürüm ve arıza durumu kontrolleri eski formdan yapılan değişikliği engeller.
@router.post("/incidents/{id}/assign")
def assign(id:int,data:AssignmentInput,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        old=get_record(db,"incidents",id)
        target=get_record(db,"users",data.user_id)
        require(target["active"],"Pasif hesaba atama yapılamaz.")
        require(old["version"]==data.version,"Arıza değişti. Güncel kaydı açın.")
        require(old["status"] not in ("resolved","cancelled"),"Kapalı arıza yeniden atanamaz.")
        db.execute("UPDATE incidents SET assigned_to=?,version=version+1 WHERE id=?",(data.user_id,id))
        audit(db,"incident",id,"assign",{"assigned_to":old["assigned_to"]},{"assigned_to":data.user_id},"Sorumlu atandı",user["id"])
    return {"ok":True}


# Yöneticinin veya atanmış teknisyenin işlem yapabildiğini doğrular.
def may_work(incident,user):
    require(user["role"]=="manager" or incident["assigned_to"]==user["id"],"Yalnızca size atanan arızada işlem yapabilirsiniz.",403,"forbidden")


# Yetkili kişinin açık arızaya saha notu eklemesini sağlar; not tek başına arızayı çözülmüş yapmaz.
@router.post("/incidents/{id}/interventions",status_code=201)
def intervention(id:int,data:NoteInput,user=Depends(authenticated),db=Depends(database)):
    with transaction(db):
        incident=get_record(db,"incidents",id)
        may_work(incident,user)
        require(incident["status"] not in ("resolved","cancelled"),"Kapalı arızaya müdahale eklenemez.")
        db.execute("INSERT INTO interventions(incident_id,note,actor_id,created_at) VALUES (?,?,?,?)",(id,data.note,user["id"],now()))
    return {"ok":True}


# İzinli arıza durum geçişlerini uygular; çözümde saha kontrolü, yeniden açmada güncel durum bilgileri kullanılır.
@router.post("/incidents/{id}/transitions")
def transition(id:int,data:TransitionInput,user=Depends(authenticated),db=Depends(database)):
    with transaction(db):
        old=get_record(db,"incidents",id)
        may_work(old,user)
        require(old["version"]==data.version,"Arıza değişti. Güncel kaydı açın.")
        # Durum makinesi yalnızca tanımlı arıza geçişlerini kabul eder; istemcinin gönderdiği her durum uygulanmaz.
        allowed={"open":{"investigating","cancelled"},"investigating":{"waiting","resolved","cancelled"},"waiting":{"investigating","cancelled"},"resolved":{"open"},"cancelled":set()}
        require(data.status in allowed[old["status"]],"Bu durum geçişine izin verilmiyor.")
        if data.status=="cancelled":
            require(user["role"]=="manager","Arızayı yalnızca sorumlu iptal edebilir.",403)
        if data.status=="investigating":
            require(old["assigned_to"] is not None,"Önce bir sorumlu atayın.")
        if data.status=="resolved":
            require(data.verified,"Arızayı çözmek için saha kontrolünü onaylayın.",422)
        resolution=data.reason if data.status=="resolved" else old["resolution"]
        resolved=now() if data.status=="resolved" else (None if data.status=="open" else old["resolved_at"])
        db.execute("UPDATE incidents SET status=?,resolution=?,resolved_at=?,version=version+1 WHERE id=?",(data.status,resolution,resolved,id))
        audit(db,"incident",id,"transition",old,{"status":data.status,"resolution":resolution,"verified":data.verified},data.reason,user["id"])
    return {"ok":True}


# Hesapları arayüze gerekli alanlarla döndürür; parola özetleri yanıtın parçası değildir.
@router.get("/users")
def users(user=Depends(authenticated),db=Depends(database)):
    return rows(db,"SELECT id,name,username,role,active FROM users ORDER BY name")


# Yönetici tarafından yeni hesap oluşturulurken parolayı özetler; rolü doğrulanmış istek modelinden alır.
@router.post("/users",status_code=201)
def create_user(data:UserInput,user=Depends(manager),db=Depends(database)):
    with transaction(db):
        id=db.execute("INSERT INTO users(username,name,password_hash,role,created_at) VALUES (?,?,?,?,?)",(data.username,data.name,hash_password(data.password),data.role,now())).lastrowid
        audit(db,"user",id,"create",None,{"username":data.username,"role":data.role},"Hesap oluşturuldu",user["id"])
    return {"id":id}


# Gösterge sayılarını kayıtlı envanter, bağlantı ve arızalardan hesaplar; canlı ağ taraması yapmaz.
@router.get("/dashboard")
def dashboard(user=Depends(authenticated),db=Depends(database)):
    cs=queries.connections(db)
    ns=queries.incidents(db)
    device_counts={r["device_type"]:r["total"] for r in rows(db,"SELECT device_type,COUNT(*) total FROM devices WHERE active=1 GROUP BY device_type")}
    port_counts={r["suitability"]:r["total"] for r in rows(db,"SELECT suitability,COUNT(*) total FROM switch_ports GROUP BY suitability")}
    total=sum(port_counts.values())
    occupancy={"used":len(cs),"free":total-len(cs),"total":total,"faulty":port_counts.get("faulty",0),"disabled":port_counts.get("disabled",0)}
    trend=rows(db,"SELECT substr(created_at,1,10) day,COUNT(*) total FROM incidents GROUP BY day ORDER BY day DESC LIMIT 7")
    return {"devices":device_counts,"open_incidents":sum(n["status"] not in ("resolved","cancelled") for n in ns),
            "pending":sum(c["verification"]=="pending" for c in cs),"mismatches":sum(c["verification"]=="mismatch" for c in cs),
            "occupancy":occupancy,"incidents":ns[:5],"changes":queries.history(db)[:5],"trend":list(reversed(trend)),
            "my_incidents":sum(n["assigned_to"]==user["id"] and n["status"] not in ("resolved","cancelled") for n in ns)}
