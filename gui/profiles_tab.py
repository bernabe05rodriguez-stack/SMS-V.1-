"""
Pestaña de gestión de perfiles.
Permite crear, listar, activar/desactivar y abrir navegadores para cada perfil.
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLineEdit, QLabel, QMessageBox, QSizePolicy,
                               QScrollArea, QGroupBox, QFileDialog, QCheckBox,
                               QFrame)
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
        self.load_saved_excel_preferences()
    
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
        create_group.setStyleSheet(
            "QGroupBox {"
            "  border: 1px solid #1f2d38;"
            "  border-radius: 12px;"
            "  padding: 12px;"
            "  background: #0f1820;"
            "}"
            "QGroupBox::title { font-weight: 700; padding: 4px 8px; }"
        )
        create_layout = QVBoxLayout(create_group)
        create_layout.setSpacing(10)

        create_hint = QLabel("Poné un nombre claro para ubicar rápido el perfil.")
        create_hint.setStyleSheet("color: #9fb3c8;")
        create_layout.addWidget(create_hint)

        form_row = QHBoxLayout()
        form_row.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Soporte - Línea 1")
        self.name_input.setMinimumHeight(38)
        self.name_input.setStyleSheet(
            "QLineEdit {"
            "  border: 1px solid #2b3a48;"
            "  border-radius: 10px;"
            "  padding: 6px 10px;"
            "  background: #0a121a;"
            "  color: #e5e5e5;"
            "}"
            "QLineEdit:focus { border-color: #1f5c7a; }"
        )

        self.create_btn = QPushButton("Crear perfil")
        self.create_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.create_btn.setMinimumHeight(38)
        self.create_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #1f5c7a;"
            "  color: white;"
            "  border: 2px solid #2f7aa2;"
            "  border-radius: 10px;"
            "  padding: 6px 14px;"
            "  font-weight: 700;"
            "}"
            "QPushButton:hover { background-color: #26749b; }"
        )
        self.create_btn.clicked.connect(self.create_profile)

        form_row.addWidget(self.name_input)
        form_row.addWidget(self.create_btn)
        create_layout.addLayout(form_row)

        layout.addWidget(create_group)

        # Botón para desplegar perfiles creados
        self.toggle_profiles_btn = QPushButton("Mostrar perfiles creados")
        self.toggle_profiles_btn.setCheckable(True)
        self.toggle_profiles_btn.setChecked(False)
        self.toggle_profiles_btn.setMinimumHeight(32)
        self.toggle_profiles_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #12354a;"
            "  color: white;"
            "  border: 1px solid #1f5c7a;"
            "  border-radius: 8px;"
            "  padding: 4px 10px;"
            "  font-weight: 600;"
            "}"
            "QPushButton:hover { background-color: #1d4f6d; }"
            "QPushButton:checked { background-color: #1f5c7a; }"
        )
        self.toggle_profiles_btn.toggled.connect(self.toggle_profiles_section)
        layout.addWidget(self.toggle_profiles_btn)

        # Contenedor de perfiles (colapsable)
        self.profiles_group = QGroupBox("Perfiles creados")
        self.profiles_group.setStyleSheet(
            "QGroupBox {"
            "  font-weight: bold;"
            "  border: 1px solid #2b3a48;"
            "  border-radius: 12px;"
            "  padding: 10px;"
            "  background: #0f1820;"
            "}"
            "QGroupBox::title { subcontrol-position: top left; padding: 6px 8px; }"
        )
        profiles_layout = QVBoxLayout(self.profiles_group)
        profiles_layout.setContentsMargins(10, 10, 10, 10)
        profiles_layout.setSpacing(10)

        self.profiles_container = QWidget()
        self.profiles_layout = QVBoxLayout(self.profiles_container)
        self.profiles_layout.setContentsMargins(0, 0, 0, 0)
        self.profiles_layout.setSpacing(8)

        profiles_layout.addWidget(self.profiles_container)
        self.profiles_group.setVisible(False)
        layout.addWidget(self.profiles_group)

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

        # Selector de campos telefónicos detectados
        self.phone_fields_label = QLabel(
            "📞 Elegí qué columnas de teléfono querés usar para las campañas."
        )
        self.phone_fields_label.setWordWrap(True)
        self.phone_fields_label.setStyleSheet("color: #9fb3c8;")
        excel_layout.addWidget(self.phone_fields_label)

        self.phone_fields_container = QWidget()
        self.phone_fields_layout = QVBoxLayout(self.phone_fields_container)
        self.phone_fields_layout.setContentsMargins(6, 2, 6, 2)
        self.phone_fields_layout.setSpacing(4)
        excel_layout.addWidget(self.phone_fields_container)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        excel_layout.addWidget(line)

        # Selector de variables disponibles
        self.variables_hint_label = QLabel(
            "🏷️ Seleccioná qué columnas del Excel querés usar en tus mensajes."
        )
        self.variables_hint_label.setWordWrap(True)
        self.variables_hint_label.setStyleSheet("color: #9fb3c8;")
        excel_layout.addWidget(self.variables_hint_label)

        self.variables_container = QWidget()
        self.variables_layout = QVBoxLayout(self.variables_container)
        self.variables_layout.setContentsMargins(6, 2, 6, 2)
        self.variables_layout.setSpacing(4)
        excel_layout.addWidget(self.variables_container)

        layout.addWidget(excel_group)
        
        layout.addStretch()
        scroll.setWidget(container)

    def toggle_profiles_section(self, checked):
        """Muestra u oculta el bloque de perfiles creados."""
        self.profiles_group.setVisible(checked)
        if checked:
            self.toggle_profiles_btn.setText("Ocultar perfiles creados")
        else:
            self.toggle_profiles_btn.setText("Mostrar perfiles creados")
    
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

    def load_saved_excel_preferences(self):
        """Carga las preferencias guardadas de teléfonos y variables al iniciar."""
        prefs = self.excel_processor.load_preferences()

        if prefs.get("last_file"):
            processed_path = os.path.join(
                self.excel_processor.processed_dir,
                prefs["last_file"],
            )

            if os.path.exists(processed_path):
                self.last_uploaded_excel = prefs["last_file"]
                self.excel_status_label.setText(
                    f"⚡ Usando el último Excel procesado: {prefs['last_file']}"
                )
                self.render_excel_metadata(prefs["last_file"])

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
                processed_name = f"{Path(filename).stem}_processed.json"
                self.last_uploaded_excel = processed_name
                self.excel_status_label.setText(
                    f"✅ '{filename}' procesado ({count} registros)."
                )
                self.excel_processor.update_preferences(
                    {
                        "last_file": processed_name,
                    }
                )
                self.render_excel_metadata(processed_name)
                QMessageBox.information(self, "Excel procesado", message)
            else:
                QMessageBox.critical(self, "Error", message)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cargar el archivo:\n{str(e)}"
            )

    def render_excel_metadata(self, processed_filename):
        """Muestra selector de teléfonos y variables según el archivo procesado."""
        contacts = self.excel_processor.load_processed_file(processed_filename) or []

        if not contacts:
            self.phone_fields_label.setText(
                "⚠️ No se pudieron leer teléfonos desde el Excel cargado."
            )
            self.variables_hint_label.setText(
                "⚠️ No hay columnas disponibles para seleccionar variables."
            )
            return

        prefs = self.excel_processor.load_preferences()
        available_phone_fields = self.excel_processor.get_phone_fields_from_contacts(contacts)
        selected_phone_fields = prefs.get("selected_phone_fields") or available_phone_fields

        self.build_phone_field_selector(
            available_phone_fields,
            selected_phone_fields,
            contacts,
        )

        available_columns = list(contacts[0].keys())
        default_variables = [
            col for col in available_columns
            if not col.startswith("Telefono_") or col == "Telefono_1"
        ]
        selected_variables = prefs.get("selected_variables") or default_variables
        self.build_variables_selector(available_columns, selected_variables)

        self.excel_processor.update_preferences(
            {
                "selected_phone_fields": selected_phone_fields,
                "selected_variables": selected_variables,
                "last_file": processed_filename,
            }
        )

    def build_phone_field_selector(self, available_fields, selected_fields, contacts):
        """Crea las casillas para elegir columnas de teléfono."""
        while self.phone_fields_layout.count():
            item = self.phone_fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not available_fields:
            self.phone_fields_label.setText(
                "⚠️ No se detectaron columnas con formato Telefono_1 ... Telefono_9."
            )
            return

        self.phone_fields_label.setText(
            "📞 Seleccioná las columnas de teléfono a incluir en la campaña:"
        )

        for field in available_fields:
            count = len([
                c for c in contacts
                if str(c.get('Telefono_origen', 'Telefono_1')) == field
            ])
            checkbox = QCheckBox(f"{field} ({count} números)")
            checkbox.setChecked(field in selected_fields)
            checkbox.stateChanged.connect(self.save_phone_field_preferences)
            checkbox.setProperty("field_name", field)
            self.phone_fields_layout.addWidget(checkbox)

    def build_variables_selector(self, available_columns, selected_columns):
        """Crea las casillas para elegir variables disponibles."""
        while self.variables_layout.count():
            item = self.variables_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not available_columns:
            self.variables_hint_label.setText(
                "⚠️ No hay columnas disponibles en el archivo procesado."
            )
            return

        self.variables_hint_label.setText(
            "🏷️ Marca las variables que vas a usar en tus mensajes:"
        )

        for column in available_columns:
            checkbox = QCheckBox(column)
            checkbox.setChecked(column in selected_columns)
            checkbox.stateChanged.connect(self.save_variable_preferences)
            checkbox.setProperty("column_name", column)
            self.variables_layout.addWidget(checkbox)

    def save_phone_field_preferences(self):
        """Guarda la selección de columnas de teléfono."""
        selected = []
        for i in range(self.phone_fields_layout.count()):
            item = self.phone_fields_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QCheckBox) and widget.isChecked():
                field_name = widget.property("field_name")
                if field_name:
                    selected.append(field_name)

        self.excel_processor.update_preferences({"selected_phone_fields": selected})

    def save_variable_preferences(self):
        """Guarda la selección de variables disponibles."""
        selected = []
        for i in range(self.variables_layout.count()):
            item = self.variables_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QCheckBox) and widget.isChecked():
                column_name = widget.property("column_name")
                if column_name:
                    selected.append(column_name)

        self.excel_processor.update_preferences({"selected_variables": selected})
    
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
