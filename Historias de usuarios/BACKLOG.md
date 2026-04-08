## **H1: Descargar plantilla limpia de carta Gantt**

**Prioridad: 2**

**Como** coordinadora regional,
**Quiero** poder descargar una plantilla vacía de carta Gantt en formato Excel,
**Para** tener un modelo estandarizado que pueda completar y luego cargar en el sistema.

### **Criterios de aceptación:**

- Dado que estoy en el menú principal, cuando seleccione "Descargar plantilla", entonces el sistema debe generar un archivo Excel con la estructura requerida (columnas de tarea, fechas, encargado, etc.).
- Dado que descargue el archivo, cuando lo abra en Excel, entonces debe estar vacío de datos pero con el formato correcto para ser usado.
- Dado que posteriormente importe un proyecto desde la plantilla, cuando lo valide, entonces el sistema debe aceptarlo como un archivo válido.

### Tareas asignadas

- programar logica en backend
- hacer manual de usuario
- Diseñar plantilla de excel

### Diagrama de Secuencia:

![imagen_2025-09-28_214047294.png](attachment:a4046169-6bbd-4f7a-9d47-f7277d1ea3df:imagen_2025-09-28_214047294.png)

---

## **H2: Crear un proyecto desde un archivo Excel (carta Gantt)**

**Prioridad: 1**

**Como** coordinadora regional,
**Quiero** poder crear un proyecto a partir de un archivo Excel con una carta Gantt,
**Para** cargar rápidamente la información y empezar a gestionarla dentro del software.

### **Criterios de aceptación:**

- Dado que estoy en el menú principal, cuando haga clic en el botón "Crear proyecto", entonces el sistema debe mostrarme la opción de importar un archivo Excel y un campo de texto para ingresar el nombre del proyecto.
- Dado que selecciono un archivo Excel válido y escribo un nombre para el proyecto, cuando confirme la creación, entonces el sistema debe generar un nuevo proyecto en la lista a partir de la información de la carta Gantt.
- Dado que intento importar un archivo Excel con formato incorrecto o inválido, cuando confirme la creación, entonces el sistema debe mostrar un mensaje de error indicando el problema.
- Dado que creo un proyecto exitosamente, cuando vuelva al menú principal, entonces el nuevo proyecto debe aparecer en la lista junto con los demás.

### Tareas asignadas

- Programar el front end
- programar logica en backend
- Agregar boton de crear plantilla
- hacer manual de usuario

### Diagrama de Secuencia:

![imagen_2025-09-28_214142245.png](attachment:c9afc5ec-ecb1-427c-bb29-c501e7780ac8:imagen_2025-09-28_214142245.png)

---

## **H3: Navegar y acceder a proyectos desde el menú principal**

**Prioridad: 2**

**Como** coordinadora regional,
**Quiero** acceder a un menú principal que me muestre todos mis proyectos y me permita seleccionar uno,
**Para** poder entrar a gestionarlo fácilmente.

### **Criterios de aceptación:**

- Dado que estoy en el menú principal, cuando se cargue la pantalla, entonces debo ver una lista con todos mis proyectos registrados.
- Dado que estoy viendo la lista de proyectos, cuando seleccione un proyecto y haga clic, entonces el sistema debe abrir ese proyecto y mostrar su información detallada.

### Tareas de asignacion

- Programar el front end con la lista de proyectos
- Agregar boton de crear proyectos que lleve hacia otra pagina
- programar logica en backend
- cuando se aprete a un proyecto se redirige a la pagina del proyecto
- Hacer manual de usuario

### Diagrama de Secuencia

![imagen_2025-09-28_214226248.png](attachment:ba9699ea-1ee2-4d3c-b206-b71457b5634f:imagen_2025-09-28_214226248.png)

---

## **H4: Visualizar simple de la carta Gantt**

**Prioridad: 2**

**Como** coordinadora regional,
**Quiero** ver una versión simple y clara de la carta Gantt dentro del sistema,
**Para** entender rápidamente las fechas  sin necesidad de abrir Excel.

### **Criterios de aceptación:**

- Dado que accedo al detalle de un proyecto, cuando seleccione la opción, entonces el sistema debe mostrar una vista gráfica de barras con las tareas en el tiempo.
- Dado que el proyecto tenga muchas tareas, cuando navegue en la vista, entonces el sistema debe permitir desplazamiento horizontal y vertical.
- Dado que actualice una tarea (fechas, estado), cuando refresque la vista, entonces la carta Gantt debe reflejar los cambios automáticamente.

