import re
from icecream import ic

class TextFormatting:
    """
    Clase para procesar texto y referencias, incluyendo limpieza, hipervínculos, y elementos eliminados.
    """

    def __init__(self, input_text_raw, input_refs_raw):
        """
        Inicializa la clase con el texto principal y las referencias.
        
        Args:
            input_text_main (str): Texto principal a procesar.
            input_text_referencias (str): Texto con las referencias.
        """
        self.input_text_raw = input_text_raw
        self.input_refs_raw = input_refs_raw
        self.text_clean = ""
        self.referencias_internas = {}
        self.refs_clean = ""
        self.items_eliminados = []
        self.items_clean = []

    def _procesar_referencias(self):
        """
        Procesa las referencias para limpiar el texto y extraer URLs.

        Returns:
            tuple: (texto limpio, diccionario con números de referencia y URLs).
        """
        lines = self.input_refs_raw.splitlines()
        patron_a_limpiar = re.compile(r'\bAvailable:?\s*|(\.\s*)$', re.IGNORECASE)
        patron_a_extraer = re.compile(r'\[(\d+)\].*?(https?://[^\s\[\]]+)')

        temp_list = []

        for line in lines:
            referencia_limpia = re.sub(patron_a_limpiar, '', line).strip()
            temp_list.append(referencia_limpia)

            match = patron_a_extraer.search(referencia_limpia)
            if match:
                numero = int(match.group(1))
                url = match.group(2)
                self.referencias_internas[numero] = url

        self.refs_clean = '\n'.join(temp_list)

    def _procesar_parrafos(self):
        """
        Procesa los párrafos para filtrar elementos, normalizar texto y eliminar figuras/tablas.

        Returns:
            tuple: (texto procesado, elementos eliminados).
        """
        paragraphs = self.input_text_raw.split('\n')
        patron_eliminar_figuras = re.compile(r'^(Nota?|Figura)(\s+\d+)?.*$')
        patron_tabla = re.compile(r'^Tabla(\s+\d+)?.*$', re.IGNORECASE)
        patron_nota = re.compile(r'^Nota(\s*)?.*$', re.IGNORECASE)

        filtered_lines = []
        eliminar = False
        paragraph_index = -1

        for paragraph in paragraphs:
            paragraph = paragraph.strip()

            if patron_tabla.match(paragraph):
                self.items_eliminados.append((paragraph_index, paragraph))
                eliminar = True
                continue

            if patron_nota.match(paragraph):
                self.items_eliminados.append((paragraph_index, paragraph))
                eliminar = False
                continue

            if eliminar:
                continue

            if paragraph and not paragraph.endswith('.'):
                paragraph += '.'

            if patron_eliminar_figuras.match(paragraph):
                self.items_eliminados.append((paragraph_index, paragraph))
            elif paragraph:
                filtered_lines.append(paragraph)
                paragraph_index += 1

        text_clean = '\n'.join(filtered_lines)
        if text_clean.endswith('.'):
            text_clean = text_clean[:-1]

        text_clean = re.sub(
            r'[⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉]',
            lambda m: {
                '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5',
                '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '₀': '0', '₁': '1',
                '₂': '2', '₃': '3', '₄': '4', '₅': '5', '₆': '6', '₇': '7',
                '₈': '8', '₉': '9'
            }[m.group(0)],
            text_clean
        )
        self.text_clean = text_clean

    def _crear_hipervinculos(self):
        """
        Crea hipervínculos en el texto basado en las referencias internas
        y actualiza el atributo `self.text_clean` con el resultado.
        """
        pattern = re.compile(r'\[([\d,\s]+)\]')

        def replacement(match):
            numbers = match.group(1).split(',')
            links = []
            for number in numbers:
                number = int(number.strip())
                if number in self.referencias_internas and self.referencias_internas[number]:
                    links.append(f'<a href="{self.referencias_internas[number]}" target="_blank">[{number}]</a>')
                else:
                    links.append(f'[{number}]')
            return ' '.join(links)

        # Actualizar el atributo `self.text_clean` directamente
        self.text_clean = re.sub(pattern, replacement, self.text_clean)


    def _procesar_items_eliminados(self):
        """
        Procesa los elementos eliminados para generar una lista de listas con:
        [orden, numeración, título, nota].

        """
        temp_dict = {}

        for orden, texto in self.items_eliminados:
            if texto.startswith("Figura") or texto.startswith("Tabla"):
                # Extraer numeración y título
                split_text = texto.split(". ", 1)
                numeracion = split_text[0]  # Numeración como 'Figura 1' o 'Tabla 1'
                if not numeracion.endswith("."):
                    numeracion += "."  # Asegurar que termina con un punto
                titulo = split_text[1] if len(split_text) > 1 else ""
                temp_dict = {"orden": orden, "numeracion": numeracion, "titulo": titulo}
            elif texto.startswith("Nota"):
                # Añadir la nota al diccionario actual y guardar el elemento procesado
                temp_dict["nota"] = texto
                self.items_clean.append([temp_dict["orden"], temp_dict["numeracion"], temp_dict["titulo"], temp_dict["nota"]])

        

    def procesar_contenido(self):
        """
        Procesa el contenido completo: texto y referencias.
        Devuelve el texto hipervinculado, referencias limpias y items limpios.

        Returns:
            text_clean (str)
            refs_clean (str)
            items_clean (list of lists)
        """
        self._procesar_parrafos()
        self._procesar_referencias()
        self._procesar_items_eliminados()
        self._crear_hipervinculos()
        
        # Devuelve el resultado final como tuple para mantener la estructura original si es necesario
        return self.text_clean, self.refs_clean, self.items_clean
    


