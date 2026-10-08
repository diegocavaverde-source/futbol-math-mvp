# models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Conexión a SQLite para buscar un desarrolo eficiente
SQLALCHEMY_DATABASE_URL = "sqlite:///./futbol.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Jugador(Base):
    __tablename__ = "jugadores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    edad = Column(Integer)
    nacionalidad = Column(String)
    liga = Column(String)
    equipo_actual = Column(String)
    posicion = Column(String)

class Equipo(Base):
    __tablename__ = "equipos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)

class Trayectoria(Base):
    __tablename__ = "trayectorias"
    id = Column(Integer, primary_key=True, index=True)
    jugador_id = Column(Integer, ForeignKey("jugadores.id"))
    equipo_nombre = Column(String) # Simplificado para el MVP

# Crear las tablas en el archivo futbol.db
Base.metadata.create_all(bind=engine)