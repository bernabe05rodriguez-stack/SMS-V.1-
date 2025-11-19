"""
Pestaña de gestión de perfiles.
Permite crear, listar, activar/desactivar y abrir navegadores para cada perfil.
"""

import os
import platform
import subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLineEdit, QTableWidget, QTableWidgetItem, 
                               QLabel, QMessageBox, QHeaderView, QCheckBox)
from PySide6.QtCore import Qt
from core.profiles_manager import ProfilesManager


class ProfilesTab(QWidget):
    """Pestaña para gestionar perfiles de líneas telefónicas."""
    
    def __init__(self):
        super().__init__()
        self.profiles_manager = ProfilesManager()
        self.init_ui()
        self.load_profiles()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Gestión de Perfiles")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Sección de crear nuevo perfil
        create_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del nuevo perfil...")
        self.name_input.setMinimumHeight(35)
        
        self.create_btn = QPushButton("Crear Perfil")
        self.create_btn.setMinimumHeight(35)
        self.create_btn.clicked.connect(self.create_profile)
        
        create_layout.addWidget(QLabel("Nombre:"))
        create_layout.addWidget(self.name_input)
        create_layout.addWidget(self.create_btn)
        
        layout.addLayout(create_layout)
        
        # Tabla de perfiles
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Nombre", "Activo", "Abrir Navegador", "Eliminar"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(400)
        
        layout.addWidget(self.table)
        
        # Información
        info_label = QLabel("💡 Los perfiles activos se usarán en las campañas de envío")
        info_label.setStyleSheet("color: #888; margin: 10px;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
    
    def create_profile(self):
        """Crea un nuevo perfil."""
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Error", "Debe ingresar un nombre para el perfil")
            return
        
        success, message = self.profiles_manager.add_profile(name)
        
        if success:
            QMessageBox.information(self, "Éxito", message)
            self.name_input.clear()
            self.load_profiles()
        else:
            QMessageBox.warning(self, "Error", message)
    
    def load_profiles(self):
        """Carga los perfiles en la tabla."""
        profiles = self.profiles_manager.get_profiles()
        self.table.setRowCount(len(profiles))
        
        for row, profile in enumerate(profiles):
            # Nombre
            name_item = QTableWidgetItem(profile['nombre'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # Checkbox activo
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            
            checkbox = QCheckBox()
            checkbox.setChecked(profile.get('activo', True))
            checkbox.stateChanged.connect(
                lambda state, name=profile['nombre']: self.toggle_profile_status(name, state)
            )
            
            checkbox_layout.addWidget(checkbox)
            self.table.setCellWidget(row, 1, checkbox_widget)
            
            # Botón abrir navegador
            open_btn = QPushButton("Abrir Chrome")
            open_btn.clicked.connect(lambda checked, name=profile['nombre']: self.open_browser(name))
            self.table.setCellWidget(row, 2, open_btn)
            
            # Botón eliminar
            delete_btn = QPushButton("Eliminar")
            delete_btn.setStyleSheet("background-color: #c0392b; color: white;")
            delete_btn.clicked.connect(lambda checked, name=profile['nombre']: self.delete_profile(name))
            self.table.setCellWidget(row, 3, delete_btn)
    
    def toggle_profile_status(self, name, state):
        """Cambia el estado activo de un perfil."""
        active = (state == Qt.Checked.value)
        self.profiles_manager.update_profile_status(name, active)
    
    def open_browser(self, profile_name):
        """Abre Chrome con el perfil específico en Google Messages."""
        profile_path = self.profiles_manager.get_profile_path(profile_name)
        
        # Comando para abrir Chrome
        chrome_paths = {
            'Windows': [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            ],
            'Darwin': [  # macOS
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            ],
            'Linux': [
                '/usr/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
            ]
        }
        
        system = platform.system()
        chrome_exe = None
        
        # Buscar Chrome instalado
        for path in chrome_paths.get(system, []):
            if os.path.exists(path):
                chrome_exe = path
                break
        
        if not chrome_exe:
            QMessageBox.warning(
                self, 
                "Chrome no encontrado",
                "No se pudo encontrar Google Chrome en tu sistema.\n"
                "Por favor, instala Chrome o ajusta la ruta manualmente."
            )
            return
        
        # Comando completo
        cmd = [
            chrome_exe,
            f'--user-data-dir={profile_path}',
            '--profile-directory=Default',
            'https://messages.google.com/web'
        ]
        
        try:
            subprocess.Popen(cmd)
            QMessageBox.information(
                self,
                "Navegador abierto",
                f"Chrome abierto para el perfil '{profile_name}'.\n"
                "Si es la primera vez, deberás iniciar sesión en Google Messages."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir Chrome:\n{str(e)}"
            )
    
    def delete_profile(self, profile_name):
        """Elimina un perfil."""
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar el perfil '{profile_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.profiles_manager.delete_profile(profile_name):
                QMessageBox.information(self, "Éxito", "Perfil eliminado")
                self.load_profiles()
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el perfil")