# texto = '''
# En la próxima década, se anticipa un auge exponencial del crimen organizado. En el futuro, la recesión económica derivada de la pandemia podría llevar a un número considerable de empresas en dificultades o incluso en quiebra al involucrarse en actividades ilícitas como el narcotráfico. El crimen organizado puede ofrecer medios para el lavado de dinero en empresas y negocios que requieren urgentemente financiamiento para continuar operando y preservar empleos. Entre 2021 y 2023, se ha registrado un incremento significativo en el Índice de Crimen Organizado a nivel mundial, ya que ha pasado de 4,87 a 5,03. Sobre la tasa de homicidios, para 2030 se espera que la tasa mundial de homicidios se reduzca en un 13 % respecto a los niveles registrados en 2015, esperando que se sitúe alrededor de 4,8 por cada 100 000 habitantes. En el periodo 2010-2023 se ha observado una disminución en la tasa mundial de víctimas de homicidio intencional por cada 100 000 habitantes, pasando de 6,09 en 2010 a 5,20 en 2023. Además, entre 2012 y 2022, la tasa mundial de trata de personas por cada 100 000 habitantes mostró una tendencia general al alza. En 2012, la tasa se situaba en 0,50 casos, pero para 2022 alcanzó los 1,39 casos por cada 100 000 personas, lo que representa un incremento relativo del 178 %.
# El crimen organizado está experimentando un auge global, impulsado por la expansión de redes criminales transnacionales que operan de manera conjunta para generar beneficios ilícitos a través de actividades como el narcotráfico, el lavado de dinero, la trata de personas y los delitos cibernéticos. Estas redes se han vuelto más sofisticadas, aprovechando tecnologías avanzadas, como las criptomonedas y las bases de datos, para facilitar sus operaciones y evadir la vigilancia. La creciente interconexión global, sumada a la urbanización y el crecimiento de las megaciudades, está consolidando centros criminales que facilitan el flujo de actividades delictivas a nivel mundial. Además, la crisis económica, el desempleo masivo y los desastres ambientales alimentan la vulnerabilidad social, creando un caldo de cultivo para el reclutamiento de individuos por parte de organizaciones criminales. La geopolítica y las debilidades de los estados también favorecen a estos grupos, que obtienen protección y apoyo estratégico de gobiernos autoritarios. De cara al futuro, se espera que los crímenes organizados se expandan aún más, con la integración de nuevas tecnologías y la intensificación de las tensiones globales, lo que dificultará el combate contra esta creciente amenaza.
# El concepto de "crimen organizado" engloba las acciones ilegales ejecutadas por redes o grupos que actúan de forma conjunta, recurriendo a la violencia, la corrupción o actividades conexas, con el objetivo de generar beneficios financieros o materiales. Estas actividades pueden tener un alcance local o extenderse a nivel transnacional [1]. 
# El Índice Global de Crimen Organizado, elaborado por la Iniciativa Global Contra el Crimen Transnacional y Organizado [1], es una herramienta clave para evaluar la dinámica del crimen en 193 Estados miembros de las Naciones Unidas. Este índice consta de dos elementos principales: la medición de la criminalidad y la evaluación de la resiliencia. El componente de criminalidad se subdivide en dos aspectos cruciales: los mercados criminales, que examinan los sistemas que sostienen el comercio ilícito, y los actores criminales, que analizan la estructura e influencia de cinco categorías de actores involucrados en el crimen organizado. Los resultados de este índice se expresan en una escala del uno al diez, donde el valor más alto (diez) indica una baja presencia o actividad de crimen organizado, mientras que el valor más bajo (uno) señala una alta actividad delictiva.
# En los últimos dos años, se ha registrado un incremento significativo en el Índice de Crimen Organizado a nivel mundial. Este índice ha pasado de 4,87 en 2021 a 5,03 en 2023, como se muestra en la Figura 1. En un análisis regional, Europa ha experimentado el mayor aumento en el índice, elevándose de 4,48 en 2021 a 4,74 en 2023, lo que representa un incremento de 0,26 puntos. Le sigue la región de Asia, cuyo índice ha crecido en 0,17 puntos, pasando de 5,30 en 2021 a 5,47 en 2023, posicionándola como la región con mayor índice de crimen organizado en comparación con sus pares. Oceanía y América también han visto un aumento en sus puntajes, con incrementos de 0,16 y 0,17, respectivamente. Por otro lado, África ha experimentado un incremento más modesto, elevándose en 0,08 puntos, desde 5,17 a 5,25.
 
