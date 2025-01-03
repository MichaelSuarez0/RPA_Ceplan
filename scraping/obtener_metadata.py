from playwright.async_api import async_playwright
import re
import random
from datetime import datetime
from dotenv import load_dotenv
import os
import json
import asyncio
from asyncio import Semaphore
from RPA_Ceplan.classes.navegador_observatorio import ReaderObs

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASS = os.getenv("PASS")

# ruta_dict = r'C:\Users\SALVADOR\OneDrive\CEPLAN\CeplanPythonCode\RPA_Ceplan\datasets\rubros_subrubros_admin.json'
# with open(ruta_dict, "r", encoding = 'utf-8') as file:
#     rubros_subrubros_admin = json.load(file)

rubros_subrubros_admin = {
    "Eventos futuros": {
        "Señal débil": "^S\\d+$",
        "Carta salvaje": "^s\\d+$",
        "Tecnología emergente": "^TE_\\d+$"
    }
}


async def obtener_metadata_ficha(rubro, subrubro, es_territorial, timeout, headless):
    """
    Punto de entrada para scrapear metadata de las fichas
    """
    # Crear una nueva session para cada tarea
    session = ReaderObs(timeout=timeout, headless=headless)
    try:
        await session.iniciar_navegador()
        await session.login()
        await session.procesar_fichas(rubro, subrubro, territorial=es_territorial)
        print(f"Completado: rubro: {rubro}, subrubro: {subrubro}, territorial: {es_territorial}")

    except Exception as e:
        print(f"Error general en la ejecución: {e}")
    finally:
        # Asegurarse de guardar cualquier dato pendiente al finalizar la sesión
        if len(session.info_fichas) > 0:
            await session.guardar_resultados()
        await session.cerrar_navegador()


async def obtener_metadata_async(timeout, headless):
    """
    Procesa un subrubro individual con el semáforo
    """
    semaforo = Semaphore(4)
    tasks = []
    for rubro, subrubros in rubros_subrubros_admin.items():
        for subrubro, _ in subrubros.items():
            # Determinar si se trata de un subrubro territorial
            es_territorial = "Territorial" in subrubro or "territorial" in subrubro
            print(f"Ejecutando para rubro: {rubro}, subrubro: {subrubro}, territorial: {es_territorial}")

            # Crear tarea limitada pasando los valores actuales como argumentos
            async def tarea_limited(rubro, subrubro, es_territorial):
                async with semaforo:  
                    await obtener_metadata_ficha(rubro, subrubro, es_territorial, timeout, headless)

            # Crear y agregar la tarea
            tasks.append(asyncio.create_task(tarea_limited(rubro, subrubro, es_territorial)))

    await asyncio.gather(*tasks)



# Ejemplo de ejecución
if __name__ == "__main__":
    asyncio.run(obtener_metadata_async(
        timeout=20,
        headless=True)
        )


