from models import SessionLocal, Jugador, Trayectoria

# Lista de jugadores de prueba con conexiones cruzadas (perfecto para el grafo)
datos_jugadores = [
    {"nombre": "Vinicius Junior", "edad": 23, "nacion": "BRA", "liga": "LaLiga", "equipo": "Real Madrid", "pos": "FW"},
    {"nombre": "Rodrygo", "edad": 23, "nacion": "BRA", "liga": "LaLiga", "equipo": "Real Madrid", "pos": "FW"},
    {"nombre": "Luka Modric", "edad": 38, "nacion": "CRO", "liga": "LaLiga", "equipo": "Real Madrid", "pos": "MF"},
    {"nombre": "Eduardo Camavinga", "edad": 21, "nacion": "FRA", "liga": "LaLiga", "equipo": "Real Madrid", "pos": "MF"},
    {"nombre": "Aurelien Tchouameni", "edad": 24, "nacion": "FRA", "liga": "LaLiga", "equipo": "Real Madrid", "pos": "MF"},
    {"nombre": "Jude Bellingham", "edad": 20, "nacion": "ENG", "liga": "LaLiga", "equipo": "Real Madrid", "pos": "MF"}, # <-- EL PUENTE
    {"nombre": "Robert Lewandowski", "edad": 35, "nacion": "POL", "liga": "LaLiga", "equipo": "Barcelona", "pos": "FW"},
    {"nombre": "Ilkay Gundogan", "edad": 33, "nacion": "GER", "liga": "LaLiga", "equipo": "Barcelona", "pos": "MF"},
    {"nombre": "Ousmane Dembele", "edad": 26, "nacion": "FRA", "liga": "Ligue 1", "equipo": "PSG", "pos": "FW"},
    {"nombre": "Erling Haaland", "edad": 23, "nacion": "NOR", "liga": "Premier League", "equipo": "Manchester City", "pos": "FW"},
    {"nombre": "Kevin De Bruyne", "edad": 32, "nacion": "BEL", "liga": "Premier League", "equipo": "Manchester City", "pos": "MF"}
]
# Trayectorias históricas de cada uno de los jugadores
historial_trayectorias = {
    "Vinicius Junior": ["Real Madrid"],
    "Rodrygo": ["Real Madrid"],
    "Luka Modric": ["Real Madrid", "Tottenham"],
    "Eduardo Camavinga": ["Real Madrid", "Rennes"],
    "Aurelien Tchouameni": ["Real Madrid", "Monaco"],
    "Jude Bellingham": ["Real Madrid", "Borussia Dortmund", "Birmingham"], # <-- CONECTA AMBAS ISLAS
    "Robert Lewandowski": ["Barcelona", "Bayern Munich", "Borussia Dortmund"],
    "Ilkay Gundogan": ["Barcelona", "Manchester City", "Borussia Dortmund"],
    "Ousmane Dembele": ["PSG", "Barcelona", "Borussia Dortmund"],
    "Erling Haaland": ["Manchester City", "Borussia Dortmund", "Red Bull Salzburg"],
    "Kevin De Bruyne": ["Manchester City", "Chelsea", "Wolfsburg"]
}

def poblar_base_de_datos():
    db = SessionLocal()
    
    print("Inyectando jugadores y calculando grafos...")
    
    for data in datos_jugadores:
        # 1. Insertamos el jugador si no existe
        jugador = db.query(Jugador).filter(Jugador.nombre == data["nombre"]).first()
        if not jugador:
            jugador = Jugador(
                nombre=data["nombre"],
                edad=data["edad"],
                nacionalidad=data["nacion"],
                liga=data["liga"],
                equipo_actual=data["equipo"],
                posicion=data["pos"]
            )
            db.add(jugador)
            db.commit()
            db.refresh(jugador)
            
            # 2. Le añadimos todos los equipos en los que ha estado para el Juego de Grafos
            equipos = historial_trayectorias.get(data["nombre"], [data["equipo"]])
            for equipo in equipos:
                trayectoria = Trayectoria(jugador_id=jugador.id, equipo_nombre=equipo)
                db.add(trayectoria)
            
            db.commit()
            print(f"✅ Añadido: {data['nombre']} y su historial de {len(equipos)} equipos.")
        else:
            print(f"⚠️ El jugador {data['nombre']} ya estaba en la base de datos.")
            
    db.close()
    print("\n🚀 ¡Base de datos lista para jugar!")

if __name__ == "__main__":
    poblar_base_de_datos()