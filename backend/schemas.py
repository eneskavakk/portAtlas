# Çekirdek modüllerin Pydantic istek modelleri; tür ve temel sınırlar burada doğrulanır.
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


# Ortak istek tabanı: metinlerin kenar boşluklarını temizler, beklenmeyen alanları reddeder.
class Input(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


# Giriş alanlarının temel uzunluk sınırlarını doğrular; kimlik denetimi API katmanında yapılır.
class Login(Input):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)


# Makine/switch kaydının alanlarını ve switch için 1–128 port sınırını tanımlar.
class DeviceInput(Input):
    asset_code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    device_type: Literal["machine", "switch"]
    location_id: int = Field(gt=0)
    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=2000)
    port_count: int = Field(default=24, ge=1, le=128)


# Cihaz değişikliklerine sürüm ve gerekçe ekler; eski formdan güncellemeyi kontrol etmeyi sağlar.
class DeviceUpdate(DeviceInput):
    version: int = Field(ge=1)
    active: bool = True
    reason: str = Field(min_length=3, max_length=2000)


# Konum türünü ve isteğe bağlı üst konum kimliğini tanımlar; hiyerarşi ilişkisi ayrıca API’de denetlenir.
class LocationInput(Input):
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["facility", "area", "line", "station"]
    parent_id: int | None = Field(default=None, gt=0)


# Bir cihazın ağ arayüzü alanlarını taşır; IP/MAC biçimleri API’de ayrıca doğrulanır.
class InterfaceInput(Input):
    device_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=60)
    ip: str = Field(default="", max_length=45)
    mac: str = Field(default="", max_length=17)


# Kablo etiketi ve türü için gerekli alanları ve uzunluk sınırlarını tanımlar.
class CableInput(Input):
    label: str = Field(min_length=1, max_length=60)
    cable_type: str = Field(default="CAT6", min_length=1, max_length=30)


# Bağlantı işlem türünü, beklenen mevcut kaydı ve tekrar denemeleri ayırt eden request_key değerini taşır.
class ConnectionInput(Input):
    kind: Literal["create", "move", "replace_cable", "terminate"]
    interface_id: int = Field(gt=0)
    expected_connection_id: int | None = Field(default=None, gt=0)
    port_id: int | None = Field(default=None, gt=0)
    cable_id: int | None = Field(default=None, gt=0)
    reason: str = Field(min_length=3, max_length=2000)
    incident_id: int | None = Field(default=None, gt=0)
    request_key: str = Field(min_length=16, max_length=100)


# Saha kontrolünü tutarlı/uyuşmazlık sonucu ve açıklamasıyla sınırlar.
class VerificationInput(Input):
    result: Literal["verified", "mismatch"]
    note: str = Field(min_length=3, max_length=2000)


# Port uygunluk değişikliği için durum, gerekçe ve kayıt sürümü ister.
class PortInput(Input):
    suitability: Literal["suitable", "faulty", "disabled"]
    reason: str = Field(min_length=3, max_length=2000)
    version: int = Field(ge=1)


# Yeni arızanın cihaz, başlık, açıklama ve öncelik alanlarını doğrular.
class IncidentInput(Input):
    device_id: int = Field(gt=0)
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=3, max_length=4000)
    priority: Literal["low", "medium", "high"] = "medium"


# Arıza durum geçişinde sürümü, gerekçeyi ve saha çözüm onayını taşır.
class TransitionInput(Input):
    status: Literal["open", "investigating", "waiting", "resolved", "cancelled"]
    version: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=2000)
    verified: bool = False


# Görevin atanacağı kullanıcıyı ve güncellenmesi beklenen sürümü tanımlar.
class AssignmentInput(Input):
    user_id: int = Field(gt=0)
    version: int = Field(ge=1)


# Saha müdahale notunun boş veya aşırı uzun olmasını engeller.
class NoteInput(Input):
    note: str = Field(min_length=3, max_length=4000)


# Yeni hesapta kullanıcı adı, görünen ad, parola uzunluğu ve izin verilen rolü doğrular.
class UserInput(Input):
    username: str = Field(min_length=3, max_length=100)
    name: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=10, max_length=256)
    role: Literal["manager", "technician"]
