-- SUC: değerlendirilen sistemin sınırı ve sorumlusu; teknik ağ taraması değildir.
CREATE TABLE security_systems (
 id INTEGER PRIMARY KEY, code TEXT NOT NULL COLLATE NOCASE UNIQUE, name TEXT NOT NULL,
 boundary TEXT NOT NULL, owner_id INTEGER NOT NULL REFERENCES users(id),
 created_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1
);
-- Ortak güvenlik ihtiyacına göre varlık kapsamı; fiziksel konum ağacından bağımsızdır.
CREATE TABLE security_zones (
 id INTEGER PRIMARY KEY, system_id INTEGER NOT NULL REFERENCES security_systems(id),
 code TEXT NOT NULL COLLATE NOCASE UNIQUE, name TEXT NOT NULL, purpose TEXT NOT NULL,
 boundary TEXT NOT NULL, owner_id INTEGER NOT NULL REFERENCES users(id),
 version INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL,
 UNIQUE(id,system_id)
);
-- device_id birincil anahtarı her cihazın bu sürümde tek bir birincil zone üyeliğini garanti eder.
CREATE TABLE zone_members (
 device_id INTEGER PRIMARY KEY REFERENCES devices(id), zone_id INTEGER NOT NULL REFERENCES security_zones(id),
 assigned_by INTEGER NOT NULL REFERENCES users(id), assigned_at TEXT NOT NULL
);
-- İki farklı zone arasındaki iletişim belgesi; birleşik yabancı anahtarlar aynı sistemde kalmayı zorunlu tutar.
CREATE TABLE security_conduits (
 id INTEGER PRIMARY KEY, system_id INTEGER NOT NULL REFERENCES security_systems(id),
 code TEXT NOT NULL COLLATE NOCASE UNIQUE, name TEXT NOT NULL,
 source_zone_id INTEGER NOT NULL, target_zone_id INTEGER NOT NULL,
 direction TEXT NOT NULL CHECK(direction IN ('one_way','bidirectional')),
 protocols TEXT NOT NULL, purpose TEXT NOT NULL, controls TEXT NOT NULL,
 owner_id INTEGER NOT NULL REFERENCES users(id), version INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL,
 CHECK(source_zone_id<>target_zone_id),
 FOREIGN KEY(source_zone_id,system_id) REFERENCES security_zones(id,system_id),
 FOREIGN KEY(target_zone_id,system_id) REFERENCES security_zones(id,system_id)
);
-- SL-A mevcut/SL-T hedef revizyonları; vektör, kanıt/risk dayanağı ve kapsam anlık görüntüsü ayrı saklanır.
CREATE TABLE security_level_profiles (
 id INTEGER PRIMARY KEY, zone_id INTEGER REFERENCES security_zones(id), conduit_id INTEGER REFERENCES security_conduits(id),
 sl_type TEXT NOT NULL CHECK(sl_type IN ('achieved','target')),
 revision INTEGER NOT NULL, vector_json TEXT NOT NULL,
 rationale TEXT NOT NULL, reference TEXT NOT NULL, scope_version INTEGER NOT NULL,
 source_context_json TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('draft','approved')),
 created_by INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL,
 approved_by INTEGER REFERENCES users(id), approved_at TEXT,
 CHECK((zone_id IS NOT NULL)+(conduit_id IS NOT NULL)=1),
 CHECK(status<>'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);
-- Aynı zone ve profil türünde aynı revizyon numarası ikinci kez açılamaz.
CREATE UNIQUE INDEX uq_zone_sl_revision ON security_level_profiles(zone_id,sl_type,revision) WHERE zone_id IS NOT NULL;
-- Aynı conduit ve profil türünde aynı revizyon numarası ikinci kez açılamaz.
CREATE UNIQUE INDEX uq_conduit_sl_revision ON security_level_profiles(conduit_id,sl_type,revision) WHERE conduit_id IS NOT NULL;
-- Operasyonel kritiklik bilgisi; eksik değerlendirme unknown kalır ve güvenlik seviyesiyle birleştirilmez.
CREATE TABLE device_security (
 device_id INTEGER PRIMARY KEY REFERENCES devices(id),
 criticality TEXT NOT NULL DEFAULT 'unknown' CHECK(criticality IN ('unknown','low','medium','high')),
 rationale TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
 updated_by INTEGER NOT NULL REFERENCES users(id), updated_at TEXT NOT NULL
);
-- Soru şablonu, sonuçlar ve bağlam kopyası saklanır; eski değerlendirmeler yeni şablondan etkilenmez.
CREATE TABLE ot_assessments (
 id INTEGER PRIMARY KEY, device_id INTEGER NOT NULL REFERENCES devices(id), template_version TEXT NOT NULL,
 template_json TEXT NOT NULL, results_json TEXT NOT NULL, context_json TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('draft','pending_review','completed')),
 author_id INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL, completed_at TEXT,
 approved_by INTEGER REFERENCES users(id), approval_note TEXT, version INTEGER NOT NULL DEFAULT 1
);
-- Bulgu tam bir cihaz/zone/conduit kapsamına bağlıdır; öncelik yönetici değerlendirmesi bekleyebilir.
CREATE TABLE security_findings (
 id INTEGER PRIMARY KEY, device_id INTEGER REFERENCES devices(id), zone_id INTEGER REFERENCES security_zones(id),
 conduit_id INTEGER REFERENCES security_conduits(id), assessment_id INTEGER REFERENCES ot_assessments(id),
 control_code TEXT, title TEXT NOT NULL, observation TEXT NOT NULL,
 priority TEXT NOT NULL CHECK(priority IN ('low','medium','high')), priority_reviewed INTEGER NOT NULL DEFAULT 0 CHECK(priority_reviewed IN (0,1)),
 status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','in_progress','awaiting_verification','closed','cancelled')),
 assigned_to INTEGER REFERENCES users(id), due_date TEXT,
 created_by INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
 CHECK((device_id IS NOT NULL)+(zone_id IS NOT NULL)+(conduit_id IS NOT NULL)=1)
);
-- Açık ve son tarihi geçmiş aksiyonları listeleyen sorguları destekler.
CREATE INDEX ix_findings_status ON security_findings(status,due_date);
-- Uygulama ve doğrulama adımlarını kişi, açıklama ve kanıt referansıyla ek kayıt olarak korur.
CREATE TABLE security_finding_actions (
 id INTEGER PRIMARY KEY, finding_id INTEGER NOT NULL REFERENCES security_findings(id),
 kind TEXT NOT NULL CHECK(kind IN ('work','submit','verify','return','cancel','reopen')),
 note TEXT NOT NULL, evidence TEXT NOT NULL, actor_id INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);
