"""
Gestor de plantillas de mensajes.
Maneja la creación, lectura y aplicación de plantillas con variables.
"""

import json
import os
import re


class TemplatesManager:
    """Administrador de plantillas de mensajes."""
    
    def __init__(self, data_file="data/plantillas.json"):
        """Inicializa el gestor de plantillas."""
        self.data_file = data_file
        self.templates = []
        self.load_templates()
    
    def load_templates(self):
        """Carga las plantillas desde el archivo JSON."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            except Exception as e:
                print(f"Error al cargar plantillas: {e}")
                self.templates = []
        else:
            # Crear archivo con plantillas de ejemplo
            self.templates = [
                {
                    "nombre": "Saludo simple",
                    "contenido": "Hola {Nombre}, ¿cómo estás?"
                },
                {
                    "nombre": "Recordatorio de pago",
                    "contenido": "Hola {Nombre}, te recordamos que tenés un saldo pendiente de {$ Asig.}. ¡Gracias!"
                }
            ]
            self.save_templates()
    
    def save_templates(self):
        """Guarda las plantillas en el archivo JSON."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al guardar plantillas: {e}")
            return False
    
    def add_template(self, name, content):
        """Agrega una nueva plantilla."""
        if not name or name.strip() == "":
            return False, "El nombre no puede estar vacío"
        
        if not content or content.strip() == "":
            return False, "El contenido no puede estar vacío"
        
        # Verificar si ya existe
        if any(t['nombre'] == name for t in self.templates):
            return False, "Ya existe una plantilla con ese nombre"
        
        template = {
            "nombre": name,
            "contenido": content
        }
        
        self.templates.append(template)
        
        if self.save_templates():
            return True, "Plantilla creada exitosamente"
        else:
            return False, "Error al guardar la plantilla"
    
    def delete_template(self, name):
        """Elimina una plantilla por nombre."""
        self.templates = [t for t in self.templates if t['nombre'] != name]
        return self.save_templates()
    
    def get_templates(self):
        """Retorna la lista de plantillas."""
        return self.templates
    
    def get_template_by_name(self, name):
        """Retorna una plantilla específica por nombre."""
        for template in self.templates:
            if template['nombre'] == name:
                return template
        return None

    def format_value(self, var, value):
        """Da formato especial a variables conocidas.

        Actualmente formatea los montos monetarios para mostrarlos como pesos
        con separadores de miles y dos decimales.
        """
        currency_fields = {'$ Hist.', '$ Asig.'}

        if var in currency_fields:
            try:
                number = float(value)
                formatted = f"{number:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                return f"$ {formatted}"
            except (TypeError, ValueError):
                # Si no se puede convertir a número, devolver tal cual
                return str(value)

        return str(value)

    def apply_template(self, template_content, data):
        """
        Aplica una plantilla reemplazando variables con datos.
        
        Args:
            template_content: Contenido de la plantilla con variables {columna}
            data: Diccionario con los datos del contacto
            
        Returns:
            Mensaje con variables reemplazadas
        """
        message = template_content
        
        # Encontrar todas las variables {columna}
        variables = re.findall(r'\{([^}]+)\}', template_content)
        
        # Reemplazar cada variable
        for var in variables:
            if var in data:
                value = self.format_value(var, data[var])
                message = message.replace(f'{{{var}}}', value)
            else:
                # Si no existe la columna, dejar la variable
                pass
        
        return message
    
    def get_variables_from_template(self, template_content):
        """
        Extrae las variables de una plantilla.
        
        Args:
            template_content: Contenido de la plantilla
            
        Returns:
            Lista de nombres de variables
        """
        return re.findall(r'\{([^}]+)\}', template_content)