# Figura 1. Mundo: índice del crimen organizado, según regiones del mundo, en 2021 y 2023 (puntajes de criminalidad).
# Nota. Elaboración Ceplan a partir de “Global Organized Crime Index”, de Global Initiative Against Transnational Organized Crime [1].
# Según la Oficina de las Naciones Unidas contra la Droga y el delito (Unodc, por sus siglas en inglés), en el periodo 2010-2023 se ha observado una disminución en la tasa mundial de víctimas de homicidio intencional por cada 100 000 habitantes, pasando de 6,09 en 2010 a 5,20 en 2023 (en 2023, alrededor de 5 personas de cada 100 000 habitantes ha sido víctimas de homicidio intencional), como se presenta en la Figura 2. A nivel regional, América presentó las mayores tasas de homicidio intencional en el periodo de análisis, aunque mostró una disminución de 16,71 en 2010 a 14,37 en 2023. De igual manera, Europa redujo su tasa de homicidio intencional de 3,48 a 2,10, en Asia, esta tasa disminuyó de 2,67 a 2,04, y en África pasó de 12,29 en 2010 a 10,57 en 2023. A excepción del resto, Oceanía mostró un aumento, elevándose de 2,89 a 2,95.
 
# Figura 2. Mundo: víctimas de homicidio intencional, según regiones del mundo, en el periodo 2010-2023 (tasa por 100 000 habitantes).
# Nota. Elaboración Ceplan a partir de la base de datos de Unodc [2]. 
# En base a la tendencia observada entre 2015 y 2022, se estima que para 2030 la tasa global de homicidios alcance los 5,1 por cada 100 000 habitantes, lo que representaría una reducción moderada del 13 % en comparación con la tasa registrada en 2015, que fue de 5,9 por cada 100 000 habitantes [3], tal como se representa en la Figura 3. No obstante, esta proyección no alcanza la reducción significativa contemplada en los Objetivos de Desarrollo Sostenible para el mismo periodo. 
 
# Figura 3. Mundo: tasa global de homicidios, en el periodo 2000-2030 (tasa por 100 000 habitantes).
# Nota. Adaptado de “The Sustainable Development Goals Report 2024”, de United Nations [3].
# Según el Observatorio del Crimen y la Violencia, con datos del Sistema Informático Nacional de Defunciones (Sinadef), el número de casos de homicidios reportados en el Perú pasó de 671 en 2017 a 1817 en 2024, lo que representa un incremento del 171 %, según se presenta en la Figura 4. El periodo de mayor crecimiento se observa entre 2020 y 2022, pues pasó de 1002 a 1516 casos. Sin embargo, en 2023 se registró una ligera disminución (1426 casos). Por su parte, en Lima, los casos de homicidios crecieron de 240 en 2017 a 752 en 2024, marcando un crecimiento del 213 %, superando el ritmo de incremento nacional. En 2024, ambas series muestran un repunte significativo, alcanzando máximos históricos.
 
# Figura 4. Mundo: homicidios según Sistema Informático Nacional de Defunciones (Sinadef), en el periodo 2017-2024 (número).
# Nota. Adaptado de “Primer reporte del Observatorio del Crimen y la Violencia”, del BCP; Banco de ideas Credicorp y CHS [4].
# En cuanto al narcotráfico, la evolución en la organización de grupos delictivos está promoviendo la expansión del narcotráfico, especialmente de cocaína, hacia nuevos mercados y el aumento del consumo en mercados ya establecidos. Esta adaptación en las cadenas de suministro reduce la vulnerabilidad de estos grupos ante intervenciones policiales tradicionales [5].
# En la extensa cuenca del Amazonas, se entrelazan múltiples facciones de narcotraficantes y organizaciones criminales que operan en colaboración estratégica y, a su vez, compiten por el control de rutas, recursos y territorios dentro de esta región de vital importancia para el tráfico ilícito y la actividad delictiva. De hecho, según la Unodc, la cuenca del Amazonas albergaría una importante concentración de grupos criminales, tal y como se ilustra en la Figura 5. En la triple frontera entre Brasil, Colombia y Perú se encuentran establecidas facciones narcotraficantes activas. Particularmente en el Perú, los grupos criminales en el Valle de los ríos Apurímac, Ene y Mantaro (Vraem) mantenían una situación de equilibrio delicado. No obstante, esta estabilidad se está viendo afectada por un aumento significativo de homicidios y actos violentos en zonas asociadas a la trata de personas. Este incremento en la violencia sugiere una alteración en el equilibrio previamente sostenido por estos grupos criminales en la región [5]. 
 
