# FastAPI başlangıcı, güvenlik başlıkları, ortak hata yönetimi ve arayüzün sunulması.
from contextlib import asynccontextmanager
import os
from pathlib import Path
import sqlite3
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from backend.api.routes import router
from backend.api.ot_routes import router as ot_router
from backend.db.database import ROOT, initialize
from backend.errors import DomainError
from backend.security import hash_password


# Uygulama örneğini, veritabanı yolunu, ortak hata yanıtlarını ve statik arayüz servislerini bir araya getirir.
def create_app(db_path=None):
    path=Path(db_path or os.getenv("PORTATLAS_DB", ROOT / "data/portatlas.db"))

    # Sunucu istek kabul etmeden önce veritabanını ve eksik göçleri hazırlar.
    @asynccontextmanager
    async def lifespan(app):
        initialize(path)
        yield

    app=FastAPI(title="PortAtlas API",version="0.2.0",lifespan=lifespan)
    app.state.db_path=path
    app.state.secure_cookie=os.getenv("PORTATLAS_SECURE_COOKIE", "false").lower()=="true"
    app.state.dummy_hash=hash_password("not-a-user-password")

    # Her isteğe izleme kimliği ekler; güvenlik başlıklarını ayarlar ve API yanıtlarının önbelleğe alınmasını önler.
    @app.middleware("http")
    async def headers(request:Request,call_next):
        request.state.request_id=uuid.uuid4().hex
        response=await call_next(request)
        response.headers["X-Request-ID"]=request.state.request_id
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Referrer-Policy"]="same-origin"
        response.headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if request.url.path.startswith('/api/'):
            response.headers["Cache-Control"]="no-store"
        return response

    # Bütün hata türleri için aynı JSON biçimini üretir; alan hatalarını ve istek kimliğini de taşır.
    def error(request,message,status,code,fields=None):
        return JSONResponse({"code":code,"message":message,"field_errors":fields or {},"request_id":getattr(request.state,"request_id",None)},status_code=status)

    # Beklenen iş kuralı hatasını, tanımlı HTTP durumu ve mesajla istemciye iletir.
    @app.exception_handler(DomainError)
    async def domain_error(request,exc):
        return error(request,exc.message,exc.status,exc.code)

    # Pydantic doğrulama hatalarını form alanı yollarına göre düzenleyerek 422 yanıtına dönüştürür.
    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        fields={".".join(str(x) for x in e["loc"][1:]):e["msg"] for e in exc.errors()}
        return error(request,"Form alanlarını kontrol edin.",422,"validation_error",fields)

    # Benzersizlik/yabancı anahtar gibi veritabanı bütünlük hatalarını kullanıcıya kayıt çakışması olarak bildirir.
    @app.exception_handler(sqlite3.IntegrityError)
    async def integrity_error(request,exc):
        return error(request,"Kayıt çakışması: kod/etiket zaten kullanılıyor veya seçilen uç başka bir aktif bağlantıya ait.",409,"integrity_conflict")

    # Kilitlenmede yeniden denenebilir 503 döndürür; diğer SQLite çalışma hatalarını ayrıntıyı sızdırmadan günlüğe alır.
    @app.exception_handler(sqlite3.OperationalError)
    async def operational_error(request,exc):
        if "locked" in str(exc).lower():
            return error(request,"Veritabanı meşgul. Kaydı kontrol edip yeniden deneyin.",503,"database_busy")
        logging.exception("Database error, request %s",getattr(request.state,"request_id",""))
        return error(request,"İşlem tamamlanamadı.",500,"database_error")

    # Çekirdek ve OT uçları aynı uygulamada çalışır; /static yalnızca frontend dosyalarını servis eder.
    app.include_router(router)
    app.include_router(ot_router)
    app.mount("/static",StaticFiles(directory=ROOT/"frontend"),name="static")

    # Vanilla JavaScript arayüzünün giriş HTML dosyasını sunar.
    @app.get("/",include_in_schema=False)
    def index():
        return FileResponse(ROOT/"frontend/index.html")

    # Sunucunun yanıt verebildiğini bildirir; ayrıntılı veritabanı veya ağ sağlık kontrolü yapmaz.
    @app.get("/health",include_in_schema=False)
    def health():
        return {"status":"ok"}

    return app


app=create_app()
