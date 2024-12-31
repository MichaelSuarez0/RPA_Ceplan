import re
import json
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from icecream import ic
import pandas as pd
import asyncio

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASS = os.getenv("PASS")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Construir la ruta relativa, ir "un paso atrás" y luego acceder a la carpeta 'datasets'
base_dir = os.path.dirname(os.path.abspath(__file__))  # Obtener el directorio absoluto del script

ruta_info_obs= os.path.join(base_dir, '..', 'datasets', 'info_obs.json')  
with open(ruta_info_obs, 'r', encoding='utf-8') as file:
    info_obs = json.load(file)

ruta_figuras_parcial= os.path.join(base_dir, '..', 'datasets', 'figuras_parcial.json')  # Subir un paso y buscar 'datasets'

figuras = {}
contador_fichas = 0

# Función para guardar los datos correctamente
async def guardar_datos(figuras_parcial):
    # Comprobar si el archivo existe para no sobrescribir datos previos
    if os.path.exists(ruta_figuras_parcial):
        with open(ruta_figuras_parcial, 'r') as f:
            # Cargar los datos actuales del archivo
            figuras_actuales = json.load(f)
    else:
        # Si el archivo no existe, crear un diccionario vacío
        figuras_actuales = {}

    # Añadir las nuevas figuras al archivo
    figuras_actuales.update(figuras_parcial)

    # Escribir el archivo de nuevo con los datos completos
    with open(ruta_figuras_parcial, 'w') as f:
        json.dump(figuras_actuales, f, ensure_ascii=False, indent=4)
    print(f'Checkpoint guardado con {contador_fichas} fichas')    

# Función para procesar una página y obtener los gráficos
async def procesar_pagina(codigo, enlace, context):
    global contador_fichas
    page = await context.new_page()
    datos_figuras = []

    try:
        await page.goto(enlace)

        # Esperar a que los gráficos se carguen
        await page.wait_for_selector("iframe[id*='datawrapper-chart']", timeout=20000)

        # Dar tiempo adicional para que se complete la carga dinámica
        await page.wait_for_timeout(500)

        # Obtener todos los iframes de Datawrapper de la página
        iframes = await page.query_selector_all("iframe[id*='datawrapper-chart']")

        for iframe in iframes:
            iframe_id = await iframe.get_attribute('id')
            if iframe_id:
                match = re.search(r'datawrapper-chart-([a-zA-Z0-9]+)', iframe_id)
                if match:
                    datos_figuras.append(match.group(1))

        # Guardar los datos en el diccionario de figuras
        figuras[codigo] = {"figuras": datos_figuras}

        # Incrementar el contador de fichas procesadas
        contador_fichas += 1
        print(f"Fichas procesadas: {contador_fichas}")  # Aquí puedes usar 'ic' si prefieres

    except Exception as e:
        print(f'Hubo un error con el código {codigo}: {e}')

    

    except Exception as e:
        # Si ocurre un error, capturarlo y mostrarlo
        print(f'Hubo un error con el código {codigo}: {e}')

    finally:
        # Almacenar los datos si son más de 50
        if len(figuras) % 50 == 0:
            await guardar_datos(figuras)

        # Cerrar la página
        await page.close()
    
    return codigo  # Devolver el código para poder hacer un seguimiento

async def procesar_con_límite(sem, codigo, enlace, context):
    async with sem:  # Limita el número de tareas concurrentes
        return await procesar_pagina(codigo, enlace, context)

async def obtener_codigo_gráficos(tareas = 5):
    sem = asyncio.Semaphore(tareas)  # Máximo de tareas concurrentes
    tasks = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=60)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})

        for codigo, datos in info_obs.items():
            if datos.get("estado") == "Activo":
                enlace = f'https://observatorio.ceplan.gob.pe/ficha/{codigo}'
                tasks.append(procesar_con_límite(sem, codigo, enlace, context))

        # Ejecutar las tareas con concurrencia limitada
        await asyncio.gather(*tasks)
        await browser.close()

# Ejecución de la función principal
if __name__ == "__main__":
    asyncio.run(obtener_codigo_gráficos(
        tareas = 5)
        )





