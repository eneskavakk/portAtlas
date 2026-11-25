# Ders demosunun isteğe bağlı OT kapsamlarını ekler; gerçek saha değerlendirmesi üretmez.
"""Optional illustrative OT data, never automatically inserted into real data."""
from backend.db.database import closing_connection,transaction,now
from backend.errors import require


# Yalnızca demo olarak işaretli veritabanına temsili SUC, zone ve conduit ekler; kanıtsız seviye veya kontrol sonucu üretmez.
def seed_ot(path):
    with closing_connection(path) as db,transaction(db):
        require(db.execute("SELECT 1 FROM settings WHERE key='demo' AND value='true'").fetchone() is not None,'OT demo yalnızca temsili demo veritabanına eklenebilir.')
        require(db.execute('SELECT 1 FROM security_systems').fetchone() is None,'OT sistemleri zaten var; mevcut kayıtlar değiştirilmedi.')
        manager=db.execute("SELECT id FROM users WHERE role='manager' AND active=1 ORDER BY id LIMIT 1").fetchone()
        require(manager is not None,'Aktif sorumlu gerekli.')
        owner=manager['id']
        sid=db.execute('INSERT INTO security_systems(code,name,boundary,owner_id,created_at) VALUES (?,?,?,?,?)',
            ('SUC-MNS','Manisa üretim kontrol sistemi','Temsili ders kapsamı: Hat 2, Hat 3 ve bakım erişim sınırı. Kurumsal IT kapsam dışında.',owner,now())).lastrowid
        # Önce mantıksal güvenlik bölgeleri oluşturulur; varlık üyelikleri sonraki adımda cihaz kodlarıyla bağlanır.
        zones=[]
        for code,name,purpose,boundary in [
            ('Z-HAT2','Hat 2 kontrol bölgesi','Hat 2 üretim kontrol varlıklarını birlikte değerlendirmek.','CNC, pres ve Hat 2 switch varlıkları; fiziksel konumdan bağımsız güvenlik kapsamı.'),
            ('Z-HAT3','Hat 3 kontrol bölgesi','Hat 3 otomasyon varlıklarını birlikte değerlendirmek.','Robot, PLC ve Hat 3 switch varlıkları.'),
            ('Z-BAKIM','Bakım erişim bölgesi','Bakım erişim sürecinin güvenlik ihtiyaçlarını değerlendirmek.','Temsili bakım erişimi kapsamı. İstemci varlıkları henüz kaydedilmedi.')]:
            zones.append(db.execute('INSERT INTO security_zones(system_id,code,name,purpose,boundary,owner_id,created_at) VALUES (?,?,?,?,?,?,?)',(sid,code,name,purpose,boundary,owner,now())).lastrowid)
        for zone,codes in [(zones[0],['CNC-014','PRS-003','SW-HAT2-01','CNC-009']),(zones[1],['RBT-008','PLC-002','SW-HAT3-01'])]:
            for code in codes:
                device=db.execute('SELECT id FROM devices WHERE asset_code=?',(code,)).fetchone()
                if device:
                    db.execute('INSERT INTO zone_members VALUES (?,?,?,?)',(device['id'],zone,owner,now()))
        db.execute('INSERT INTO security_conduits(system_id,code,name,source_zone_id,target_zone_id,direction,protocols,purpose,controls,owner_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            (sid,'C-BAKIM-H2','Bakım → Hat 2',zones[2],zones[0],'one_way','Temsili plan: HTTPS / TCP 443; gerçek akış doğrulanmadı.','Planlanan bakım erişiminin kayıt altına alınması.','Planlanan: yetkili erişim, ara sunucu ve kayıt. Uygulandığı doğrulanmadı.',owner,now()))
        # Mevcut/hedef seviye ve değerlendirme kanıtı uydurulmaz; bunlar kullanıcı değerlendirmesi gerektirir.
    print('Temsili SUC, 3 zone ve 1 conduit eklendi. SL-A / SL-T belirlenmedi.')