# Figura 5. América del Sur: ecosistema transnacional de grupos narcotraficantes en la Cuenca Amazónica.
# Nota. Adaptado de “World Drug Report 2023”, de Unodc [5, p. 89].
# En la región andina, entre 2020 y 2022, el cultivo de hoja de coca mostró una tendencia de crecimiento sostenido, alcanzando un aumento total del 51,5 %, al pasar de 234 177 hectáreas en 2020 a 354 900 hectáreas en 2022, como se presenta en la Figura 6. En contraste, las actividades de erradicación mostraron una disminución generalizada en la región. La erradicación total pasó de 139 131 hectáreas en 2020 a 100 779 hectáreas en 2022, lo que representa una reducción del 27,6 %. En 2022, el Perú registró un total de 95 000 hectáreas de cultivos de hoja de coca, de las cuales se logró erradicar el 22,8 %, equivalente a 21 626 hectáreas.
 
# '''

# referencias = '''
# [1] 	Forbes, «The Impact Of Digital Transformation On Business Models: Opportunities And Challenges,» 12 octubre 2023. Disponible en: https://www.forbes.com/sites/bernardmarr/2023/10/12/the-impact-of-digital-transformation-on-business-models-opportunities-and-challenges/
# [2] 	A. Libarikian, Interviewee, Building a great digital business. [Entrevista]. 20 diciembre 2020.
# [3] 	McKinsey & Company, «Social commerce: The future of how consumers interact with brands,» 19 diciembre 2022. Disponible en: https://www.mckinsey.com/capabilities/growth-marketing-and-sales/our-insights/social-commerce-the-future-of-how-consumers-interact-with-brands
# [4] 	Unctad, «Digital Economy Report 2024,» 2024. Disponible en: https://unctad.org/publication/digital-economy-report-2024
# [5] 	Predence Research, «E-commerce Market Size, Share, and Trends 2024 to 2034,» 25 septiembre 2024. Disponible en: https://www.precedenceresearch.com/e-commerce-market
# [6] 	ILO, «Realizing decent work in the platform economy,» 31 enero 2024. Disponible en: https://www.ilo.org/resource/conference-paper/ilc/113/realizing-decent-work-platform-economy
# [7] 	Roland Berger, «Megatrend 5: Technology & Innovation,» 2022. Disponible en: https://cognizium.io/uploads/resources/Roland%20Berger%20-%20Tech%20Innovation%20Trends%20-%202022.pdf
# [8] 	Datareportal, «Digital 2024: Global Overview Report,» 31 enero 2024. Disponible en: https://datareportal.com/reports/digital-2024-global-overview-report
# [9] 	Ericson, «5G will carry 80 percent of mobile data traffic globally in 2030,» 2024. Disponible en: https://www.ericsson.com/en/reports-and-papers/mobility-report/dataforecasts/mobile-traffic-forecast
# [10] 	McKinsey & Company, «Building a cloud-ready operating model for agility and resiliency,» 19 marzo 2021. Disponible en: https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights/building-a-cloud-ready-operating-model-for-agility-and-resiliency
# [11] 	Google Cloud, «Nube de datos,» 2022. Disponible en: https://cloud.google.com/data-cloud?hl=es
# [12] 	Statista, «El Big Bang del Big Data,» 22 octubre 2021. Disponible en: https://es.statista.com/grafico/26031/volumen-estimado-de-datos-digitales-creados-o-replicados-en-todo-el-mundo/
# [13] 	The Bussines Research Company, «Cloud Storage Global Market Report,» octubre 2024. Disponible en: https://www.thebusinessresearchcompany.com/report/cloud-storage-global-market-report

# '''

# procesador = TextFormatting(texto, referencias)
# texto_n, ref_n, items_n = procesador.procesar_contenido()

# ic(texto_n)
# ic(ref_n)
# ic(items_n)

    

    