### Tareas asignadas

- Programar vistas (Frontend)
- hacer manual de usuario
- Programar Backend

### Diagrama de Secuencia

![imagen_2025-09-28_214310344.png](attachment:a5129889-56a9-47ea-8cad-0399eaaad87f:imagen_2025-09-28_214310344.png)

---

## **H5: Crear una nueva tarea en un proyecto existente**

**Prioridad: 3**

**Como** coordinadora regional,
**Quiero** poder añadir una nueva tarea directamente en un proyecto ya existente,
**Para** actualizar la planificación con nuevas actividades sin necesidad de reimportar todo el archivo Excel.

### **Criterios de aceptación:**

- Dado que estoy gestionando un proyecto, cuando seleccione la opción "Añadir Tarea", entonces el sistema debe mostrar un formulario con los campos necesarios para definirla (ej: nombre, fechas, encargado, descripción).
- Dado que completo los campos requeridos del formulario (como mínimo el nombre y las fechas), cuando guarde la nueva tarea, entonces esta debe aparecer en la lista de tareas y reflejarse en la carta Gantt del proyecto.
- Dado que la tarea fue creada exitosamente, cuando la acción finalice, entonces el sistema debe mostrar un mensaje de confirmación.
- Dado que intento guardar una tarea con información inválida o incompleta (ej: sin nombre), cuando confirme la creación, entonces el sistema debe mostrar un mensaje de error indicando qué campos se deben corregir.

---

## **H6: Modificar tareas del proyecto**

**Prioridad:2**

**Como** coordinadora regional,
**Quiero** poder modificar la información de cada tarea (nombre, fechas, encargado, descripción, etc.),
**Para** mantener actualizado el proyecto cuando ocurren cambios en la planificación.

### **Criterios de aceptación:**

- Dado que estoy visualizando el detalle de un proyecto, cuando seleccione una tarea y elija la opción "Editar", entonces el sistema debe mostrar un formulario con los campos de la tarea.
- Dado que modifico un campo de la tarea (ejemplo: nombre, fecha de inicio o encargado), cuando guarde los cambios, entonces el sistema debe actualizar la información y mostrar un mensaje de confirmación.

### Tareas asignadas:

- Programar la modificación en la BD(Backend)
- Hacer manual de usuario
- Programar boton y Modal de la modificación (Frontend)
- Hacer diagrama de secuencia

### Diagrama de Secuencia

![image.png](attachment:fb06ca65-80b4-41f3-b6a7-95c7d7335313:image.png)

![image.png](attachment:f8386a4c-e360-43d3-b13f-bc3e2276d904:image.png)

![image.png](attachment:5566d10d-6ad5-4d91-8360-2d60bfa188ae:image.png)

---

## **H7: Cambiar estado de una tarea**

**Prioridad: 1**

**Como** coordinadora regional,
**Quiero** poder cambiar el estado de la tarea,
**Para** reflejar el avance dentro del proyecto.

### **Criterios de aceptación:**

- Dado que estoy visualizando una lista de tareas, cuando marque una tarea como completada, entonces debe mostrarse como terminada (ejemplo: con un check y cambio de estado).
- Dado que una tarea está completada, cuando vuelva a revisar el proyecto, entonces la tarea debe seguir registrada como finalizada.
- Dado que por error marco una tarea como terminada, cuando quite el check, entonces la tarea debe volver al estado “En revisión”.
- Dado que estoy visualizando el Backlog, cuando identifique una tarea que deba cambiar de estado, entonces puedo arrastrar la tarea de un estado a otro.

### Tareas asignadas

- hacer manual de usuario
- Implementar botón para acceder a lista en la navbar
- Mostrar la lista de actividades
- Implementar botón para acceder a el tablero en la navbar*
- Mostrar tablero*
- Implementar dropdown para cambiar el estado de una actividad
- Hacer diagrama de secuencia
- Programar el backend para cambiar el estado en la vista de lista
- Programar el backend para cambiar el estado en la vista de tabla*

### Diagrama de Secuencia

![Screenshot_2025-09-29_212402.png](attachment:cf40805c-9c50-4049-a229-64a87706ca11:Screenshot_2025-09-29_212402.png)

