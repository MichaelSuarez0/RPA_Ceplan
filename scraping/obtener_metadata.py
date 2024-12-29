from playwright.sync_api import sync_playwright
import re
import random
from datetime import datetime
from dotenv import load_dotenv
import os
import json
from RPA_Ceplan.classes.navegador_observatorio import NavegadorObs, ReaderObs

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASS = os.getenv("PASS")

ruta_dict = r'C:\Users\SALVADOR\OneDrive\CEPLAN\CeplanPythonCode\RPA_Ceplan\datasets\rubros_subrubros_admin.json'
with open(ruta_dict, "r", encoding = 'utf-8') as file:
    rubros_subrubros_admin = json.load(file)


def obtener_metadata(timeout):
    """
    Punto de entrada para scrapear metadata de las fichas
    """
    session = ReaderObs(timeout=timeout)
    session.iniciar_navegador()
    try:
        session.login()

        for rubro, subrubros in rubros_subrubros_admin.items():
            for subrubro, _ in subrubros.items():
                # Determinar si se trata de un subrubro territorial
                es_territorial = "Territorial" in subrubro or "territorial" in subrubro
                print(f"Ejecutando para rubro: {rubro}, subrubro: {subrubro}, territorial: {es_territorial}")

                session.procesar_fichas(rubro, subrubro, territorial=es_territorial)
                session.guardar_resultados(rubro, subrubro)    

    except Exception as e:
        print(f"Error general en la ejecución: {e}")
    finally:
        session.cerrar_navegador()



# Ejemplo de ejecución
if __name__ == "__main__":
    obtener_metadata(timeout=20)