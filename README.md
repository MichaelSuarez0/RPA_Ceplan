# RPA_Ceplan
RPA_Ceplan es un proyecto de automatización diseñado para gestionar tareas manuales que consumen mucho tiempo en Ceplan, como la carga de documentos, la extracción de datos y su organización.
RPA_Ceplan is an automation project designed to handle time-consuming manual tasks in Ceplan, such as document uploading, data extraction and organization

# Estructura del proyecto

RPA_Ceplan/
│
├── classes/
│   ├── navegador_observatorio.py    # Clases base para navegar, leer y escribir
│
├── scraping/
│   ├── obtener_metadata.py          # Script que usa la clase ReaderObs para scraping a partir del panel de administrador
│
├── actualizacion/
│   ├── actualizar_fichas.py         # Script que usa la clase WriterObs para actualizar el contenido de las fichas
│
├── productos/                       # Carpeta para guardar productos como diccionarios, configuraciones, etc.
│   ├── info_obs.json                # Dict con metadata de todas las fichas (producto de obtener_metada.py)
│   ├── rubros_subrubros.json        # Dict con expresiones regulares para clasificar cualquier tipo de ficha según su código
│   ├── rubros_subrubros_admin.json  # rubros_subrubros simplificado para navegar por el panel de administrador en el Obs.
│
├── README.md                        # Explicación general del repositorio
└── requirements.txt                 # Dependencias del proyecto