---

## **H8: Agregar notas dentro del detalle de una tarea**

**Prioridad: 4**

**Como** coordinadora regional,

**Quiero** que cada tarea tenga una sección de comentarios donde pueda registrar apuntes, retrasos u observaciones,

**Para** llevar un historial claro de información relevante sobre la ejecución de la tarea.

### **Criterios de aceptación:**

- **Dado** que estoy visualizando una tarea, **cuando** acceda a su detalle, **entonces** debo ver una sección destinada a los comentarios.
- **Dado** que quiero dejar un apunte sobre la tarea, **cuando** escriba un comentario y lo guarde, **entonces** este debe quedar asociado a la tarea.

---

## **H9: Filtrar y ordenar la lista de tareas del proyecto**

**Prioridad:  3**

**Como** coordinadora regional,
**Quiero** poder filtrar y ordenar la lista de tareas de un proyecto,
**Para** localizar y organizar fácilmente la información según mis necesidades de gestión.

### **Criterios de aceptación:**

- Dado que estoy en la vista de tareas de un proyecto, cuando seleccione la opción "Filtrar", entonces el sistema debe mostrar criterios como: encargado, estado (pendiente, en progreso, completada), rango de fechas o palabra clave.
- Dado que aplique un filtro, cuando confirme, entonces la lista debe mostrar solo las tareas que cumplen con esos criterios.
- Dado que existan filtros activos, cuando los desactive, entonces la lista debe volver a mostrar todas las tareas del proyecto.
- Dado que quiera ordenar la lista, cuando seleccione un criterio (ejemplo: fecha de inicio, fecha de término, encargado, estado), entonces el sistema debe reorganizar las tareas en base a esa selección.
- Dado que aplique filtros y ordenamientos combinados, cuando los ejecute, entonces la lista debe mostrar únicamente las tareas que cumplan con el filtro y en el orden elegido.

---

## **H10:  Alertar proximidad de fechas de entrega de tarea**

**Prioridad: 1**

**Como** coordinadora regional,
**Quiero** que el software envíe alertas a los encargados de cada tarea (según la información en la carta Gantt),
**Para** mantenerlos informados de sus responsabilidades y plazos.

### **Criterios de aceptación:**

- Dado que una tarea tiene un encargado con nombre y correo asociado, cuando se aproxime la fecha límite, entonces el sistema debe enviar una alerta por correo electrónico de manera automática.
- Dado que el sistema tiene una configuración de alerta fija por defecto, cuando se cree un proyecto, entonces esa configuración se aplicará automáticamente a todas las tareas.
- Dado que el sistema envía una alerta, cuando el encargado la reciba, entonces esta debe contener al menos: nombre del proyecto, tarea asignada, fecha límite y estado actual.
- Dado que modifique el estado de una tarea a “En progreso”, entonces se le enviará una notificación al encargado de dicha tarea.

### Tareas Asignadas

- programar creación de las alertas por defecto(Backend)
- hacer manual de usuario
- Programar vista de alertas(Frontend)
- Programar script de automatización de alertas(Backend)

### Diagrama de Secuencia

![imagen_2025-09-28_215049019.png](attachment:48d2807f-0705-400d-bc1c-e503c5c5ee18:imagen_2025-09-28_215049019.png)

---

## **H11: Configurar las alertas individuales por tarea**

**Prioridad: 2**

**Como** coordinadora regional,
**Quiero** poder modificar las alertas de cada tarea de manera individual,
**Para** adaptar los recordatorios según la importancia o urgencia de cada tarea.

### **Criterios de aceptación:**

- Dado que estoy gestionando un proyecto, cuando observe las actividades, entonces puedo configurar las alertas asociadas a las actividades una por una.
- Dado que quiero personalizar una tarea, cuando modifique sus parámetros de alerta (ejemplo: días de anticipación, canal de notificación), entonces el sistema debe aplicar esos cambios solo a esa tarea.
- Dado que modifico la configuración de una tarea, cuando guarde los cambios, entonces el sistema debe mostrar un mensaje de confirmación indicando que la alerta individual fue actualizada.
- Dado la visualización de una tarea, puedo agregar mas de una alerta para una tarea especifica.

### Tareas asignadas

- Programar configuración de las alertas(Backend)
- Hacer manual de usuario
- Programar modal de alerta(Frontend)
- Hacer diagrama de secuencia

