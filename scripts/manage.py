# Yerel kurulum, temsili veri, yönetici hesabı ve veritabanı yedeği için yönetim komutları.
"""Run from repository root: python -m scripts.manage --help."""
import argparse
import getpass
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from backend.db.database import ROOT, initialize, closing_connection, transaction, now
from backend.security import hash_password


# Yalnızca boş veritabanına temsili ekip, konum, varlık ve bağlantı verisi ekler; mevcut kayıtların üzerine yazmaz.
def seed_demo(path):
    initialize(path)
    with closing_connection(path) as db, transaction(db):
        if db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            raise SystemExit("Veritabanı boş değil; demo verisi eklenmedi. Mevcut kayıtlar korundu.")
        db.execute("INSERT INTO settings VALUES ('demo','true')")
        for username,name,role in [("admin","Enes Kavak","manager"),("teknisyen","Doğukan Keser","technician")]:
            db.execute("INSERT INTO users(username,name,password_hash,role,created_at) VALUES (?,?,?,?,?)",(username,name,hash_password("PortAtlas2026!"),role,now()))
        for code,name,kind,parent in [("TES-01","Manisa Üretim Tesisi","facility",None),("BLG-01","Üretim","area",1),("HAT-02","Hat 2","line",2),("IST-04","İstasyon 4","station",3),("HAT-03","Hat 3","line",2),("IST-07","İstasyon 7","station",5)]:
            db.execute("INSERT INTO locations(code,name,kind,parent_id) VALUES (?,?,?,?)",(code,name,kind,parent))
        # Örnek varlıklar eğitim içindir; gerçek cihaz keşfi veya saha doğrulaması yapılmış sayılmaz.
        assets=[("CNC-014","Dikey İşleme Merkezi","machine",4,"DMG MORI","NVX 2500"),
                ("PRS-003","Hidrolik Pres","machine",4,"Durmazlar","AD-S"),
                ("RBT-008","Kaynak Robotu","machine",6,"ABB","IRB 2600"),
                ("PLC-002","Hat Kontrol Ünitesi","machine",6,"Siemens","S7-1500"),
                ("SW-HAT2-01","Hat 2 Dağıtım Switch'i","switch",3,"Cisco","CBS250"),
                ("SW-HAT3-01","Hat 3 Dağıtım Switch'i","switch",5,"Siemens","SCALANCE"),
                ("CNC-009","Yatay İşleme Merkezi","machine",4,"Mazak","HCN-5000")]
        for code,name,kind,loc,brand,model in assets:
            db.execute("INSERT INTO devices(asset_code,name,device_type,location_id,brand,model,description,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",(code,name,kind,loc,brand,model,"Temsili ders demosu kaydı",now(),now()))
        for device in (1,2,3,4,7):
            db.execute("INSERT INTO network_interfaces(device_id,name,ip,mac) VALUES (?,?,?,?)",(device,"Ethernet-1",f"192.168.20.{40+device}",f"00:1B:44:11:3A:{device:02X}"))
        db.execute("INSERT INTO network_interfaces(device_id,name) VALUES (1,'Ethernet-2')")
        for n in range(87,96):
            db.execute("INSERT INTO cables(label) VALUES (?)",(f"KBL-{n:04}",))
        for device,count in [(5,24),(6,16)]:
            db.executemany("INSERT INTO switch_ports(device_id,number) VALUES (?,?)",[(device,i) for i in range(1,count+1)])
        db.execute("UPDATE switch_ports SET suitability='faulty' WHERE device_id=5 AND number=12")
        db.execute("UPDATE switch_ports SET suitability='disabled' WHERE device_id=5 AND number=24")
        stamp=(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()
        for interface,port,cable in [(1,5,1),(2,3,2),(3,25,3),(4,26,4),(5,16,5)]:
            id=db.execute("INSERT INTO connections(interface_id,port_id,cable_id,started_at,created_by) VALUES (?,?,?,?,1)",(interface,port,cable,stamp)).lastrowid
            db.execute("INSERT INTO connection_changes(new_connection_id,kind,reason,actor_id,created_at) VALUES (?,'create','İlk envanter kaydı',1,?)",(id,stamp))
            if interface in (2,3,4):
                db.execute("INSERT INTO field_verifications(connection_id,result,note,actor_id,created_at) VALUES (?,'verified','Etiketler sahada kontrol edildi',2,?)",(id,stamp))
        for days,device,title,priority,status,assigned in [(0,1,"Aralıklı bağlantı kesintisi","high","open",2),(1,3,"Kablo etiketi okunamıyor","medium","investigating",2),(3,2,"Ağ arayüzü kontrolü","low","resolved",1)]:
            created=(datetime.now(timezone.utc)-timedelta(days=days,hours=2)).isoformat()
            resolved=now() if status=="resolved" else None
            db.execute("INSERT INTO incidents(device_id,title,description,priority,status,assigned_to,created_by,created_at,resolved_at,resolution) VALUES (?,?,?,?,?,?,1,?,?,?)",(device,title,"Temsili saha bildirimi. Bağlantı ve kablo kontrolü gerekli.",priority,status,assigned,created,resolved,"Saha kontrolü tamamlandı" if resolved else ""))
    print("Demo hazır. admin veya teknisyen / PortAtlas2026! (yalnızca yerel demo)")


# Komut satırı seçeneklerini okuyarak kurulum, demo, yönetici oluşturma veya tutarlı yedekleme işlemini seçer.
def main():
    parser=argparse.ArgumentParser(description="PortAtlas kurulum ve yedekleme")
    parser.add_argument("command",choices=["init","demo","ot-demo","create-admin","backup"])
    parser.add_argument("--db",default=os.getenv("PORTATLAS_DB",str(ROOT/"data/portatlas.db")))
    parser.add_argument("--output",help="Yedek hedef dosyası")
    args=parser.parse_args()
    path=Path(args.db)
    initialize(path)
    # Her komut farklı kurulum işini yürütür; gerçek kayıtların üzerine demo yüklenmez.
    if args.command=="demo":
        seed_demo(path)
    elif args.command=="ot-demo":
        from scripts.seed_ot import seed_ot
        seed_ot(path)
    elif args.command=="create-admin":
        username=input("Kullanıcı adı: ").strip()
        name=input("Ad soyad: ").strip()
        password=getpass.getpass("Parola (en az 10 karakter): ")
        if not username or not name or len(password)<10:
            raise SystemExit("Kullanıcı adı, ad ve en az 10 karakter parola gerekli.")
        with closing_connection(path) as db, transaction(db):
            db.execute("INSERT INTO users(username,name,password_hash,role,created_at) VALUES (?,?,?,'manager',?)",(username,name,hash_password(password),now()))
        print("Sorumlu hesabı oluşturuldu.")
    elif args.command=="backup":
        import sqlite3
        if not args.output:
            raise SystemExit("--output ile yeni bir yedek dosya yolu belirtin.")
        target=Path(args.output)
        if target.exists() or target.resolve()==path.resolve():
            raise SystemExit("Yedek hedefi yeni bir dosya olmalıdır.")
        target.parent.mkdir(parents=True,exist_ok=True)
        # SQLite backup API, bağlantı açıkken tutarlı bir yedek üretir; canlı dosya ham kopyalanmaz.
        with closing_connection(path) as source, sqlite3.connect(target) as dest:
            source.backup(dest)
        print("Tutarlı SQLite yedeği oluşturuldu.")
    else:
        print("Veritabanı ve migrations hazır.")


if __name__=="__main__":
    main()
