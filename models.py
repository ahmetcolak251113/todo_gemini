from database import Base # modeller oluşturulurken kullanılır
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

# db değişikliklerini migration dediğimiz değişiklik ile yapıyoruz (sonraki bölümlerde yapılacak)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True) # unique= True ile tek girdi sağlanımı
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)
    phone_number = Column(String)

# Migration için alembic kurulmalı ardından % alembic init alembic





