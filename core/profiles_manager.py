"""
Gestor de perfiles de líneas telefónicas.
Maneja la creación, lectura, actualización y eliminación de perfiles.
"""

import json
import os
from pathlib import Path


class ProfilesManager:
    """Administrador de perfiles de líneas telefónicas."""
    
    def __init__(self, data_file="data/perfiles.json"):
        """Inicializa el gestor de perfiles."""
        self.data_file = data_file
        self.profiles = []
        self.load_profiles()
    
    def load_profiles(self):
        """Carga los perfiles desde el archivo JSON."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.profiles = json.load(f)
            except Exception as e:
                print(f"Error al cargar perfiles: {e}")
                self.profiles = []
        else:
            # Crear archivo vacío si no existe
            self.profiles = []
            self.save_profiles()
    
    def save_profiles(self):
        """Guarda los perfiles en el archivo JSON."""
        try:
            # Asegurar que existe el directorio
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al guardar perfiles: {e}")
            return False
    
    def add_profile(self, name):
        """Agrega un nuevo perfil."""
        if not name or name.strip() == "":
            return False, "El nombre no puede estar vacío"
        
        # Verificar si ya existe
        if any(p['nombre'] == name for p in self.profiles):
            return False, "Ya existe un perfil con ese nombre"
        
        profile = {
            "nombre": name,
            "activo": True
        }
        
        self.profiles.append(profile)
        
        if self.save_profiles():
            return True, "Perfil creado exitosamente"
        else:
            return False, "Error al guardar el perfil"
    
    def delete_profile(self, name):
        """Elimina un perfil por nombre."""
        self.profiles = [p for p in self.profiles if p['nombre'] != name]
        return self.save_profiles()
    
    def update_profile_status(self, name, active):
        """Actualiza el estado activo de un perfil."""
        for profile in self.profiles:
            if profile['nombre'] == name:
                profile['activo'] = active
                return self.save_profiles()
        return False
    
    def get_profiles(self):
        """Retorna la lista de perfiles."""
        return self.profiles
    
    def get_active_profiles(self):
        """Retorna solo los perfiles activos."""
        return [p for p in self.profiles if p.get('activo', False)]
    
    def get_profile_path(self, profile_name):
        """Retorna la ruta del directorio de datos del perfil."""
        base_path = Path("profiles_storage")
        profile_path = base_path / profile_name
        
        # Crear directorio si no existe
        profile_path.mkdir(parents=True, exist_ok=True)
        
        return str(profile_path.absolute())
