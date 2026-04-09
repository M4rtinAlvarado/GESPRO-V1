# Importamos la clase especial de Django para pruebas con navegador real
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
# Importamos 'reverse' para buscar nuestras URLs por su nombre
from django.urls import reverse

# Importaciones necesarias de Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

import time
from .models import Proyecto
import os
from django.conf import settings



# Ruta al archivo plantilla que usaremos para crear el proyecto
PLANTILLA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
    "static",
    "plantilla.xlsx",
)

class ProyectosSeleniumTests(StaticLiveServerTestCase):
    """
    Suite de pruebas E2E (End-to-End) para la aplicación de Proyectos usando Selenium.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Paso de preparación: Se ejecuta una sola vez antes de comenzar las pruebas.
        Aquí inicializamos nuestro navegador virtual.
        """
        super().setUpClass()
        
        # Configuramos opciones para el navegador Chrome
        options = webdriver.ChromeOptions()
        # Si quisieras que la prueba corra sin abrir la ventana (modo fantasma),
        # descomentarías la siguiente línea:
        # options.add_argument('--headless') 
        
        # Instalamos y abrimos Chrome automáticamente
        cls.selenium = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), 
            options=options
        )
        
        # Le damos a Selenium hasta 10 segundos de tolerancia para encontrar elementos
        # en caso de que la página tarde un poco en cargar
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        """
        Paso de limpieza: Se ejecuta al finalizar todas las pruebas en esta clase.
        """
        # Cerramos el navegador para no dejar ventanas "huérfanas" en tu computadora
        cls.selenium.quit()
        super().tearDownClass()



    def test_crear_proyecto_test01_con_plantilla(self):
            # 1. Navegar al formulario de creación
            # El nombre es 'verificar_proyecto' según tu excel/urls.py
            url_crear = self.live_server_url + reverse('verificar_proyecto') 
            self.selenium.get(url_crear)
            
            # 2. Escribir el nombre del proyecto
            # Asegúrate de que en tu HTML el <input> tenga name="nombre"
            input_nombre = self.selenium.find_element(By.NAME, "nombre_proyecto")
            
            time.sleep(2) # Pausa para que alcances a ver la ventana de Chrome
            input_nombre.send_keys("test01")
            
            # 3. Pausa final para verificar visualmente antes de que se cierre
            time.sleep(1)
            
             # 4. CARGAMOS EL ARCHIVO EXCEL
            # Buscamos el input de tipo archivo (revisando tu HTML, tiene el id="id_archivo")
            campo_archivo = self.selenium.find_element(By.ID, "id_archivo")
            
            # Construimos la ruta exacta de tu archivo usando BASE_DIR de Django
            ruta_archivo = os.path.join(settings.BASE_DIR, 'frontend', 'static', 'plantilla.xlsx')
            
            # Enviamos la ruta del archivo al input
            campo_archivo.send_keys(ruta_archivo)
            time.sleep(1) # Pausa para que veas que el archivo se cargó (el nombre debería aparecer en tu interfaz)
            
            # 5. ENVIAMOS EL FORMULARIO
            # Buscamos el botón de tipo "submit" para guardar el formulario
            boton_guardar = self.selenium.find_element(By.CSS_SELECTOR, "button[type='submit']")
            boton_guardar.click()

            time.sleep(1) # Pausa para que veas el resultado después de enviar el formulario

            confirmar_btn = self.selenium.find_element(By.ID, "btn-confirmar")
            confirmar_btn.click()

            time.sleep(2) # Pausa para que veas el resultado después de confirmar






