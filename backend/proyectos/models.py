from django.db import models

# Create your models here.
class Proyecto(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    

class LineaTrabajo(models.Model):
    id = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(Proyecto, related_name='lineas_trabajo', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre
    
    
class ProductoAsociado(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    extension = models.CharField(max_length=10)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)
    proyecto = models.ForeignKey(Proyecto, related_name='productos_asociados', on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre
    

class EstadoActividad(models.TextChoices):
    PENDIENTE = 'PEN', 'Pendiente'
    LISTO_PARA_COMENZAR = 'LPC', 'Listo para comenzar'
    EN_PROGRESO = 'EPR', 'En progreso'
    COMPLETADA = 'COM', 'Completada'
    TERMINADA = 'TER', 'Terminada'
    

# Clase base para herencia multi-table
class ActividadBase(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    n_act = models.IntegerField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(
        max_length=3,
        choices=EstadoActividad.choices,
        default=EstadoActividad.PENDIENTE
    )

    class Meta:
        abstract = False

    def tipo(self):
        if isinstance(self, ActividadDifusion):
            return "Difusión"
        else:
            return "Normal"

    def __str__(self):
        return self.nombre


# Actividades normales
class Actividad(ActividadBase):
    linea_trabajo = models.ForeignKey(LineaTrabajo, related_name='actividades', on_delete=models.CASCADE)
    producto_asociado = models.ForeignKey(ProductoAsociado, related_name='actividades', on_delete=models.SET_NULL, null=True, blank=True)


# Actividades de difusión
class ActividadDifusion(ActividadBase):
    proyecto = models.ForeignKey(Proyecto, related_name='actividades_difusion', on_delete=models.CASCADE)

    def __str__(self):
        return f"Difusión: {self.nombre}"


# Tabla de fechas, apuntando a la clase base
class Fecha(models.Model):
    actividad = models.ForeignKey(
        ActividadBase, related_name='fechas', on_delete=models.CASCADE
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.actividad.nombre}: {self.fecha_inicio} - {self.fecha_fin}"


class Alerta(models.Model):
    id = models.AutoField(primary_key=True)
    actividad = models.ForeignKey(ActividadBase, related_name='alertas', on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(db_index=True)
    enviado = models.BooleanField(default=True)

    class Meta:
        ordering = ["fecha_envio"]

    def __str__(self):
        return f"Alerta para {self.actividad.nombre}: {self.fecha_envio}"


class Encargado(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    correo_electronico = models.EmailField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    

class Actividad_Encargado(models.Model):
    actividad = models.ForeignKey(
        ActividadBase,
        related_name='actividad_encargados',
        on_delete=models.CASCADE
    )
    encargado = models.ForeignKey(
        Encargado,
        related_name='actividad_encargados',
        on_delete=models.CASCADE
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.actividad.nombre} - {self.encargado.nombre}"
    

class ActividadDifusion_Producto(models.Model):
    id = models.AutoField(primary_key=True)
    actividad = models.ForeignKey(ActividadDifusion, on_delete=models.CASCADE, related_name='actividad_productos')
    producto_asociado = models.ForeignKey(ProductoAsociado, on_delete=models.CASCADE, related_name='actividad_productos')
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.actividad.nombre} - {self.producto_asociado.nombre}"
    

class ActividadDifusion_Linea(models.Model):
    id = models.AutoField(primary_key=True)
    actividad = models.ForeignKey(ActividadDifusion, on_delete=models.CASCADE, related_name='actividad_lineas')
    linea_trabajo = models.ForeignKey(LineaTrabajo, on_delete=models.CASCADE, related_name='actividad_lineas')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.actividad.nombre} - {self.linea_trabajo.nombre}"
    


class RegistroCambioActividad(models.Model):
    actividad = models.ForeignKey(
        'ActividadBase',
        on_delete=models.CASCADE,
        related_name='registros_cambio'
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    cambios = models.JSONField() # JSON: {campo: {antes, despues}}

    class Meta:
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"Cambio en '{self.actividad.nombre}' el {self.fecha_cambio}"