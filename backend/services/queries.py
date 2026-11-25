# Arayüzün ihtiyaç duyduğu birleşik okuma sorguları; bu katman kayıt değiştirmez.
from backend.db.database import rows

CONNECTION_SELECT = """
SELECT c.*,i.name interface_name,i.device_id,d.asset_code,d.name device_name,
 s.asset_code switch_code,s.id switch_id,p.number port_number, p.suitability,
 k.label cable_label,l.name location_name,
 COALESCE((SELECT result FROM field_verifications v WHERE v.connection_id=c.id ORDER BY v.id DESC LIMIT 1),'pending') verification,
 (SELECT created_at FROM field_verifications v WHERE v.connection_id=c.id ORDER BY v.id DESC LIMIT 1) verified_at,
 (SELECT u.name FROM field_verifications v JOIN users u ON u.id=v.actor_id WHERE v.connection_id=c.id ORDER BY v.id DESC LIMIT 1) verifier
FROM connections c JOIN network_interfaces i ON i.id=c.interface_id
JOIN devices d ON d.id=i.device_id JOIN switch_ports p ON p.id=c.port_id
JOIN devices s ON s.id=p.device_id JOIN cables k ON k.id=c.cable_id
JOIN locations l ON l.id=d.location_id
"""


# Bağlantıları cihaz, kablo, port ve son saha doğrulamasıyla birleştirir; filtre değerleri parametre olarak bağlanır.
def connections(db, where="c.ended_at IS NULL", args=()):
    return rows(db, CONNECTION_SELECT + " WHERE " + where + " ORDER BY c.id DESC", args)


# Özyinelemeli sorguyla konum ağacını düz listeye çevirir; path ve depth alanları arayüzde hiyerarşiyi gösterir.
def locations(db):
    return rows(db, """WITH RECURSIVE tree AS (
    SELECT *, name path, 0 depth FROM locations WHERE parent_id IS NULL
    UNION ALL SELECT l.*, tree.path || ' / ' || l.name,tree.depth+1 FROM locations l JOIN tree ON l.parent_id=tree.id)
    SELECT * FROM tree ORDER BY path""")


# Eski ve yeni bağlantı uçlarını birlikte döndürür; sonlandırılmış kayıtların geçmişi de listede kalır.
def history(db, device_id=None):
    sql = """SELECT ch.*,u.name actor_name,
    i.device_id,d.asset_code,
    op.number old_port,np.number new_port,os.asset_code old_switch,ns.asset_code new_switch,
    ok.label old_cable,nk.label new_cable
    FROM connection_changes ch JOIN users u ON u.id=ch.actor_id
    LEFT JOIN connections oc ON oc.id=ch.old_connection_id
    LEFT JOIN connections nc ON nc.id=ch.new_connection_id
    JOIN network_interfaces i ON i.id=COALESCE(nc.interface_id,oc.interface_id)
    JOIN devices d ON d.id=i.device_id
    LEFT JOIN switch_ports op ON op.id=oc.port_id LEFT JOIN devices os ON os.id=op.device_id
    LEFT JOIN switch_ports np ON np.id=nc.port_id LEFT JOIN devices ns ON ns.id=np.device_id
    LEFT JOIN cables ok ON ok.id=oc.cable_id LEFT JOIN cables nk ON nk.id=nc.cable_id"""
    return rows(db, sql + (" WHERE i.device_id=?" if device_id else "") + " ORDER BY ch.id DESC LIMIT 300", (device_id,) if device_id else ())


# Arızaları cihaz, bildiren kullanıcı ve atanmış sorumlu bilgileriyle listeler.
def incidents(db):
    return rows(db, """SELECT n.*,d.asset_code,d.name device_name,u.name assignee_name,
    a.name reporter_name,l.name location_name FROM incidents n JOIN devices d ON d.id=n.device_id
    JOIN locations l ON l.id=d.location_id LEFT JOIN users u ON u.id=n.assigned_to
    JOIN users a ON a.id=n.created_by ORDER BY n.created_at DESC,n.id DESC""")
