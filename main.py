# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import networkx as nx
import models

app = FastAPI(title="Fútbol Math API")

@app.get("/")
def pagina_principal():
    return FileResponse("index.html")

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- DATOS DE PRUEBA (Para no empezar con la base de datos vacía) ---
@app.post("/inicializar-datos/")
def inicializar_datos(db: Session = Depends(get_db)):
    if db.query(models.Jugador).first():
        return {"mensaje": "La base de datos ya tiene datos."}
    
    # Insertar jugadores
    j1 = models.Jugador(nombre="Messi", edad=36, nacionalidad="Argentina", liga="MLS", equipo_actual="Inter Miami", posicion="DEL")
    j2 = models.Jugador(nombre="Bellingham", edad=20, nacionalidad="Inglaterra", liga="LaLiga", equipo_actual="Real Madrid", posicion="MED")
    j3 = models.Jugador(nombre="Mbappé", edad=25, nacionalidad="Francia", liga="Ligue 1", equipo_actual="PSG", posicion="DEL")
    
    db.add_all([j1, j2, j3])
    db.commit()
    
    # Insertar trayectorias (Para el Grafo)
    t1 = models.Trayectoria(jugador_id=1, equipo_nombre="Barcelona")
    t2 = models.Trayectoria(jugador_id=1, equipo_nombre="PSG")
    t3 = models.Trayectoria(jugador_id=3, equipo_nombre="PSG")
    t4 = models.Trayectoria(jugador_id=3, equipo_nombre="Real Madrid")
    t5 = models.Trayectoria(jugador_id=2, equipo_nombre="Real Madrid")
    
    db.add_all([t1, t2, t3, t4, t5])
    db.commit()
    return {"mensaje": "Datos iniciales cargados con éxito"}

# --- JUEGO 1: LA ECUACIÓN DEL FICHAJE (Wordle) ---
@app.get("/juego/fichaje/{intento_nombre}")
def jugar_fichaje(intento_nombre: str, db: Session = Depends(get_db)):
    # 1. Fijamos un objetivo que SÍ esté en nuestra base de datos (seed_db.py)
    objetivo = db.query(models.Jugador).filter(models.Jugador.nombre == "Vinicius Junior").first()
    
    # 2. Hacemos la búsqueda flexible usando % (ej: si pones "modric", encontrará "Luka Modric")
    intento = db.query(models.Jugador).filter(models.Jugador.nombre.ilike(f"%{intento_nombre}%")).first()
    
    if not intento:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Evaluamos los colores
    resultado = {
        "nombre": intento.nombre,
        "nacionalidad": "verde" if intento.nacionalidad == objetivo.nacionalidad else "rojo",
        "liga": "verde" if intento.liga == objetivo.liga else "rojo",
        "equipo_actual": "verde" if intento.equipo_actual == objetivo.equipo_actual else "rojo",
        "posicion": "verde" if intento.posicion == objetivo.posicion else "rojo",
    }
    
    # Evaluamos la edad
    if intento.edad == objetivo.edad:
        resultado["edad"] = "verde"
    elif intento.edad > objetivo.edad:
        resultado["edad"] = "rojo_flecha_abajo"
    else:
        resultado["edad"] = "rojo_flecha_arriba"
        
    return resultado

# --- JUEGO 2: EL GRAFO DE TRASPASOS ---
@app.get("/juego/grafo/{jugador_origen}/{jugador_destino}")
def jugar_grafo(jugador_origen: str, jugador_destino: str, db: Session = Depends(get_db)):
    # Reconstruimos el grafo desde la base de datos
    G = nx.Graph()
    trayectorias = db.query(models.Trayectoria).all()
    jugadores = {j.id: j.nombre for j in db.query(models.Jugador).all()}
    
    for t in trayectorias:
        nombre_jugador = jugadores.get(t.jugador_id)
        if nombre_jugador:
            G.add_edge(nombre_jugador, t.equipo_nombre)
            
    try:
        # Aquí está la magia matemática: Dijkstra para encontrar el camino más corto
        camino = nx.shortest_path(G, source=jugador_origen, target=jugador_destino)
        pasos = (len(camino) - 1) // 2 # Dividimos entre 2 porque intercala Jugador-Equipo-Jugador
        return {"conectados": True, "camino_optimo": camino, "pasos_jugadores": pasos}
    except nx.NetworkXNoPath:
        return {"conectados": False, "mensaje": "No hay conexión posible."}
    except nx.NodeNotFound:
        raise HTTPException(status_code=404, detail="Uno de los jugadores no está en la base de datos")