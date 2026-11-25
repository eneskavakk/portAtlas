# SQLite bağlantı yaşam döngüsü, şema göçleri ve transaction yardımcıları.
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[2]


# Zaman damgalarını UTC ve ISO biçiminde üretir; kayıtların sıralaması ortak bir zaman temeline dayanır.
def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


# Her istek için ayrı SQLite bağlantısı açar; yabancı anahtarları ve kilit bekleme süresini etkinleştirir.
def connect(path):
    # Bağlantı bir isteğe aittir. FastAPI aynı isteğin bağımlılık ve uç kodunu farklı
    # iş parçacıklarında sürdürebilir; bağlantı farklı istekler arasında paylaşılmaz.
    db = sqlite3.connect(str(path), timeout=5, isolation_level=None, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=5000")
    return db


# Eksik veritabanını hazırlar ve daha önce uygulanmamış SQL göçlerini dosya sırasıyla çalıştırır.
def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing_connection(path) as db:
        # WAL, okuyucuların yazma işlemleriyle birlikte çalışabilmesini kolaylaştırır; tek yazıcı sınırı devam eder.
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
        # Göç dosya adı uygulanan sürüm olarak tutulur; açılışta aynı SQL tekrar çalıştırılmaz.
        for file in sorted((ROOT / "backend/db/migrations").glob("*.sql")):
            if not db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (file.name,)).fetchone():
                # executescript için BEGIN/COMMIT açıkça verilir; göçün sürüm kaydı da aynı işlemde yazılır.
                script = "BEGIN IMMEDIATE;\n" + file.read_text() + "\nINSERT INTO schema_migrations VALUES ('" + file.name.replace("'", "''") + "','" + now() + "');\nCOMMIT;"
                # Göç ve sürüm kaydı birlikte tamamlanır; hata olursa açık transaction geri alınır.
                try:
                    db.executescript(script)
                except Exception:
                    if db.in_transaction:
                        db.rollback()
                    raise


# İşlem başarılı olsa da hata oluşsa da bağlantının kapanmasını sağlayan bağlam yöneticisidir.
@contextmanager
def closing_connection(path):
    db = connect(path)
    try:
        yield db
    finally:
        db.close()


# Yazma kilidini baştan alır; bütün adımlar başarılıysa commit, hata varsa rollback yapar.
@contextmanager
def transaction(db):
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


# SQLite satırlarını JSON yanıtlarında kullanılabilecek sözlük listesine dönüştürür.
def rows(db, sql, args=()):
    return [dict(r) for r in db.execute(sql, args).fetchall()]
