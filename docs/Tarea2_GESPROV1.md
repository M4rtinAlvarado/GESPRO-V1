# Guía de Ejecución de Pruebas (Testing)


## 1. Requisitos para la Ejecución

Para asegurar que los tests de integración y de interfaz (E2E) se ejecuten correctamente, el entorno debe cumplir con lo siguiente:

### 1.1 Entorno de Desarrollo
* **Python 3.x**: Instalado y configurado en el PATH.
* **Django**: El framework principal del proyecto.
* **Selenium**: Biblioteca para la automatización del navegador (`pip install selenium`).
* ** required packages**: Asegúrese de tener instalados todos los paquetes necesarios listados en `requirements.txt` del proyecto.

### 1.2 Web Drivers
Selenium requiere un controlador para interactuar con el navegador. Asegúrese de tener uno de los siguientes según su preferencia:
* **ChromeDriver**: Para Google Chrome.
* **GeckoDriver**: Para Mozilla Firefox.
> **Nota:** El driver debe ser de la misma versión que el navegador instalado y debe estar disponible en el PATH del sistema o en la raíz del proyecto.

### 1.3 Base de Datos de Pruebas
* No es necesario configurar una base de datos manual. Django creará automáticamente una base de datos temporal en memoria o en un archivo local para garantizar que los datos de desarrollo no se vean afectados.

---

## 2. Ejecución de los Tests
Para ejecutar las pruebas unitarias de la interfaz de proyectos mencionada en la documentación:

### Ejecutar Test Específico (Test 01)

```bash
cd backend 
python manage.py test proyectos.tests.ProyectosSeleniumTests.test01
```
video de ejecución del test:
https://youtu.be/eD7SDIQjEvg?si=udF3nPWi6ubV449Q

### Para ejecutar el Test Específico (Test 02)
```bash
cd backend 
python manage.py test proyectos.tests.ProyectosSeleniumTests.test02
```
video de ejecución del test:
https://youtu.be/HXipB6VgcHo?si=KaXmxr08sO8Slq8B
