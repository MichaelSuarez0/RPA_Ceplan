from datetime import datetime
import os
import json
import asyncio
from asyncio import Semaphore
from RPA_Ceplan.classes.navegador_observatorio import ReaderObs
import logging

script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, "..", "logs", "obtener_metadata.log")
ruta_dict = os.path.join(script_dir, "..", "datasets", "rubros_subrubros_admin.json")

# Configuración básica del logging
logging.basicConfig(
    level=logging.ERROR,  # Nivel de registro (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  
    handlers=[
    logging.FileHandler(log_path, mode='a', encoding='utf-8'),  # Archivo en UTF-8
    logging.StreamHandler()  # También mostrar logs en la consola
    ]
)

# Diccionario principal
with open(ruta_dict, "r", encoding = 'utf-8') as file:
    rubros_subrubros_admin = json.load(file)


# rubros_subrubros_admin = {
#     "Eventos futuros": {
#         "Señal débil": "^S\\d+$",
#         "Carta salvaje": "^s\\d+$",
#         "Tecnología emergente": "^TE_\\d+$"
#     }
# }

rubros_subrubros_admin = {
    "Megatendencias": "^t\\d+$"
#    "Fuerzas primarias": "^fp\\d+$"
}
#     "Tendencias": {
#         "Tendencia territorial": "^t\\d+_\\w+",
#         },
#     "Riesgos": {
#         "Riesgo Territorial": "^r\\d+_\\w+"
#     },
#     "Oportunidades": {
#         "Oportunidad territorial": "^o\\d+_\\w+"
#     },
# }


async def obtener_metadata_ficha(rubro: str, subrubro: str, es_territorial: bool, timeout: int, headless: bool):
    """
    Punto de entrada para scrapear metadata de las fichas
    """
    # Crear una nueva session para cada tarea
    session = ReaderObs(timeout=timeout, headless=headless)
    try:
        await session.iniciar_navegador()
        await session.login()
        await session.scrapear_fichas(rubro, subrubro, territorial=es_territorial)
        logging.info(f"Completado: rubro: {rubro}, subrubro: {subrubro}, territorial: {es_territorial}")

    except Exception as e:
        logging.error(f"Error general en la ejecución: {e}")
    finally:
        # Asegurarse de guardar cualquier dato pendiente al finalizar la sesión
        if len(session.info_fichas) > 0:
            await session.guardar_resultados()
        await session.cerrar_navegador()


async def obtener_metadata_async(timeout: int, headless: bool, semaphore: int = 4):
    """
    Procesa todos los rubros y subrubros con un límite de operaciones concurrentes
    """
    semaforo = Semaphore(semaphore)
    tasks = []
    
    # Función auxiliar para crear tareas con semáforo
    async def ejecutar_con_semaforo(func):
        async with semaforo:
            await func
    
    for rubro, subrubros in rubros_subrubros_admin.items():
        if rubro in ["Megatendencias", "Fuerzas primarias"]:
            logging.info(f"Ejecutando para rubro especial: {rubro}")
            tarea = ejecutar_con_semaforo(
                obtener_metadata_ficha(rubro, None, False, timeout, headless)
            )
            tasks.append(asyncio.create_task(tarea))
        else:
            # Caso normal: rubros con subrubros
            for subrubro in subrubros.keys():
                es_territorial = "territorial" in subrubro.lower()
                logging.info(f"Ejecutando para rubro: {rubro}, subrubro: {subrubro}, territorial: {es_territorial}")
                
                tarea = ejecutar_con_semaforo(
                    obtener_metadata_ficha(rubro, subrubro, es_territorial, timeout, headless)
                )
                tasks.append(asyncio.create_task(tarea))
    
    # Esperar a que todas las tareas terminen
    await asyncio.gather(*tasks)


# TODO: Si li.btn no está visible, actualizar la página
# Ejemplo de ejecución
if __name__ == "__main__":
    asyncio.run(obtener_metadata_async(
        timeout=12,
        headless=False,
        semaphore = 4
        )
    )


