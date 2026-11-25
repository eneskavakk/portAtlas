-- Hedef farkından açılan bulguyu ilgili FR kodu ve SL-T revizyonuna bağlar.
ALTER TABLE security_findings ADD COLUMN fr_code TEXT CHECK(fr_code IN ('FR1','FR2','FR3','FR4','FR5','FR6','FR7'));
ALTER TABLE security_findings ADD COLUMN target_profile_id INTEGER REFERENCES security_level_profiles(id);
