from django import forms


class UploadExcelForm(forms.Form):
    nombre_proyecto = forms.CharField(
        label='Nombre del proyecto',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Debes ingresar un nombre para el proyecto',
            'max_length': 'El nombre no puede tener más de 100 caracteres'
        }
    )
    archivo = forms.FileField(
        label='Archivo Excel',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'}),
        error_messages={
            'required': 'Debes seleccionar un archivo Excel'
        }
    )