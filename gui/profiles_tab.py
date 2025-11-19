"""
Pestaña de gestión de perfiles.
Permite crear, listar, activar/desactivar y abrir navegadores para cada perfil.
"""

import os
import platform
import shutil
import subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLineEdit, QTableWidget, QTableWidgetItem,
                               QLabel, QMessageBox, QHeaderView, QCheckBox,
                               QSizePolicy, QScrollArea, QGroupBox,
                               QFileDialog)
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
        title = QLabel("Perfiles activos y contactos")
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

        # Tabla de perfiles
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Perfil", "Activo", "Acciones"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(400)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.table)
        
        # Información
        info_label = QLabel("💡 Los perfiles activos se usarán en las campañas de envío")
        info_label.setStyleSheet("color: #888; margin: 10px;")
        layout.addWidget(info_label)
        
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
            
            # Acciones
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(6)

            open_btn = QPushButton("Abrir")
            open_btn.setMinimumHeight(28)
            open_btn.clicked.connect(
                lambda checked, name=profile['nombre']: self.open_browser(name)
            )
            actions_layout.addWidget(open_btn)

            delete_btn = QPushButton("Eliminar")
            delete_btn.setStyleSheet("background-color: #c0392b; color: white;")
            delete_btn.setMinimumHeight(28)
            delete_btn.clicked.connect(
                lambda checked, name=profile['nombre']: self.delete_profile(name)
            )
            actions_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 2, actions_widget)

    def toggle_profile_status(self, name, state):
        """Cambia el estado activo de un perfil."""
        active = (state == Qt.CheckState.Checked)
        self.profiles_manager.update_profile_status(name, active)

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
