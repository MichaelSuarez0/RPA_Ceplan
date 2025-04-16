import asyncio
from asyncio import Semaphore
from playwright.async_api import async_playwright
from datetime import datetime
from dotenv import load_dotenv
import os
import json
from RPA_Ceplan.classes.navegador_observatorio import WriterObs

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASS = os.getenv("PASS")

# Función para procesar múltiples fichas y aplicar hipervínculos
async def hipervincular_referencias(sem:Semaphore, codigo_ficha, timeout, headless = True):
    async with sem:
        session = WriterObs(timeout=timeout, headless=headless)
        await session.iniciar_navegador()    
        try:
            await session.login()
            await session.identificar_rubro(codigo_ficha)
            await session.agregar_enlace_a_casillas(codigo_ficha) # Verificar si solo los activos
            await session.volver_a_inicio()
            print(f"Ficha {codigo_ficha} con referencias hipervinculadas")
        except Exception as e:
            print(f"Error al procesar la ficha {codigo_ficha}: {e}")
        finally:
            await session.cerrar_navegador()

async def hipervincular_referencias_async(codigos_ficha:list[str], timeout:float, sem:int, headless:bool):
    sem_limit = Semaphore(sem)
    tasks = [hipervincular_referencias(sem_limit, codigo_ficha, timeout, headless) for codigo_ficha in codigos_ficha]
    await asyncio.gather(*tasks)

#Llamada al flujo principal
if __name__ == "__main__":
    # codigos_ficha = [f"t{i}" for i in range(1, 10)]  # Generar códigos dinámicamente
    asyncio.run(hipervincular_referencias_async(
        codigos_ficha= ["t2"],
        timeout= 150,
        sem= 3,
        headless= False
    ))
   