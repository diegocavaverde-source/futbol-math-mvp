from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
import unicodedata
import models

# Aseguramos que las tablas existan al arrancar
models.Base.metadata.create_all(bind=models.engine)

app = FastAPI(title="Futbol Math API")

# Permisos CORS para que tu index.html pueda comunicarse con esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia de la base de datos
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def inicio():
    return {"estado": "API de Futbol Math funcionando al 100%"}

@app.get("/api/jugadores")
def listar_jugadores(limite: int = 20, db: Session = Depends(get_db)):
    """Devuelve una lista de jugadores para comprobaciones rápidas"""
    jugadores = db.query(models.Jugador).limit(limite).all()
    return jugadores

@app.get("/api/jugador/aleatorio")
def jugador_aleatorio(dificultad: str = "facil", db: Session = Depends(get_db)):
    """Devuelve un único jugador al azar según la dificultad elegida"""
    
    # Lista de equipos top para el modo fácil
    equipos_top = [
        "Real Madrid", "Barcelona", "Atletico Madrid", "Manchester City", 
        "Arsenal", "Liverpool", "Chelsea", "Manchester Utd", "Tottenham",
        "Bayern Munich", "Dortmund", "Bayer Leverkusen", 
        "Paris S-G", "Inter", "Milan", "Juventus", "Napoli"
    ]
    
    # Equipos de tabla baja/recién ascendidos a excluir en el modo difícil
    equipos_proscritos = [
        "Monza", "Venezia", "Empoli", "Lecce", "Genoa",
        "Leganés", "Valladolid", "Getafe", "Las Palmas",
        "Angers", "Le Havre", "Nantes", "Montpellier",
        "St. Pauli", "Holstein Kiel", "Bochum",
        "Ipswich Town", "Southampton", "Leicester City"
    ]
    
    query = db.query(models.Jugador)
    
    if dificultad == "facil":
        # Solo busca en los equipos gigantes
        query = query.filter(models.Jugador.equipo_actual.in_(equipos_top))
    elif dificultad == "dificil":
        # Busca en todos, EXCEPTO en los equipos proscritos
        query = query.filter(models.Jugador.equipo_actual.notin_(equipos_proscritos))
        
    jugador = query.order_by(func.random()).first()
    if not jugador:
        raise HTTPException(status_code=404, detail="No se encontraron jugadores")
    return jugador

def limpiar_texto(texto: str):
    """Elimina tildes y pasa a minúsculas"""
    texto = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn').lower()

@app.get("/api/buscar/{nombre}")
def buscar_jugador(nombre: str, db: Session = Depends(get_db)):
    """Buscador definitivo: ignora mayúsculas y tildes"""
    print(f"\n🔍 Buscando el texto: '{nombre}' (A prueba de tildes y mayúsculas)")
    
    # Nos traemos todos los jugadores y dejamos que Python haga la magia
    todos_los_jugadores = db.query(models.Jugador).all()
    busqueda_limpia = limpiar_texto(nombre)
    
    resultados = []
    for jugador in todos_los_jugadores:
        nombre_limpio = limpiar_texto(jugador.nombre)
        if busqueda_limpia in nombre_limpio:
            resultados.append(jugador)
            if len(resultados) == 5: # Máximo 5 sugerencias para no saturar la lista
                break
                
    if not resultados:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
        
    return resultados