# Servis ve API katmanlarının ortak iş kuralı hata sözleşmesi.
# Beklenen iş kuralı ihlalini teknik hatalardan ayıran uygulama istisnasıdır.
class DomainError(Exception):
    # İş kuralı hatasının kullanıcı mesajını, HTTP durumunu ve makine tarafından okunabilir kodunu taşır.
    def __init__(self, message, status=409, code="conflict"):
        self.message, self.status, self.code = message, status, code


# İş kuralı sağlanmıyorsa ortak hata işleyicisine aktarılacak DomainError üretir.
def require(condition, message, status=409, code="conflict"):
    if not condition:
        raise DomainError(message, status, code)
