# Fiziksel bağlantı değişimlerinin atomik, geçmişi koruyan servis akışı.
import hashlib
import json
from backend.db.database import now, transaction
from backend.errors import require


# Bağlantı değişimini doğrulama, geçmiş ve tekrar istek korumasıyla tek veritabanı işlemi içinde uygular.
def change_connection(db, payload, user):
    data = payload.model_dump()
    # Aynı request_key ile gelen isteğin içeriğini de karşılaştırmak için kararlı bir özet üretilir.
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    with transaction(db):
        # Ağ kesintisi sonrası aynı istek tekrarlanırsa ikinci değişiklik yerine önceki sonuç döner.
        cached = db.execute("SELECT * FROM request_keys WHERE user_id=? AND request_key=?", (user["id"], data["request_key"])).fetchone()
        if cached:
            require(cached["payload_hash"] == fingerprint, "Bu işlem anahtarı başka bir istek için kullanıldı.")
            return json.loads(cached["response_json"])
        interface = db.execute("SELECT i.*,d.active device_active FROM network_interfaces i JOIN devices d ON d.id=i.device_id WHERE i.id=?", (data["interface_id"],)).fetchone()
        require(interface is not None, "Arayüz bulunamadı.", 404)
        require(interface["active"] and interface["device_active"], "Kullanım dışı arayüze bağlantı kurulamaz.")
        # Kullanıcının gördüğü bağlantı hâlâ geçerli mi kontrol edilir; başkasının değişikliği sessizce ezilmez.
        current = db.execute("SELECT * FROM connections WHERE interface_id=? AND ended_at IS NULL", (data["interface_id"],)).fetchone()
        require((current["id"] if current else None) == data["expected_connection_id"], "Bağlantı başka bir işlemle değişti. Güncel kaydı tekrar açın.")
        if data["kind"] == "create":
            require(current is None, "Bu arayüz zaten bağlı.")
        else:
            require(current is not None, "Değiştirilecek aktif bağlantı bulunamadı.")
        # Bağlantı işlemi bir arızaya bağlanacaksa aynı cihaza ve açık arızaya ait olmalıdır.
        if data["incident_id"]:
            incident = db.execute("SELECT * FROM incidents WHERE id=?", (data["incident_id"],)).fetchone()
            require(incident is not None and incident["device_id"] == interface["device_id"], "Arıza aynı cihaza ait olmalıdır.")
            require(incident["status"] not in ("resolved", "cancelled"), "Kapalı arızaya yeni bağlantı işlemi eklenemez.")
        # Sonlandırma dışındaki işlemlerde hedef uçlar, kablo ve işlem türüne özgü değişim kuralları denetlenir.
        if data["kind"] != "terminate":
            require(data["port_id"] is not None and data["cable_id"] is not None, "Port ve kablo seçin.", 422)
            port = db.execute("SELECT p.*,d.active device_active FROM switch_ports p JOIN devices d ON d.id=p.device_id WHERE p.id=?", (data["port_id"],)).fetchone()
            cable = db.execute("SELECT * FROM cables WHERE id=?", (data["cable_id"],)).fetchone()
            require(port is not None and cable is not None, "Port veya kablo bulunamadı.", 404)
            require(port["suitability"] == "suitable" and port["device_active"], "Hedef port kullanıma uygun değil.")
            require(cable["active"], "Kablo kullanım dışı.")
            require(not current or (current["port_id"], current["cable_id"]) != (data["port_id"], data["cable_id"]), "Bağlantıda değişiklik yapılmadı.")
            if data["kind"] == "move":
                require(current["port_id"] != data["port_id"] and current["cable_id"] == data["cable_id"], "Port taşıma işleminde yalnızca port değişmelidir.")
            if data["kind"] == "replace_cable":
                require(current["port_id"] == data["port_id"] and current["cable_id"] != data["cable_id"], "Kablo değişiminde port aynı kalmalıdır.")
        # Eski bağlantı silinmez: bitiş zamanı yazılır, gerekiyorsa yeni bağlantı ayrı kayıt olarak açılır.
        stamp = now()
        if current:
            db.execute("UPDATE connections SET ended_at=? WHERE id=?", (stamp, current["id"]))
        new_id = None
        if data["kind"] != "terminate":
            new_id = db.execute("INSERT INTO connections(interface_id,port_id,cable_id,started_at,created_by) VALUES (?,?,?,?,?)", (data["interface_id"], data["port_id"], data["cable_id"], stamp, user["id"])).lastrowid
        # Eski/yeni kayıt kimlikleriyle gerekçe saklanır; yeni bağlantı eski saha doğrulamasını devralmaz.
        change_id = db.execute("INSERT INTO connection_changes(old_connection_id,new_connection_id,kind,reason,actor_id,incident_id,created_at) VALUES (?,?,?,?,?,?,?)", (current["id"] if current else None, new_id, data["kind"], data["reason"], user["id"], data["incident_id"], stamp)).lastrowid
        result = {"change_id": change_id, "connection_id": new_id}
        # Başarılı yanıt aynı transaction içinde saklanır; işlem veya tekrar koruması yarım kalmaz.
        db.execute("INSERT INTO request_keys VALUES (?,?,?,?)", (user["id"], data["request_key"], fingerprint, json.dumps(result)))
        return result
