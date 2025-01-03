# RPA_Ceplan
RPA_Ceplan es un proyecto de automatización diseñado para gestionar tareas manuales en Ceplan, 
particularmente la subida de información en el Observatorio Nacional de Prospectiva
y la organización de sus datos.

## Estructura del proyecto

```plaintext
RPA_Ceplan/
├── classes/
│   └── navegador_observatorio.py     # Clases base para navegar, leer y escribir en el Observatorio
│   └── text_fomatting.py             # Clase para procesar texto antes de subir al Observatorio
│
│
├── datasets/                        # Carpeta para guardar productos como diccionarios, configuraciones, etc.
│   ├── info_obs.json                 # Dict con metadata de todas las fichas (producto de obtener_metadata.py)
│   ├── rubros_subrubros.json         # Dict con expresiones regulares para clasificar fichas según su código
│   └── rubros_subrubros_admin.json   # Versión simplificada de rubros_subrubros para facilitar la
│                                       navegación por el panel de administrador del Observatorio
│
│
├── actualizacion/
│   └── hipervincular_referencias.py  # Script que usa la clase WriterObs para hipervincular referencias
│   └── actualizar_fichas.py          # Script que usa la clase WriterObs para actualizar el contenido
│                                       de las fichas (ambos scripts solo para administradores)
│ 
│
├── scraping/
│   └── obtener_metadata.py           # Script que usa la clase ReaderObs para web scraping (solo administradores)
│   └── obtener_codigos_graficos.py   # Script para obtener los códigos Datawrapper de los gráficos
│                                       de todas las fichas (uso público)
│
│
├── README.md                         # Explicación general del repositorio
└── requirements.txt                  # Dependencias del proyecto