### Diagrama de Secuencia

![image.png](attachment:3178ba27-62fa-475b-b428-b8dc81a3a0af:image.png)

![image.png](attachment:6a803e51-0217-48b9-804e-12b36fdc26db:image.png)

---

## **H12: Asignar de manera masiva alertas**

**Prioridad: 3**

**Como** coordinadora regional,
**Quiero** poder aplicar configuraciones de alertas a varias tareas al mismo tiempo,
**Para** ahorrar tiempo y mantener la coherencia en la gestión de recordatorios.

### **Criterios de aceptación:**

- Dado que estoy en la lista de tareas, cuando seleccione varias tareas, entonces el sistema debe mostrar la opción "Configurar alertas en lote".
- Dado que configure parámetros de alerta (ejemplo: días de anticipación, canal de notificación), cuando guarde la configuración, entonces debe aplicarse a todas las tareas seleccionadas.
- Dado que una tarea ya tenga una configuración individual distinta, cuando aplique la configuración masiva, entonces el sistema debe preguntar si quiero reemplazar o mantener la configuración previa.
- Dado que consulte el detalle de una tarea, cuando revise su configuración, entonces debo ver reflejada la configuración masiva aplicada (si corresponde).

### Tareas asignadas

- Programar configuración de las alertas(Backend)
- Hacer manual de usuario
- Programar modal de alerta(Frontend)
- Hacer diagrama de secuencia

### Diagrama de Secuencia

![image.png](attachment:3c4d6131-52e2-4557-8c44-499084fa6233:image.png)

![image.png](attachment:c110810a-6b1b-4ae5-9885-1f17b112986d:image.png)

---

## **H13: Notificar automáticamente cambios importantes a encargados**

**Prioridad: 4**

**Como** coordinadora regional,
**Quiero** que el sistema notifique automáticamente a los encargados cuando una tarea sea modificada en aspectos críticos,
**Para** asegurar que estén siempre informados de cambios que afectan su trabajo.

### **Criterios de aceptación:**

- Dado que una tarea cambie de encargado, cuando guarde la modificación, entonces el nuevo responsable debe recibir una notificación con los detalles de la asignación.
- Dado que una tarea cambie sus fechas de inicio o término, cuando guarde la modificación, entonces el encargado de la tarea debe recibir una notificación con las fechas actualizadas.
- Dado que se realice cualquier cambio crítico, cuando consulte el historial de notificaciones, entonces debo poder ver qué notificación se envió, a quién y cuándo.

### Tareas asignadas

- Programar lógica Backend
- Hacer manual de usuario
- Programar modal de alerta(Frontend)
- Hacer diagrama de secuencia

### Diagrama de Secuencia

![Screenshot 2025-11-13 193529.png](attachment:19cc96b9-202f-4e22-948e-244328e76b89:Screenshot_2025-11-13_193529.png)

---

## **H14: Alertar proximidad fechas de entregas de reportes**

**Prioridad: 2**

**Como** coordinadora regional,
**Quiero** que el sistema envíe de forma automática recordatorios a los responsables de las actividades correspondientes,
**Para** disminuir la carga laboral y evitar retrasos en las entregas.

### **Criterios de aceptación:**

- Dado que una tarea tiene una fecha límite definida, cuando falten X días u horas para su vencimiento, entonces el sistema debe enviar un recordatorio automático al responsable de la tarea.
- Dado que un responsable no ha marcado la tarea como completada, cuando la fecha límite esté muy próxima (ej. 24 horas antes), entonces el sistema debe enviar un recordatorio final de urgencia.
- Dado que se configure la periodicidad de los recordatorios, cuando llegue la fecha/hora correspondiente, entonces el sistema debe enviar el aviso respetando dicha configuración.
- Dado que un usuario reciba un recordatorio, cuando lo abra, entonces este debe contener información clara: nombre de la tarea, fecha límite y estado actual.

---

## **H15: Generar gráficos y reportes de avance**

**Prioridad: 4**

**Como** coordinadora regional,
**Quiero** que el sistema genere gráficos de avance y reportes de manera automática,
**Para** visualizar el progreso de los proyectos en tiempo real y contar con reportes descargables para análisis y presentación.

### **Criterios de aceptación:**

