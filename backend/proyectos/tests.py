import time
import os
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from .models import Proyecto
from excel.import_gantt import importar_gantt

PLANTILLA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
    "static",
    "plantilla.xlsx",
)

class ProyectosSeleniumTests(StaticLiveServerTestCase):
    """
    Suite de pruebas End-to-End (E2E) para la gestión de proyectos y actividades.
    Utiliza Selenium WebDriver para simular la interacción real de un usuario.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Inicializa el servidor de pruebas en vivo y configura el controlador de Google Chrome.
        Se ejecuta una única vez al comenzar la suite de pruebas.
        """
        super().setUpClass()
        options = webdriver.ChromeOptions()
        
        cls.selenium = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), 
            options=options
        )
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        """
        Cierra la instancia del navegador web y limpia el entorno al finalizar todas las pruebas.
        """
        cls.selenium.quit()
        super().tearDownClass()

    def test01(self, tiempo=2):
        """
        Verifica el flujo completo de creación de un proyecto simulando la interacción del usuario.
        Abarca la navegación, llenado del formulario, carga del archivo Excel y confirmación.
        """
        url_crear = self.live_server_url + reverse('verificar_proyecto') 
        self.selenium.get(url_crear)
        
        input_nombre = self.selenium.find_element(By.NAME, "nombre_proyecto")
        time.sleep(tiempo) 
        input_nombre.send_keys("test01")
        time.sleep(tiempo)
        
        campo_archivo = self.selenium.find_element(By.ID, "id_archivo")
        ruta_archivo = os.path.join(settings.BASE_DIR, 'frontend', 'static', 'plantilla.xlsx')
        campo_archivo.send_keys(ruta_archivo)
        time.sleep(tiempo) 
        
        boton_guardar = self.selenium.find_element(By.CSS_SELECTOR, "button[type='submit']")
        boton_guardar.click()
        time.sleep(tiempo) 

        confirmar_btn = self.selenium.find_element(By.ID, "btn-confirmar")
        confirmar_btn.click()
        time.sleep(tiempo) 

    def test02(self):
        """
        Verifica la funcionalidad de modificación de una actividad existente en un proyecto.
        
        Flujo de la prueba:
        1. Prepara el entorno inyectando el proyecto base en la BD (Data Seeding).
        2. Navega al proyecto y accede a la vista de "Lista".
        3. Abre el modal de edición de la primera actividad.
        4. Modifica el nombre de la actividad y añade un nuevo encargado.
        5. Guarda los cambios y aserta que las modificaciones se reflejen en el DOM.
        """
        ruta_archivo = os.path.join(settings.BASE_DIR, 'frontend', 'static', 'plantilla.xlsx')
        with open(ruta_archivo, 'rb') as archivo_excel:
            importar_gantt("test01", archivo_excel)

        url_proyectos = self.live_server_url + reverse('proyectos')
        self.selenium.get(url_proyectos)
        time.sleep(2) 

        proyecto_link = self.selenium.find_element(
            By.XPATH, f"//h2[contains(text(), 'test01')]/ancestor::a"
        )
        proyecto_link.click()
        time.sleep(2)
        
        self.assertIn('gantt', self.selenium.current_url.lower())
        time.sleep(1)

        boton_lista = self.selenium.find_element(By.LINK_TEXT, "Lista")
        boton_lista.click()
        time.sleep(2) 
        
        self.assertIn('lista_actividades', self.selenium.current_url)
        
        boton_lista_nuevo = self.selenium.find_element(By.LINK_TEXT, "Lista")
        clases_boton = boton_lista_nuevo.get_attribute("class")
        self.assertIn("bg-white", clases_boton)

        boton_editar = self.selenium.find_element(By.CLASS_NAME, "btn-editar")
        self.selenium.execute_script("arguments[0].scrollIntoView();", boton_editar)
        self.selenium.execute_script("arguments[0].click();", boton_editar)
        time.sleep(1) 
        
        modal_edicion = self.selenium.find_element(By.ID, "editModal")
        self.assertNotIn("hidden", modal_edicion.get_attribute("class"))
        
        nombre_actividad = boton_editar.get_attribute("data-nombre")
        input_nombre = self.selenium.find_element(By.ID, "editNombreInput")
        self.assertEqual(input_nombre.get_attribute("value"), nombre_actividad)
        time.sleep(2) 

        input_nombre = self.selenium.find_element(By.ID, "editNombreInput")
        input_nombre.clear()
        nuevo_nombre = "test_2"
        input_nombre.send_keys(nuevo_nombre)

        btn_abrir_add_encargado = self.selenium.find_element(By.CSS_SELECTOR, "#editModal .btnOpenAddEncargado")
        self.selenium.execute_script("arguments[0].click();", btn_abrir_add_encargado)
        time.sleep(1) 

        self.selenium.find_element(By.ID, "addEncargadoNombre").send_keys("ivan duran")
        self.selenium.find_element(By.ID, "addEncargadoCorreo").send_keys("ivan.duran@gmail.com")
        time.sleep(2) 

        btn_guardar_encargado = self.selenium.find_element(By.ID, "saveAddEncargado")
        btn_guardar_encargado.click()
        time.sleep(1) 

        lista_encargados_modal = self.selenium.find_element(By.CLASS_NAME, "js-encargados-list")
        self.assertIn("ivan duran", lista_encargados_modal.text)

        btn_guardar = self.selenium.find_element(By.ID, "saveChanges")
        btn_guardar.click()
        time.sleep(1.5) 
        
        try:
            alerta = self.selenium.switch_to.alert
            alerta.accept()
        except:
            pass

        time.sleep(4)
        modal_edicion = self.selenium.find_element(By.ID, "editModal")
        self.assertIn("hidden", modal_edicion.get_attribute("class"))

        primer_nombre_lista = self.selenium.find_element(By.CLASS_NAME, "activity-name").text
        self.assertEqual(primer_nombre_lista, "test_2")
