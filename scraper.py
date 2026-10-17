import time
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import models

# El núcleo sigiloso
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Cargar configuración de base de datos
load_dotenv()
models.Base.metadata.create_all(bind=models.engine)

LIGAS_TOP_5 = {
    "Premier League": "https://fbref.com/en/comps/9/Premier-League-Stats",
    "LaLiga": "https://fbref.com/en/comps/12/La-Liga-Stats",
    "Serie A": "https://fbref.com/en/comps/11/Serie-A-Stats",
    "Bundesliga": "https://fbref.com/en/comps/20/Bundesliga-Stats",
    "Ligue 1": "https://fbref.com/en/comps/13/Ligue-1-Stats"
}

def crear_navegador():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox") 
    options.add_argument("--disable-dev-shm-usage") 
    options.add_argument("--disable-gpu") 
    return uc.Chrome(options=options)

def obtener_equipos(driver):
    equipos = {}
    for liga, url_liga in LIGAS_TOP_5.items():
        print(f"\n🗺️ Explorando la {liga} para extraer sus equipos...")
        try:
            driver.get(url_liga)
            
            print("⏳ Esperando a que cargue la clasificación (resuelve Captchas si aparecen)...")
            # Espera inteligente de hasta 45 segundos en lugar de una pausa fija
            wait = WebDriverWait(driver, 45)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table[id^='results']")))
            
            sopa = BeautifulSoup(driver.page_source, "html.parser")
            tablas = sopa.find_all("table", {"id": re.compile("^results")})
            
            if not tablas:
                print(f"⚠️ No se encontró la tabla de clasificación para {liga}.")
                continue
                
            tabla = tablas[0]
            enlaces = tabla.find_all("a", href=re.compile("^/en/squads/"))
            
            for enlace in enlaces:
                nombre = enlace.text.strip()
                url_equipo = "https://fbref.com" + enlace["href"]
                if nombre and nombre not in equipos:
                    equipos[nombre] = {"url": url_equipo, "liga": liga}
                    
            print(f"✅ Equipos detectados correctamente en la {liga}. (Llevamos {len(equipos)})")
        except Exception as e:
            print(f"❌ Error al extraer equipos de {liga}: La tabla no cargó a tiempo.")
            
    return equipos

def iniciar_extraccion():
    db = models.SessionLocal()
    print("🚀 Iniciando extracción masiva europea con Undetected ChromeDriver...")
    
    driver = crear_navegador()
    
    # 1. Generamos el diccionario de equipos dinámicamente
    lista_equipos = obtener_equipos(driver)
    print(f"\n📊 ¡Se han encontrado {len(lista_equipos)} equipos en total! Empezamos la extracción...")
    time.sleep(3)
    
    # 2. Recorremos los equipos detectados para extraer a los jugadores
    for nombre_equipo, datos in lista_equipos.items():
        print(f"\n🔍 Navegando a: {nombre_equipo} ({datos['liga']})...")
        try:
            driver.get(datos["url"])
            
            wait = WebDriverWait(driver, 60)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table[id^='stats_standard_']")))
            
            html = driver.page_source
            sopa = BeautifulSoup(html, "html.parser")
            
            tabla = sopa.find("table", {"id": re.compile("^stats_standard_")})
            if not tabla:
                print("⚠️ No se encontró la tabla de estadísticas.")
                continue
                
            tbody = tabla.find("tbody")
            if not tbody:
                print("⚠️ La tabla no tiene cuerpo (tbody).")
                continue
                
            filas = tbody.find_all("tr")
            jugadores_añadidos = 0
            
            for fila in filas:
                try:
                    classes = fila.get("class", [])
                    if "spacer" in classes or "thead" in classes:
                        continue

                    th_player = fila.find("th", {"data-stat": "player"})
                    if not th_player:
                        continue
                    nombre = th_player.text.strip()
                    
                    nacion_td = fila.find("td", {"data-stat": "nationality"})
                    nacion = nacion_td.text.strip().split()[-1] if nacion_td and nacion_td.text else "N/A"
                    
                    pos_td = fila.find("td", {"data-stat": "position"})
                    pos = pos_td.text.strip() if pos_td else ""
                    
                    edad_td = fila.find("td", {"data-stat": "age"})
                    edad = edad_td.text.strip() if edad_td else ""
                    
                    if not edad or not pos:
                        continue
                        
                    edad_int = int(edad.split("-")[0]) 

                    jugador_existente = db.query(models.Jugador).filter(models.Jugador.nombre == nombre).first()
                    
                    if not jugador_existente:
                        nuevo_jugador = models.Jugador(
                            nombre=nombre,
                            edad=edad_int,
                            nacionalidad=nacion,
                            liga=datos["liga"],
                            equipo_actual=nombre_equipo,
                            posicion=pos[:2] 
                        )
                        
                        db.add(nuevo_jugador)
                        db.commit()
                        
                        nueva_trayectoria = models.Trayectoria(jugador_id=nuevo_jugador.id, equipo_nombre=nombre_equipo)
                        db.add(nueva_trayectoria)
                        db.commit()
                        
                        jugadores_añadidos += 1
                except Exception:
                    pass 
                    
            print(f"✅ Se han añadido {jugadores_añadidos} jugadores de {nombre_equipo}.")
        
        except Exception as e:
            print(f"❌ Tiempo agotado o error en {nombre_equipo}. Error de red o antibot.")
            try:
                driver.quit()
            except Exception:
                pass
            print("🔄 Reiniciando camuflaje para el siguiente equipo...")
            driver = crear_navegador()
            time.sleep(3)
        
        print("⏳ Pausa de seguridad (5s)...")
        time.sleep(5)
        
    try:
        driver.quit()
    except Exception:
        pass
    db.close()
    print("\n🎉 ¡Extracción de toda Europa completada con éxito!")

if __name__ == "__main__":
    iniciar_extraccion()