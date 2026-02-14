from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./todoai_app.db" # todoai_app db adı olacak, sqlite: aynı yerde çalışacak
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgreserver/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #Session bağlantı açmak demek

Base = declarative_base() # Base modelleri oluştururken tablo için oluşturulacak dosyada kullanılır.