- Dado que existan datos de avance en el sistema, cuando el usuario acceda a la sección de reportes, entonces el sistema debe mostrar gráficos actualizados en tiempo real.
- Dado que el sistema genere un reporte, cuando el usuario lo solicite, entonces este debe estar disponible en formatos estándar (ejemplo: PDF, Excel).
- Dado que un proyecto tenga múltiples tareas, cuando se genere el gráfico de avance, entonces este debe reflejar el porcentaje de cumplimiento del proyecto en general.
- Dado que un usuario desee descargar un reporte, cuando haga clic en la opción de descarga, entonces el sistema debe entregar el archivo con los datos actualizados al momento de la solicitud.
- Dado que los reportes puedan compartirse, cuando el usuario los descargue, entonces deben incluir metadatos básicos (nombre del proyecto, fecha de generación, responsable).

### Tareas asignadas

- Crear boceto de graficas más importantes
- Documentarnos sobre la herramienta de visualización
- Consultas a las BD para nuestra visualización
- Implementar nuestra vista en nuestro frontend
- Hacer diagrama de secuencia
- Hacer manual de usuario

### Diagrama de Secuencia

![Screenshot 2025-11-13 193443.png](attachment:8e412e35-d16b-40be-9655-5dc0d6fc6149:Screenshot_2025-11-13_193443.png)

---

## **H16:  Exportar carta Gantt a Excel**

**Prioridad: 3**

**Como** coordinadora regional,
**Quiero** poder exportar la carta Gantt de mi proyecto a un archivo Excel con el mismo formato de la planilla original,
**Para** compartirlo fácilmente con mi equipo o usarlo fuera del sistema.

### **Criterios de aceptación:**

- Dado que estoy gestionando un proyecto, cuando seleccione la opción "Exportar a Excel", entonces el sistema debe generar un archivo Excel con todas las tareas del proyecto.
- Dado que el sistema genere el archivo, cuando lo abra en Excel, entonces debe mantener el mismo formato de la planilla original (columnas de nombre, fechas, encargado, progreso, etc.).
- Dado que una tarea fue modificada dentro del sistema, cuando exporte el proyecto, entonces el archivo Excel debe reflejar esos cambios actualizados.
- Dado que existen varios proyectos en el sistema, cuando elija exportar, entonces el archivo debe corresponder únicamente al proyecto seleccionado.
- Dado que la exportación fue exitosa, cuando termine el proceso, entonces el sistema debe ofrecer la descarga inmediata del archivo.

---

## **H17: Eliminar un proyecto desde el menú principal**

**Prioridad:  4**

**Como** coordinadora regional,
**Quiero** poder seleccionar y eliminar un proyecto desde el listado del menú principal,
**Para** mantener actualizada mi cartera de proyectos activos.

### **Criterios de aceptación:**

- Dado que estoy viendo la lista de proyectos, cuando seleccione un proyecto y elija la opción "Eliminar", entonces el sistema debe mostrar un mensaje pidiéndome confirmación antes de borrarlo permanentemente.
- Dado que he confirmado la eliminación de un proyecto, cuando la acción se complete, entonces el proyecto debe desaparecer de la lista.
- Dado que un proyecto ha sido eliminado, cuando intente buscarlo o acceder a él nuevamente, entonces no debe estar disponible en el sistema.

---

## H18: Visualizar historial de alertas enviadas

**Prioridad: 5**

**Como** coordinadora regional

**Quiero** que el sistema mantenga un registro de todas las alertas enviadas (con fecha, hora, destinatario y motivo)

**Para** tener trazabilidad y verificar que los recordatorios se entregaron correctamente.

### **Criterios de aceptación:**

- Dado que una alerta sea enviada (ya sea por vencimiento de tarea, reporte nacional o recordatorio), cuando el envío se ejecute, entonces el sistema debe guardar un registro con: proyecto, tarea, destinatario, fecha/hora y tipo de alerta.
- Dado que consulte el registro de alertas, cuando acceda a la sección de historial, entonces debo ver la lista completa en orden cronológico.
- Dado que filtre el historial, cuando seleccione criterios (ejemplo: por proyecto, por destinatario, por rango de fechas), entonces el sistema debe mostrar solo los resultados que cumplen con ese filtro.
- Dado que una alerta no pueda ser entregada (ejemplo: correo inválido), cuando esto ocurra, entonces el registro debe reflejar el intento fallido y el motivo.
