-- Ekip hesapları: rol ve aktiflik denetlenir; parola yerine özet saklanır.
CREATE TABLE users (
 id INTEGER PRIMARY KEY, username TEXT NOT NULL COLLATE NOCASE UNIQUE,
 name TEXT NOT NULL, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('manager','technician')),
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)), created_at TEXT NOT NULL
);
-- Süreli oturumlar: belirtecin özeti, kullanıcı ve CSRF değeri birlikte tutulur.
CREATE TABLE sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
 csrf_token TEXT NOT NULL, expires_at TEXT NOT NULL
);
-- İstemci adresine göre giriş denemelerini sayarak kaba kuvvet sınırı uygulanmasını sağlar.
CREATE TABLE login_attempts (id INTEGER PRIMARY KEY, scope TEXT NOT NULL, attempted_at TEXT NOT NULL);
-- Zaman aralığı ve istemciye göre giriş denemesi sayımını hızlandırır.
CREATE INDEX ix_login_attempts ON login_attempts(scope, attempted_at);
-- Demo modu gibi uygulama ayarlarını anahtar/değer biçiminde saklar.
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
-- Fiziksel tesis ağacı; parent_id üst konumu, kind hiyerarşi türünü belirtir.
CREATE TABLE locations (
 id INTEGER PRIMARY KEY, code TEXT NOT NULL COLLATE NOCASE UNIQUE,
 name TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('facility','area','line','station')),
 parent_id INTEGER REFERENCES locations(id), version INTEGER NOT NULL DEFAULT 1,
 UNIQUE(parent_id,name)
);
-- Makine ve switch envanteri; version eski formdan güncellemeyi denetlemek için artırılır.
CREATE TABLE devices (
 id INTEGER PRIMARY KEY, asset_code TEXT NOT NULL COLLATE NOCASE UNIQUE, name TEXT NOT NULL,
 device_type TEXT NOT NULL CHECK(device_type IN ('machine','switch')),
 location_id INTEGER NOT NULL REFERENCES locations(id), brand TEXT NOT NULL DEFAULT '',
 model TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)), version INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
-- Cihazın eski/yeni fiziksel konumunu, gerekçeyi ve yapan kişiyi geçmişte korur.
CREATE TABLE device_location_events (
 id INTEGER PRIMARY KEY, device_id INTEGER NOT NULL REFERENCES devices(id),
 old_location_id INTEGER REFERENCES locations(id), new_location_id INTEGER NOT NULL REFERENCES locations(id),
 actor_id INTEGER NOT NULL REFERENCES users(id), reason TEXT NOT NULL, created_at TEXT NOT NULL
);
-- Makineye ait ağ uçları; arayüz adı aynı cihaz içinde tekrarlanamaz.
CREATE TABLE network_interfaces (
 id INTEGER PRIMARY KEY, device_id INTEGER NOT NULL REFERENCES devices(id), name TEXT NOT NULL,
 mac TEXT NOT NULL DEFAULT '', ip TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1,
 UNIQUE(device_id,name)
);
-- Büyük/küçük harften bağımsız benzersiz kablo etiketi ve kullanım durumu.
CREATE TABLE cables (
 id INTEGER PRIMARY KEY, label TEXT NOT NULL COLLATE NOCASE UNIQUE,
 cable_type TEXT NOT NULL DEFAULT 'CAT6', active INTEGER NOT NULL DEFAULT 1
);
-- Switch içindeki fiziksel portlar; doluluk bağlantıdan, uygunluk bu tablodan okunur.
CREATE TABLE switch_ports (
 id INTEGER PRIMARY KEY, device_id INTEGER NOT NULL REFERENCES devices(id), number INTEGER NOT NULL CHECK(number>0),
 suitability TEXT NOT NULL DEFAULT 'suitable' CHECK(suitability IN ('suitable','disabled','faulty')),
 version INTEGER NOT NULL DEFAULT 1, UNIQUE(device_id,number)
);
-- Bağlantı ömrü: eski uç silinmez, ended_at ile sonlandırılır ve yeni kayıt açılır.
CREATE TABLE connections (
 id INTEGER PRIMARY KEY, interface_id INTEGER NOT NULL REFERENCES network_interfaces(id),
 port_id INTEGER NOT NULL REFERENCES switch_ports(id), cable_id INTEGER NOT NULL REFERENCES cables(id),
 started_at TEXT NOT NULL, ended_at TEXT, created_by INTEGER NOT NULL REFERENCES users(id),
 CHECK(ended_at IS NULL OR ended_at >= started_at)
);
-- Yalnızca aktif bağlantılarda arayüz tekilliği; tarihsel kayıtlar aynı arayüzü kullanabilir.
CREATE UNIQUE INDEX uq_active_interface ON connections(interface_id) WHERE ended_at IS NULL;
-- Bir fiziksel port aynı anda en fazla bir aktif bağlantıda yer alabilir.
CREATE UNIQUE INDEX uq_active_port ON connections(port_id) WHERE ended_at IS NULL;
-- Bir kablo aynı anda en fazla bir aktif bağlantıda kullanılabilir.
CREATE UNIQUE INDEX uq_active_cable ON connections(cable_id) WHERE ended_at IS NULL;
-- Saha kontrolleri ek kayıt olarak tutulur; en son sonuç bağlantının doğrulama durumunu belirler.
CREATE TABLE field_verifications (
 id INTEGER PRIMARY KEY, connection_id INTEGER NOT NULL REFERENCES connections(id),
 result TEXT NOT NULL CHECK(result IN ('verified','mismatch')), note TEXT NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);
