# Parola ve oturum belirteçlerinin güvenli biçimde işlenmesine ait yardımcılar.
import hashlib
import hmac
import secrets


# Her parola için rastgele tuz üretir; düz metin yerine scrypt özeti ve tuzu saklanır.
def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return f"scrypt${salt}${digest}"


# Kayıtlı tuzla özeti yeniden hesaplar; karşılaştırma süresinden bilgi sızmasını azaltmak için compare_digest kullanır.
def verify_password(password, stored):
    try:
        algorithm, salt, expected = stored.split("$")
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
        return hmac.compare_digest(expected, actual)
    except (ValueError, TypeError):
        return False


# Oturum belirtecinin kendisini değil SHA-256 özetini veritabanına yazmak için kullanılır.
def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()
