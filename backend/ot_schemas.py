# OT kapsamı, seviye, kontrol ve bulgu isteklerinin doğrulama kuralları.
from datetime import date
from typing import Annotated, Literal
from pydantic import Field, model_validator
from backend.schemas import Input

# Tekrarlanan alan sınırlarını ortak türlere toplar; bool değerleri güvenlik seviyesi yerine kabul edilmez.
Text = Annotated[str, Field(min_length=3, max_length=4000)]
Id = Annotated[int, Field(gt=0)]
Level = Annotated[int, Field(strict=True, ge=0, le=4)]


# SUC (değerlendirilen sistem) kodunu, sınırını ve sorumlusunu tanımlar.
class SystemInput(Input):
    code: str = Field(min_length=2, max_length=60)
    name: str = Field(min_length=3, max_length=160)
    boundary: Text
    owner_id: Id


# Aynı güvenlik ihtiyacına sahip varlıkların zone tanımını ve sistem bağını taşır.
class ZoneInput(Input):
    system_id: Id
    code: str = Field(min_length=2, max_length=60)
    name: str = Field(min_length=3, max_length=160)
    purpose: Text
    boundary: Text
    owner_id: Id


# Zone değişikliği için mevcut sürüm ve gerekçe ister.
class ZoneUpdate(ZoneInput):
    version: Id
    reason: Text


# Zone’a atanacak cihazların tamamını, sürümü ve üyelik değişikliği gerekçesini taşır.
class MembershipInput(Input):
    device_ids: list[Id] = Field(max_length=500)
    version: Id
    reason: Text


# İki zone arasındaki iletişim yönünü, protokolleri, amacı ve kayıtlı koruma önlemlerini tanımlar.
class ConduitInput(Input):
    system_id: Id
    code: str = Field(min_length=2, max_length=60)
    name: str = Field(min_length=3, max_length=160)
    source_zone_id: Id
    target_zone_id: Id
    direction: Literal['one_way', 'bidirectional']
    protocols: Text
    purpose: Text
    controls: Text
    owner_id: Id


# Conduit değişikliği için sürüm ve gerekçe ekler.
class ConduitUpdate(ConduitInput):
    version: Id
    reason: Text


# Cihaz, zone veya conduit kapsamlarından tam olarak birinin seçilmesini sağlar.
class ScopeInput(Input):
    device_id: Id | None = None
    zone_id: Id | None = None
    conduit_id: Id | None = None

    # Bir bulgunun aynı anda birden fazla kapsamı işaretlemesini veya kapsamsız kalmasını engeller.
    @model_validator(mode='after')
    def exactly_one(self):
        if sum(value is not None for value in (self.device_id,self.zone_id,self.conduit_id)) != 1:
            raise ValueError('Tek bir cihaz, zone veya conduit kapsamı seçin.')
        return self


# SL-A mevcut durum, SL-T hedef için yedi FR seviyesini taşır; None bilinmeyendir, seviye 0 ile aynı değildir.
class LevelInput(Input):
    zone_id: Id | None = None
    conduit_id: Id | None = None
    sl_type: Literal['achieved', 'target']
    vector: list[Level | None] = Field(min_length=7, max_length=7)
    rationale: Text
    reference: str = Field(default='', max_length=2000)
    scope_version: Id
    expected_profile_id: Id | None = None
    status: Literal['draft', 'approved'] = 'draft'

    # Zone/conduit seçiminden birini zorunlu tutar; onay için yedi FR değeri ve referans bulunmasını denetler.
    @model_validator(mode='after')
    def valid_profile(self):
        if (self.zone_id is None) == (self.conduit_id is None):
            raise ValueError('Zone veya conduit seçin.')
        if self.status == 'approved' and (None in self.vector or len(self.reference) < 3):
            raise ValueError('Onay için 7 FR seviyesi ve kanıt/risk değerlendirmesi referansı gerekir.')
        return self


# Cihazın operasyonel etkisini ve gerekçesini kaydeder; kritiklik bir güvenlik seviyesi değildir.
class CriticalityInput(Input):
    criticality: Literal['unknown', 'low', 'medium', 'high']
    rationale: Text
    version: int = Field(ge=0)


# Bir kontrol maddesinin sonucu, gözlemi ve kanıt referansını taşır.
class ControlResult(Input):
    code: str = Field(min_length=4,max_length=10)
    result: Literal['suitable','unsuitable','unknown','not_applicable'] | None = None
    note: str = Field(default='',max_length=2000)
    evidence: str = Field(default='',max_length=2000)


# Sekiz maddelik cihaz kontrolünün taslak veya tamamlama isteğini ve sürümünü tanımlar.
class AssessmentInput(Input):
    device_id: Id
    results: list[ControlResult] = Field(max_length=8)
    finalize: bool = False
    version: int = Field(default=0,ge=0)


# Kapsam dışı cevapların yönetici onay notunu ve beklenen kayıt sürümünü taşır.
class ApprovalInput(Input):
    version: Id
    note: Text


# Bir bulgunun gözlemini ve isteğe bağlı kontrol/FR/hedef profil bağlantılarını tanımlar.
class FindingInput(ScopeInput):
    title: str = Field(min_length=3,max_length=180)
    observation: Text
    assessment_id: Id | None = None
    control_code: str | None = Field(default=None,max_length=10)
    fr_code: Literal['FR1','FR2','FR3','FR4','FR5','FR6','FR7'] | None = None
    target_profile_id: Id | None = None


# Öncelik, sorumlu, hedef tarih ve plan değişikliği gerekçesini birlikte taşır.
class FindingPlan(Input):
    priority: Literal['low','medium','high']
    assigned_to: Id | None = None
    due_date: date | None = None
    reason: Text
    version: Id


# İzin verilen bulgu işlem türlerini, açıklamayı, kanıtı ve beklenen sürümü tanımlar.
class FindingAction(Input):
    kind: Literal['work','submit','verify','return','cancel','reopen']
    note: Text
    evidence: str = Field(default='',max_length=2000)
    version: Id
