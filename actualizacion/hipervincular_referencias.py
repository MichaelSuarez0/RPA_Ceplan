from playwright.sync_api import sync_playwright
import re
import random
from datetime import datetime
from dotenv import load_dotenv
import os
import json
from RPA_Ceplan.classes.navegador_observatorio import NavegadorObs, WriterObs
from RPA_Ceplan.classes.text_formatting import TextFormatting

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASS = os.getenv("PASS")

ruta_dict = r'C:\Users\SALVADOR\OneDrive\CEPLAN\CeplanPythonCode\RPA_Ceplan\datasets\rubros_subrubros.json'

with open(ruta_dict, "r", encoding = 'utf-8') as file:
    rubros_subrubros = json.load(file)

# Función para procesar múltiples fichas y aplicar hipervínculos
def hipervincular_referencias(codigos_ficha, timeout):
    session = WriterObs(timeout=timeout)
    session.iniciar_navegador()
    try:
        session.login()
        for codigo_ficha in codigos_ficha:
            try:
                session.identificar_rubro(codigo_ficha)
                session.agregar_enlace_a_casillas(codigo_ficha) # Verificar si solo los activos
                session.volver_a_inicio()
                print(f"Ficha {codigo_ficha} con referencias hipervinculadas")
            except Exception as e:
                print(f"Error al procesar la ficha {codigo_ficha}: {e}")
    finally:
        session.cerrar_navegador()


#Llamada al flujo principal
if __name__ == "__main__":
    # Hipervincular referencias de múltiples fichas
    # codigos_ficha = [f"t{i}" for i in range(1, 10)]  # Generar códigos dinámicamente
    codigos_ficha = ["r4_apu"] # individual
    hipervincular_referencias(codigos_ficha)
   