"""
Pestaña de gestión de perfiles.
Permite crear, listar, activar/desactivar y abrir navegadores para cada perfil.
"""

import os
import platform
import shutil
import subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLineEdit, QLabel, QMessageBox, QSizePolicy,
                               QScrollArea, QGroupBox, QFileDialog)
from PySide6.QtCore import Qt
from core.profiles_manager import ProfilesManager
from core.excel_processor import ExcelProcessor


class ProfilesTab(QWidget):
    """Pestaña para gestionar perfiles de líneas telefónicas."""
    
    def __init__(self):
        super().__init__()
        self.profiles_manager = ProfilesManager()
        self.excel_processor = ExcelProcessor()
        self.last_uploaded_excel = None
        self.browser_processes = {}
        self.init_ui()
        self.load_profiles()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title = QLabel("Perfiles y contactos")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Gestioná tus líneas y carga un Excel en el mismo lugar."
        )
        subtitle.setStyleSheet("color: #b3b3b3; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        # Sección de crear nuevo perfil
        create_group = QGroupBox("Crear perfil nuevo")
        create_layout = QHBoxLayout(create_group)
        create_layout.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del nuevo perfil...")
        self.name_input.setMinimumHeight(35)
        
        self.create_btn = QPushButton("Crear Perfil")
        self.create_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.create_btn.setMinimumHeight(35)
        self.create_btn.clicked.connect(self.create_profile)
        
        create_layout.addWidget(self.name_input)
        create_layout.addWidget(self.create_btn)

        layout.addWidget(create_group)

        # Bloque rápido para cargar Excel
        excel_group = QGroupBox("Contactos desde Excel")
        excel_layout = QVBoxLayout(excel_group)
        excel_layout.setSpacing(6)

        excel_info = QLabel(
            "📥 Seleccioná tu archivo y lo procesamos automáticamente para que "
            "esté listo en las campañas."
        )
        excel_info.setWordWrap(True)
        excel_layout.addWidget(excel_info)

        self.upload_excel_btn = QPushButton("Cargar y procesar Excel")
        self.upload_excel_btn.setMinimumHeight(35)
        self.upload_excel_btn.clicked.connect(self.upload_excel_file)
        excel_layout.addWidget(self.upload_excel_btn)

        self.excel_status_label = QLabel("Todavía no cargaste ningún archivo.")
        self.excel_status_label.setStyleSheet("color: #bbbbbb;")
        excel_layout.addWidget(self.excel_status_label)

        layout.addWidget(excel_group)

        # Contenedor de perfiles
        profiles_group = QGroupBox("Perfiles creados")
        profiles_group.setStyleSheet(
            "QGroupBox { font-weight: bold; }"
            "QGroupBox::title { subcontrol-position: top left; padding: 6px 8px; }"
        )
        profiles_layout = QVBoxLayout(profiles_group)
        profiles_layout.setContentsMargins(10, 10, 10, 10)
        profiles_layout.setSpacing(10)

        self.profiles_container = QWidget()
        self.profiles_layout = QVBoxLayout(self.profiles_container)
        self.profiles_layout.setContentsMargins(0, 0, 0, 0)
        self.profiles_layout.setSpacing(8)

        profiles_layout.addWidget(self.profiles_container)
        layout.addWidget(profiles_group)
        
        layout.addStretch()
        scroll.setWidget(container)
    
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

        # Limpiar contenedor
        while self.profiles_layout.count():
            item = self.profiles_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        button_style = (
            "QPushButton {"
            "background-color: #12354a;"
            "color: white;"
            "border: 2px solid #1f5c7a;"
            "border-radius: 10px;"
            "padding: 4px 14px;"
            "font-weight: 600;"
            "}"
            "QPushButton:hover {"
            "background-color: #1d4f6d;"
            "}"
        )

        secondary_style = (
            "QPushButton {"
            "background-color: #2c3e50;"
            "color: white;"
            "border: 2px solid #3d566e;"
            "border-radius: 10px;"
            "padding: 4px 14px;"
            "font-weight: 600;"
            "}"
            "QPushButton:hover {"
            "background-color: #34495e;"
            "}"
        )

        danger_style = (
            "QPushButton {"
            "background-color: #c0392b;"
            "color: white;"
            "border: 2px solid #e74c3c;"
            "border-radius: 10px;"
            "padding: 4px 14px;"
            "font-weight: 600;"
            "}"
            "QPushButton:hover {"
            "background-color: #a93226;"
            "}"
        )

        if not profiles:
            empty_label = QLabel(
                "No hay perfiles creados todavía. Agrega uno para empezar."
            )
            empty_label.setStyleSheet("color: #9b9b9b;")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setMinimumHeight(80)
            self.profiles_layout.addWidget(empty_label)
            return

        for profile in profiles:
            card = QGroupBox()
            card.setStyleSheet(
                "QGroupBox {"
                "  border: 1px solid #2b3a48;"
                "  border-radius: 10px;"
                "  padding: 10px;"
                "  background: #0f1820;"
                "}"
            )

            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)
            card_layout.setSpacing(12)

            name_label = QLabel(profile['nombre'])
            name_label.setStyleSheet("font-size: 14px; font-weight: 600;")
            card_layout.addWidget(name_label, stretch=1)

            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout(buttons_widget)
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(8)

            open_btn = QPushButton("Abrir")
            open_btn.setMinimumWidth(70)
            open_btn.setStyleSheet(button_style)
            open_btn.clicked.connect(
                lambda checked, name=profile['nombre']: self.open_browser(name)
            )
            buttons_layout.addWidget(open_btn)

            close_btn = QPushButton("Cerrar")
            close_btn.setMinimumWidth(70)
            close_btn.setStyleSheet(secondary_style)
            close_btn.clicked.connect(
                lambda checked, name=profile['nombre']: self.close_browser(name)
            )
            buttons_layout.addWidget(close_btn)

            delete_btn = QPushButton("Eliminar")
            delete_btn.setMinimumWidth(70)
            delete_btn.setStyleSheet(danger_style)
            delete_btn.clicked.connect(
                lambda checked, name=profile['nombre']: self.delete_profile(name)
            )
            buttons_layout.addWidget(delete_btn)

            card_layout.addWidget(buttons_widget)
            self.profiles_layout.addWidget(card)

        self.profiles_layout.addStretch()

    def upload_excel_file(self):
        """Sube y procesa un archivo Excel/CSV desde el bloque de perfiles."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo Excel/CSV",
            "",
            "Archivos Excel/CSV (*.xlsx *.xls *.csv)"
        )

        if not file_path:
            return

        try:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.excel_processor.uploads_dir, filename)
            shutil.copy2(file_path, dest_path)

            success, message, count = self.excel_processor.process_file(filename)

            if success:
                self.last_uploaded_excel = filename
                self.excel_status_label.setText(
                    f"✅ '{filename}' procesado ({count} registros)."
                )
                QMessageBox.information(self, "Excel procesado", message)
            else:
                QMessageBox.critical(self, "Error", message)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cargar el archivo:\n{str(e)}"
            )
    
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
        
        existing_process = self.browser_processes.get(profile_name)
        if existing_process:
            if existing_process.poll() is None:
                QMessageBox.information(
                    self,
                    "Perfil ya abierto",
                    f"El perfil '{profile_name}' ya tiene un navegador abierto."
                )
                return
            else:
                self.browser_processes.pop(profile_name, None)

        # Comando completo
        cmd = [
            chrome_exe,
            f'--user-data-dir={profile_path}',
            '--profile-directory=Default',
            'https://messages.google.com/web'
        ]

        try:
            process = subprocess.Popen(cmd)
            self.browser_processes[profile_name] = process
            QMessageBox.information(
                self,
                "Navegador abierto",
                f"Chrome abierto para el perfil '{profile_name}'.\n"
                "Si es la primera vez, deberás iniciar sesión en Google Messages."
            )
        except Exception as e:
            self.browser_processes.pop(profile_name, None)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir Chrome:\n{str(e)}"
            )

    def close_browser(self, profile_name):
        """Cierra el navegador abierto para un perfil si existe."""
        process = self.browser_processes.get(profile_name)

        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

            QMessageBox.information(
                self,
                "Navegador cerrado",
                f"Se cerró el navegador del perfil '{profile_name}'."
            )
        else:
            QMessageBox.information(
                self,
                "Navegador no encontrado",
                f"No hay un navegador abierto para el perfil '{profile_name}'."
            )

        self.browser_processes.pop(profile_name, None)
    
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
