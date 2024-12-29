import asyncio
from playwright.sync_api import async_playwright
import re
from datetime import datetime
from dotenv import load_dotenv
import os
import json

# Credenciales
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASS = os.getenv("PASS")

# Variables globales
ruta_dict = r'C:\Users\SALVADOR\OneDrive\CEPLAN\CeplanPythonCode\RPA_Ceplan\datasets\rubros_subrubros.json'
with open(ruta_dict, "r", encoding = 'utf-8') as file:
    rubros_subrubros = json.load(file)

ruta_dict = r'C:\Users\SALVADOR\OneDrive\CEPLAN\CeplanPythonCode\RPA_Ceplan\datasets\rubros_subrubros_admin.json'
with open(ruta_dict, "r", encoding = 'utf-8') as file:
    rubros_subrubros_admin = json.load(file)

mapeo_tematica = {
        "1": "Social",
        "2": "Económica",
        "3": "Ambiental",
        "4": "Tecnológica",
        "13": "Política",
        "14": "Ética",
        "15": "General"
    }


class NavegadorObs():
    def __init__(self, timeout):
        self.email = EMAIL
        self.password = PASS
        self.timeout = timeout
        self.playwright = None
        self.browser = None
        self.page = None

    async def iniciar_navegador(self):
        """
        Inicia el navegador y configura la página.
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False, slow_mo=self.timeout)
        context = await self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = await context.new_page()

        
    async def login(self):
        """
        Realiza el inicio de sesión en la página.
        """
        await self.page.goto('https://observatorio.ceplan.gob.pe/')
        await self.page.evaluate("document.body.style.zoom='90%'")

        await self.page.click('.icon-header.fa.fa-user.fa-3')
        await self.page.click('a[routerlink="login"]')

        await self.page.fill('input[name="email"]', self.email)
        await self.page.fill('input[name="pass"]', self.password)
        await self.page.click('.btn.btn-outline-dark.btn-secure')

    async def volver_a_inicio(self):
        """
        Navega de vuelta al panel de administrador
        """
        await self.page.click('i.icon-header.fa.fa-user.fa-3')
        await self.page.wait_for_selector('a[href="/adm/tendencia"]')
        await self.page.click('a[href="/adm/tendencia"]')
    
    async def cerrar_navegador(self):
        """
        Cierra el navegador y libera los recursos.
        """
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


    async def identificar_rubro(self, codigo_ficha):
        """
        Selecciona automáticamente el rubro y subrubro basándose en el código de ficha,
        y abre la ficha deseada.
        
        Args:
            codigo_ficha (str): Código de la ficha que se desea abrir.
        
        Raises:
            ValueError: Si no se encuentra un rubro o subrubro correspondiente al código.
        """
        # Detección automática de rubro y subrubro usando regex
        rubro_encontrado = None
        subrubro_encontrado = None
        
        for rubro, subrubros in rubros_subrubros.items():
            for subrubro, patron in subrubros.items():
                if re.match(patron, codigo_ficha):  # Compara el código de ficha con el patrón
                    rubro_encontrado = rubro
                    subrubro_encontrado = subrubro
                    break
            if rubro_encontrado and subrubro_encontrado:
                break

        # Validar detección
        if not rubro_encontrado or not subrubro_encontrado:
            raise ValueError(f"No se encontró un rubro o subrubro para el código de ficha: {codigo_ficha}")

        # Imprimir el rubro y subrubro encontrados
        print(f"Rubro encontrado: {rubro_encontrado}, Subrubro encontrado: {subrubro_encontrado}")

        # Seleccionar el rubro
        await self.page.wait_for_selector('li.btn-org[routerlinkactive="active"]')
        await self.page.click(f'li.btn-org:has-text("{rubro_encontrado}")')

        # Seleccionar el subrubro
        await self.page.wait_for_selector('a.col-sm-3.btn-org')
        await self.page.click(f'a.col-sm-3.btn-org:has-text("{subrubro_encontrado}")')


    async def seleccionar_icono(self, codigo_ficha, orden):
        """
        Selecciona un ícono dentro de una fila específica basada en el código de la ficha y el índice.

        Args:
            self.page: Página de Playwright.
            codigo_ficha (str): Código de la ficha que se desea localizar.
            orden (int): Índice (nth) del ícono dentro de la fila.
                0: editar texto
                1: editar gráficos
                2: editar referencias
                3: editar fuentes primarias
                4: editar metadata

        Raises:
            ValueError: Si no se encuentra la ficha con el código proporcionado.
        """
        await self.page.wait_for_selector('tr.tbody-detail')  # Esperar a que las filas estén visibles
        ficha_element = await self.page.locator(f'tr.tbody-detail:has-text("{codigo_ficha}") a.a-icon').nth(orden)
        
        if ficha_element.count() == 0:
            raise ValueError(f"No se encontró la ficha con código: {codigo_ficha}")
        
        await ficha_element.click()

    
    async def recopilar_estado_filas(self, rows):
        """
        Recopila el estado de las filas en la tabla de acuerdo a si están activas o inactivas.

        Args:
            rows (Locator): El locator de las filas de la tabla donde están las casillas.

        Returns:
            list: Lista de booleanos donde True significa que la casilla está activa y False que está inactiva.
        """
        row_count = await rows.count()
        row_status = []

        # Paso 1: Recopilar el estado de cada fila
        for index in range(row_count):
            label_locator = rows.nth(index).locator('td.text-center div.label-inactive, td.text-center div.label-active')
            if await label_locator.is_visible():
                label = await label_locator.inner_text()
                row_status.append(label.strip() == "ACTIVO")
            else:
                row_status.append(False)

        return row_status



class WriterObs(NavegadorObs):
    def __init__(self, timeout):
        super().__init__(timeout)

    async def llenar_campo(self, selector, valor, click=False):
        await self.page.wait_for_selector(selector, state='visible')
        await self.page.locator(selector).scroll_into_view_if_needed()
        # Si se debe hacer clic en el campo antes de llenarlo
        if click:
            await self.page.locator(selector).click()
            await self.page.wait_for_timeout(self.timeout)
        await self.page.fill(selector, str(valor))
        await self.page.wait_for_timeout(self.timeout)

    async def click_selector(self, selector):
        await self.page.wait_for_selector(selector)
        await self.page.locator(selector).scroll_into_view_if_needed()
        await self.page.locator(selector).click()
        await self.page.wait_for_timeout(self.timeout)

    async def desactivar_casillas_activadas(self, rows, desactivar=True):
        """
        Desactiva las casillas activadas según el parámetro 'desactivar'.

        Args:
            rows (Locator): El locator de las filas de la tabla donde están las casillas.
            desactivar (bool): Si es True, desactiva las casillas activadas. Si es False, activa las casillas inactivas.

        Returns:
            None
        """
        row_status = await self.recopilar_estado_filas(rows)

        # Paso 2: Desactivar las casillas según el parámetro 'desactivar'
        for index, is_active in enumerate(row_status):
            if (desactivar and is_active) or (not desactivar and not is_active):
                action = "Desactivando" if desactivar else "Activando"
                pencil_icon = rows.nth(index).locator('a.a-icon i.fa-pencil')
                await pencil_icon.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(self.timeout / 3)

                if await pencil_icon.is_visible():
                    try:
                        await pencil_icon.click()  # Aquí se hace clic en el lápiz
                        await self.page.evaluate('document.querySelector("#switch1").click()')

                        # Hacer hover sobre el botón y luego clic (mejora la consistencia)
                        save_button = self.page.locator('button.btn.btn-outline-primary.btn-block')
                        await save_button.hover()  # Hover sobre el botón
                        await self.page.click('button.btn.btn-outline-primary.btn-block')
                        await self.page.wait_for_timeout(self.timeout / 3)

                        # Esperar a que la tabla se recargue completamente antes de continuar
                        await self.page.wait_for_selector('tr.tbody-detail', state='visible')
                    except Exception as e:
                        print(f"Error al procesar la fila {index + 1}: {e}")
                else:
                    try:
                        print(f"Lápiz de la fila {index + 1} no es visible, intentando alternativa")
                        await self.page.wait_for_timeout(30)

                        # Hacer click en el lápiz con js
                        await self.page.evaluate('''var pencil = document.querySelector('a.a-icon i.fa-pencil');
                                            if (pencil) {
                                                pencil.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                                pencil.click();
                                            }''')

                        # Cambiar el estado del switch usando JavaScript
                        await self.page.evaluate('document.querySelector("#switch1").click()')

                        # Hacer hover sobre el botón y luego clic
                        save_button = self.page.locator('button.btn.btn-outline-primary.btn-block')
                        await save_button.hover()  # Hover sobre el botón
                        await self.page.click('button.btn.btn-outline-primary.btn-block')

                        # Esperar a que la tabla se recargue completamente antes de continuar
                        await self.page.wait_for_selector('tr.tbody-detail', state='visible')
                        print(f"Fila {index + 1} ha sido procesada por el método alternativo.")
                    except Exception as e:
                        print(f"No se pudo hacer clic en el lápiz de la fila {index + 1}")

    
        
            
         ################ INSERTAR TEXTO ACTUALIZADO ##################
    async def actualizar_sumilla(self, codigo_ficha, texto_con_hipervínculos, timeout=50):
        """
        Actualiza la sumilla de una ficha y modifica la fecha de actualización en la interfaz.

        Args:
            self.page (self.page): Página de Playwright.
            codigo_ficha (str): Código de la ficha que se desea procesar.
            texto_con_hipervínculos (str): Texto procesado con hipervínculos para la sumilla.
            timeout (int, optional): Tiempo de espera en milisegundos para las operaciones 
                (por defecto: 50).

        Raises:
            Exception: Si ocurre algún problema al insertar la fecha de actualización.
        """
        # Seleccionar el ícono del lápiz (orden 4) para editar toda la ficha
        await self.seleccionar_icono(self, codigo_ficha, 4)

        # Obtener el primer párrafo del texto
        primer_parrafo = texto_con_hipervínculos.split('\n')[0]
        
        # Rellenar el campo de texto con el primer párrafo
        await self.llenar_campo(self, 'textarea[formcontrolname="summary"]', primer_parrafo)

        # Seleccionar la fecha de hoy
        today = datetime.today().strftime('%Y-%m-%d')  # Cambiar el formato a YYYY-MM-DD

        try:
            # Rellenar el campo de la fecha
            await self.llenar_campo('input[placeholder="Actualización"]', today, timeout, click=True)
        except Exception as e:
            print(f"No se insertó la fecha, por favor revisar: {e}")


        # Guardar los cambios
        #self.page.evaluate('document.querySelector("#switch1").click()')
        await self.page.click('button.btn.btn-outline-primary.btn-block')
        print("Se actualizó la sumilla y fecha de actualización")



    async def actualizar_texto(self, codigo_ficha, texto_con_hipervínculos):
        """
        Actualiza el texto asociado a una ficha, eliminando el contenido previo y 
        guardando el nuevo contenido procesado.

        Args:
            self.page (self.page): Página de Playwright.
            codigo_ficha (str): Código de la ficha a procesar.
            texto_con_hipervínculos (str): Texto procesado que reemplazará el contenido existente.
            timeout (int, optional): Tiempo de espera en milisegundos para las operaciones 
                (por defecto: 50).

        Raises:
            Exception: Si ocurre algún error al interactuar con los elementos de la página.
        """
        # Seleccionar el ícono de texto (orden 0)
        await self.seleccionar_icono(codigo_ficha, 0)

        ### Paso 1: Reemplazar sección anterior
        # Darle click al lápiz
        try:
            await self.click_selector('i.fa-pencil')
            # Apagar la subsección y guardar
            await self.page.evaluate('document.querySelector("#switch1").click()')
            await self.click_selector('button.btn.btn-outline-primary.btn-block')
        except Exception:
            # Si no hay una sección creada para borrar, se ignora este paso
            pass

        # Crear nueva subsección
        await self.click_selector('a.btn-add')

        # Colocar orden 1 y guardar
        await self.llenar_campo('input[formcontrolname="order"]', str("1"))
        await self.page.evaluate('document.querySelector("#switch1").click()')
        await self.click_selector('button.btn.btn-outline-primary.btn-block')
        await self.page.wait_for_timeout(self.timeout*2)

        # Darle click a las subsecciones
        await self.click_selector('i.fa-list')
        

        ### Paso 2: Agregar el nuevo contenido
        # Eliminar el primer párrafo (el primer bloque de texto antes de un salto de línea)
        texto_sin_primer_parrafo = "\n".join(texto_con_hipervínculos.split("\n")[1:])
        
        # Darle click a "Agregar Bloque"
        await self.page.wait_for_selector('a.btn-add')
        await self.page.locator("a.btn-add").nth(0).click() 

        try:
            await self.llenar_campo('textarea[formcontrolname="textbox"]', texto_sin_primer_parrafo)
            await self.page.wait_for_timeout(self.timeout*3)

            # Esta parte me la dio Claude, he preferido dejarla así porque me tomó mucho encontrar un método
            dialog_appeared = False
            
            def handle_dialog(dialog):
                global dialog_appeared
                print(f"Mensaje del diálogo: {dialog.message}")
                dialog_appeared = True
                dialog.accept()
                
            # Registrar el event listener para diálogos
            try:
                await self.page.on("dialog", handle_dialog)
            except Exception as e:
                print("Verificar si se aceptó el diálogo")

            # Hacer clic en el botón
            await self.click_selector('button.btn.btn-outline-primary.btn-block')
                    
            # Esperar un poco para asegurar que el diálogo sea manejado
            await self.page.wait_for_timeout(self.timeout*3)
            print("Se actualizó el texto de la ficha")

        except Exception as e:
            print(f"Ocurrió un error actualizando el texto de la ficha: {str(e)}")
        
        
        # # Paso 3: Desactivar la primera fila
        #     self.page.wait_for_selector('tr.tbody-detail')
        #     rows = self.page.locator('tr.tbody-detail')
        #     edit_button = rows.nth(0).locator('i.fa-pencil')  # Asume que el lápiz está identificado por esta clase
        #     if edit_button.is_visible():
        #         edit_button.click()
        #         print("Lápiz de la primera fila presionado.")
        #     else:
        #         print("El lápiz de la primera fila no está visible.")
        #     # Cambiar el estado del switch usando JavaScript
        #     self.page.evaluate('document.querySelector("#switch1").click()')
        #     self.page.click('button.btn.btn-outline-primary.btn-block')
        #     self.page.reload()

        finally:
            # Mantener el navegador abierto si algo falla
            #input("Presiona Enter para cerrar el navegador...")
            await self.page.remove_listener("dialog", handle_dialog)



        ################## MANEJO DE GRÁFICOS ####################
    async def actualizar_gráficos(self, codigo_ficha, resultado, desactivar=True):
        """
        Desactiva los gráficos existentes, crea nuevas casillas con los datos proporcionados,
        y guarda los cambios.

        Args:
            codigo_ficha (str): Código de la ficha a procesar.
            resultado (list): Lista de listas con los detalles de cada gráfico. Contiene [orden, numeración, título, nota].
            desactivar (bool, optional): Si es True, desactiva los gráficos. Si es False, los sobreescribe (default: True).

        Raises:
            Exception: Si ocurre un error al procesar las filas o al guardar los cambios de los gráficos.
        """

        # Seleccionar el ícono de gráficos (orden 1)
        await self.seleccionar_icono(codigo_ficha, 1)

        # Obtener número de gráficos
        await self.page.wait_for_selector('tr.tbody-detail')
        rows = await self.page.locator('tr.tbody-detail')
        row_count = rows.count()
        
        # Paso 1: Usar la función desactivar_casillas 
        await self.desactivar_casillas_activadas(rows, desactivar)

        # Paso 2: Procesar cada entrada en resultado
        for item in resultado:
            # Crear nueva casilla
            await self.page.wait_for_selector('a.btn-add i.fa-plus', state='visible')
            await self.page.locator('a.btn-add').click()

            # Seleccionar Frame Datawrapper
            await self.page.wait_for_selector('select[formcontrolname="idgraphictype"]', state='visible')
            await self.page.select_option('select[formcontrolname="idgraphictype"]', value="12")

            # Desempaquetar los elementos de la lista
            orden, numeracion, titulo, nota = item

            # Llenar los campos
            await self.llenar_campo('input[formcontrolname="order"]', str(orden))
            await self.llenar_campo('input[formcontrolname="numeration"]', numeracion)
            await self.llenar_campo('input[formcontrolname="title"]', titulo)
            await self.llenar_campo('textarea[formcontrolname="note"]', nota)

            # Activar el switch usando JavaScript
            await self.page.evaluate('document.querySelector("#switch1").click()')

            # Guardar la casilla
            await self.click_selector('button.btn.btn-outline-primary.btn-block')

            # Esperar a que se recargue la tabla antes de procesar la siguiente entrada
            await self.page.wait_for_selector('tr.tbody-detail', state='visible')
        print("Se actualizaron los datos de los gráficos")



        ################## MANEJO DE REFERENCIAS ####################
    async def desactivar_referencias(self, codigo_ficha, desactivar=True, omitir_inicio=False):
        """
        Desactiva las referencias en las filas de la tabla de referencias según el estado marcado como "ACTIVO".

        Args:
            codigo_ficha (str): Código de la ficha a procesar.
            desactivar (bool, optional): Si es True, desactiva los switches. Si es False, los activa (default: True).
            omitir_inicio (bool, optional): Si es True, asume que ya se encuentra en la pestaña de referencias (default: False).

        Raises:
            Exception: Si ocurre un error al procesar los switches o interactuar con la página.
        """

        # Seleccionar el ícono de referencias (orden 2) para modificar switches
        if not omitir_inicio:
            await self.seleccionar_icono(codigo_ficha, 2)

        # Esperamos que las filas estén disponibles en la página
        await self.page.wait_for_selector('tr.tbody-detail')
        rows = await self.page.locator('tr.tbody-detail')

        # Llamamos a la función que recopila el estado y desactiva/activa según el parámetro
        self.desactivar_casillas_activadas(rows, desactivar)


    async def agregar_referencias(self, codigo_ficha, referencias_limpias, omitir_inicio=False):
        """
        Agrega referencias y las procesa para hipervincularlas utilizando "Agregar Nuevo".

        Args:
            codigo_ficha (str): Código de la ficha a procesar.
            referencias_limpias (str): Texto de las referencias procesadas a agregar.
            omitir_inicio (bool, optional): Si es True, asume que ya se encuentra en la pestaña de referencias (default: False).

        Raises:
            Exception: Si ocurre un error al procesar las referencias o interactuar con la página.
        """
        if not omitir_inicio:
            await self.seleccionar_icono(codigo_ficha, 2)  # Seleccionar el ícono de referencias (orden 2)

        referencias = re.split(r'\n(?=\[\d+\])', referencias_limpias.strip())  # Dividir las referencias por líneas
        pattern = r'https?://[^\s]+(?:\s|$|\.)'  # Captura enlaces desde "http" hasta espacio, fin de línea o punto

        for referencia in referencias:
            try:
                # Hacer clic en "Agregar Nuevo"
                await self.page.wait_for_selector('a.btn-add')
                await self.page.locator("a.btn-add").nth(1).click()

                # Llenar el campo de contenido con la referencia
                await self.llenar_campo('textarea[formcontrolname="content"]', referencia.strip())

                # Obtener URL de la referencia
                match = re.search(pattern, referencia)
                url_value = match.group(0).rstrip('.') if match else ""  # Capturar URL limpia

                # Insertar URL en el campo correspondiente
                await self.llenar_campo('input[formcontrolname="urlsource"]', url_value)

                # Guardar cambios
                await self.click_selector('button.btn.btn-outline-primary.btn-block')
                await self.page.wait_for_selector('tr.tbody-detail', state='visible')  # Esperar recarga

            except Exception as e:
                print(f"Error al agregar referencia: {referencia[:30]}... -> {str(e)}")

        print("Se agregaron todas las referencias")

       

    async def agregar_enlace_a_casillas(self, codigo_ficha, omitir_inicio=False):
        """
        NO UTILZAR, OUTDATED
        Extrae el contenido de un campo de texto (textarea) de una referencia, procesa el enlace HTML y lo inserta en una casilla de URL.

        Args:
            codigo_ficha (str): Código de la ficha que se desea procesar.
            omitir_inicio (bool, optional): Si es True, asume que ya se encuentra en la pestaña de referencias (default: False).

        Raises:
            Exception: Si ocurre un error al extraer el enlace o interactuar con la página.
        """

        # Si 'inicio' es False, seleccionar el ícono del libro (orden 2) para modificar referencias
        if not omitir_inicio:
            await self.seleccionar_icono(self.page, codigo_ficha, 2)

        # Esperar a que la tabla se cargue
        await self.page.wait_for_selector('tr.tbody-detail', state='visible')
        rows = self.page.locator('tr.tbody-detail')
        row_count = await rows.count()

        # Iterar sobre cada fila para extraer y actualizar HTML
        for index in range(row_count):
            # Seleccionar la subfila y abrir el modal de edición
            subrow = rows.nth(index)
            pencil_icon = subrow.locator('a.a-icon i.fa-pencil')
            pencil_icon.scroll_into_view_if_needed()
                
            if await pencil_icon.is_visible():
                try:
                    await pencil_icon.click()
                    # Extraer contenido del textarea
                    
                except Exception as e:
                    print(f"Lápiz de la fila {index + 1} no es visible, intentando alternativa")
                    try:
                        # Hacer click en el lápiz con js
                        await self.page.evaluate('''
                            var pencil = document.querySelector('a.a-icon i.fa-pencil');
                            if (pencil) {
                                pencil.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                pencil.click();
                            }
                        ''')
                        print(f"Se logró seleccionar el lápiz de la fila {index + 1} mediante método alternativo.")
                    except Exception as e:
                        print(f"Error al procesar la fila, pero el lápiz sí era visible {index + 1}: {e}")

                    # Extraer contenido del text area
                    await self.page.wait_for_selector('textarea[formcontrolname="content"]', state='visible')
                    textarea_value = await self.page.locator('textarea[formcontrolname="content"]').input_value()
                    pattern = r'http[^\s]+(?:\s|$|\.)'  # Captura desde http hasta un espacio, fin de línea o punto
                    match = re.search(pattern, textarea_value)

                    if match:
                        url_value = match.group(0)  # Captura el enlace completo
                        # Si termina en punto y no hay más texto después de la URL, elimina el punto
                        if url_value.endswith('.') and (match.end() == len(textarea_value) or textarea_value[match.end()] == ' '):
                            url_value = url_value.rstrip('.')  # Eliminar el punto al final si es el caso
                    else:
                        url_value = ""  # Si no se encuentra ninguna URL

                    #print(f"URL extraída (fila {index + 1}): {url_value}")

                    # Insertar el contenido extraído en el campo de URL
                    await self.llenar_campo('input[formcontrolname="urlsource"]', url_value)

                    # Hacer hover sobre el botón y luego clic
                    save_button = self.page.locator('button.btn.btn-outline-primary.btn-block')
                    await save_button.hover()  # Hover sobre el botón
                    await self.page.click('button.btn.btn-outline-primary.btn-block')

                    # Esperar a que la tabla se recargue antes de continuar
                    await self.page.wait_for_selector('tr.tbody-detail', state='visible')
                except Exception as e:
                    print(f"Error al procesar la fila, pero el lápiz sí era visible {index + 1}: {e}")
        print("Se hipervincularon todas las referencias")


class ReaderObs(NavegadorObs):
    def __init__(self, timeout):
        super().__init__(timeout)
        self.info_fichas = {}  # Diccionario para almacenar la información de las fichas
        self.fichas_con_problemas = []  # Lista para almacenar fichas con problemas

    async def seleccionar_rubro_y_subrubro(self, rubro, subrubro):
        """
        Selecciona el rubro y subrubro en la interfaz.
        """
        await self.page.wait_for_selector('li.btn-org[routerlinkactive="active"]')
        await self.page.click(f'li.btn-org:has-text("{rubro}")')
        await self.page.wait_for_selector('a.col-sm-3.btn-org')
        await self.page.click(f'a.col-sm-3.btn-org:has-text("{subrubro}")')

    # FUNCIONES PRINCIPALES
    async def obtener_informacion_ficha(self, codigo, territorial=False):
        """
        Extrae información de una ficha abierta.

        Args:
            codigo (str): Código de la ficha.
            territorial (bool): Indica si se debe extraer información territorial.

        Returns:
            dict: Información de la ficha.
        """
        campos = {
            "codigo": 'input[placeholder="Código"]',
            "titulo_corto": 'input[placeholder="Título corto"]',
            "titulo_largo": 'input[placeholder="Título largo"]',
            "sumilla": 'textarea[formcontrolname="summary"]',
            "fecha_publicacion": 'input[formcontrolname="publication"]',
            "ultima_actualizacion": 'input[formcontrolname="lastUpdated"]',
            "tags": 'input[formcontrolname="tags"]'
        }

        self.info_fichas[codigo] = {}
        for campo, selector in campos.items():
            try:
                await self.page.wait_for_selector(selector)
                await self.page.locator(selector).scroll_into_view_if_needed()
                self.info_fichas[codigo][campo] = await self.page.locator(selector).input_value()
            except Exception as e:
                print(f"Error al extraer '{campo}' de la ficha {codigo}: {e}")
                self.info_fichas[codigo][campo] = "No disponible"

        # Extraer "Estado"
        try:
            estado_selector = 'input[formcontrolname="status"]'
            await self.page.wait_for_selector(estado_selector)
            estado = await self.page.locator(estado_selector).is_checked()
            self.info_fichas[codigo]["estado"] = "Activo" if estado else "Inactivo"
        except Exception as e:
            print(f"Error al extraer 'Estado': {e}")
            self.info_fichas[codigo]["estado"] = "No disponible"

        # Extraer "Temática"
        try:
            tematica_selector = 'select[formcontrolname="idtematic"]'
            await self.page.wait_for_selector(tematica_selector)
            numero = await self.page.locator(tematica_selector).input_value()
            tematica = mapeo_tematica.get(numero, "Desconocido")
            self.info_fichas[codigo]["tematica"] = tematica
        except Exception as e:
            print(f"No se pudo extraer la temática: {e}")
            self.info_fichas[codigo]["tematica"] = "No disponible"

        # Extraer "Departamentos" si es territorial
        if territorial:
            try:
                departamento_value = await self.page.evaluate(
                    '''() => {
                        const selected = document.querySelector('select[formcontrolname="iddpto"] option:checked');
                        return selected ? selected.textContent.trim() : "No disponible";
                    }'''
                )
                self.info_fichas[codigo]["departamento"] = departamento_value
            except Exception as e:
                print(f"Error al extraer 'Departamento': {e}")
                self.info_fichas[codigo]["departamento"] = "No disponible"


    async def procesar_ficha(self, codigo_ficha, territorial=False):
        """
        Procesa una ficha individualmente.
        """
        # Por lo general omitir_inicio = True, ya que se busca obtener de todas las fichas
        try:
            # if not omitir_inicio:
            #     rubro, subrubro = self.identificar_rubro_y_subrubro(codigo_ficha)
            #     if not rubro or not subrubro:
            #         raise ValueError(f"No se encontró rubro/subrubro para {codigo_ficha}")
            #     await self.seleccionar_rubro_y_subrubro(self, rubro, subrubro)

            # Hacer clic en el lápiz para ver la metadata de la ficha (orden 4)
            await self.seleccionar_icono(codigo_ficha, 4) 

            # Obtenemos y guardamos la info de una ficha
            await self.obtener_informacion_ficha(codigo_ficha, territorial=territorial)
            print(f"Ficha {codigo_ficha} procesada exitosamente.")
        except Exception as e:
            # Detección de errores
            self.fichas_con_problemas.append(codigo_ficha)
            print(f"Error procesando la ficha {codigo_ficha}: {e}")
        finally:
            await self.volver_a_inicio()


    async def procesar_fichas(self, rubro, subrubro, territorial=False):
        """
        Procesa todas las fichas dentro de un rubro
        """
        try:
            await self.seleccionar_rubro_y_subrubro(rubro, subrubro)
            await self.page.wait_for_selector('tr.tbody-detail')
            filas = self.page.locator('tr.tbody-detail')
            total_filas = await filas.count()
            print(f"Se extraerá información de {total_filas} fichas de {subrubro}")

            for i in range(total_filas):
                try:
                    # Navegar a la página del subrubro
                    if subrubro != "Tendencia nacional":
                        await self.seleccionar_rubro_y_subrubro(rubro, subrubro)
                    await self.page.wait_for_selector('tr.tbody-detail')

                    # Obtener el código de la ficha
                    fila = filas.nth(i)
                    codigo_ficha = (await fila.locator('td').nth(1).inner_text()).strip()
                    #print(f"Este es el código_ficha obtenido: {codigo_ficha}")

                    # Procesar la ficha
                    await self.procesar_ficha(codigo_ficha, territorial=territorial)
                except Exception as e:
                    print(f"Error procesando fila {i}: {e}")
        except Exception as e:
            print(f"Error procesando todas las fichas del subrubro: {e}")


    async def guardar_resultados(self, rubro, subrubro):
        """
        Guarda los resultados en archivos JSON y TXT.
        """
        # Calcula el path absoluto al directorio 'dicts'
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Directorio del script
        directorio_salida = os.path.join(script_dir, "dicts")  # Subcarpeta 'dicts'

        # Construye las rutas completas para los archivos
        #archivo_info = os.path.join(directorio_salida, f'info_{rubro}_{subrubro}.json')
        #archivo_problemas = os.path.join(directorio_salida, f'problemas_{rubro}_{subrubro}.txt')

        archivo_info = os.path.join(directorio_salida, 'info_obs_prueba.json')
        archivo_problemas = os.path.join(directorio_salida, 'problemas_obs_prueba.txt')


        # Guarda el JSON con la información de las fichas
        with open(archivo_info, 'w', encoding='utf-8') as json_file:
            json.dump(self.info_fichas, json_file, indent=4, ensure_ascii=False)
        print(f"Información guardada como {archivo_info}")

        # Guarda la lista de problemas en un archivo de texto
        with open(archivo_problemas, 'w', encoding='utf-8') as txt_file:
            for problema in self.fichas_con_problemas:
                txt_file.write(f"{problema}\n")
        print(f"Problemas guardados como {archivo_problemas}")

        #self.info_fichas = {}
        #self.fichas_con_problemas = []