-- Arıza durumu, önceliği, ataması ve çözüm kaydı; bağlantı doğrulamasından ayrı yaşam döngüsüdür.
CREATE TABLE incidents (
 id INTEGER PRIMARY KEY, device_id INTEGER NOT NULL REFERENCES devices(id), title TEXT NOT NULL,
 description TEXT NOT NULL, priority TEXT NOT NULL CHECK(priority IN ('low','medium','high')),
 status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','investigating','waiting','resolved','cancelled')),
 assigned_to INTEGER REFERENCES users(id), created_by INTEGER NOT NULL REFERENCES users(id),
 created_at TEXT NOT NULL, resolved_at TEXT, resolution TEXT NOT NULL DEFAULT '',
 version INTEGER NOT NULL DEFAULT 1
);
-- Arızaya eklenen saha notları; kayıt eklemek arızayı kendiliğinden kapatmaz.
CREATE TABLE interventions (
 id INTEGER PRIMARY KEY, incident_id INTEGER NOT NULL REFERENCES incidents(id),
 note TEXT NOT NULL, actor_id INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);
-- Varlık değişikliğinin önce/sonra JSON değerleri, gerekçesi ve yapan kişisi.
CREATE TABLE audit_events (
 id INTEGER PRIMARY KEY, entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL, action TEXT NOT NULL,
 before_json TEXT, after_json TEXT, reason TEXT NOT NULL, actor_id INTEGER NOT NULL REFERENCES users(id),
 created_at TEXT NOT NULL
);
-- Fiziksel değişikliğin eski/yeni bağlantı kimlikleri ve isteğe bağlı arıza ilişkisi.
CREATE TABLE connection_changes (
 id INTEGER PRIMARY KEY, old_connection_id INTEGER REFERENCES connections(id),
 new_connection_id INTEGER REFERENCES connections(id), kind TEXT NOT NULL,
 reason TEXT NOT NULL, actor_id INTEGER NOT NULL REFERENCES users(id),
 incident_id INTEGER REFERENCES incidents(id), created_at TEXT NOT NULL
);
-- Kullanıcı ve istek anahtarı tekildir; aynı isteğin tekrarında saklanan yanıt döndürülür.
CREATE TABLE request_keys (
 user_id INTEGER NOT NULL REFERENCES users(id), request_key TEXT NOT NULL, payload_hash TEXT NOT NULL,
 response_json TEXT NOT NULL, PRIMARY KEY(user_id,request_key)
);
-- Durum ve cihaza göre arıza listesi sorgularını hızlandırır.
CREATE INDEX ix_incidents_status ON incidents(status,device_id);
-- Varlık türü ve kimliğine göre denetim geçmişi okumalarını destekler.
CREATE INDEX ix_audit_entity ON audit_events(entity_type,entity_id);
