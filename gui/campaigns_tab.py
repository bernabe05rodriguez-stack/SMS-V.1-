"""
Pestaña de gestión de campañas.
Permite crear campañas seleccionando plantillas, perfiles y contactos.
Diseño moderno y atractivo.
"""

from html import escape

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTextEdit, QLineEdit, QComboBox,
                               QSpinBox, QMessageBox, QGroupBox,
                               QFormLayout, QCheckBox, QScrollArea)
from PySide6.QtCore import Qt, QThread, Signal
import threading
from core.templates_manager import TemplatesManager
from core.profiles_manager import ProfilesManager
from core.excel_processor import ExcelProcessor
from core.sending_engine import SendingEngine


class SendingThread(QThread):
    """Thread para envío de mensajes en segundo plano."""
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, campaign_id, sending_engine):
        super().__init__()
        self.campaign_id = campaign_id
        self.sending_engine = sending_engine
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

    def run(self):
        """Ejecuta el envío de la campaña."""
        try:
            success, message = self.sending_engine.start_campaign(
                self.campaign_id,
                self.progress,
                stop_event=self.stop_event,
                pause_event=self.pause_event
            )
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"Error en el envío: {str(e)}")

    def pause(self):
        """Pausa el envío."""
        self.pause_event.set()

    def resume(self):
        """Reanuda el envío pausado."""
        self.pause_event.clear()

    def cancel(self):
        """Cancela el envío en curso."""
        self.stop_event.set()


class CampaignsTab(QWidget):
    """Pestaña para crear y gestionar campañas de envío."""

    def __init__(self, status_tab=None):
        super().__init__()
        self.status_tab = status_tab
        self.templates_manager = TemplatesManager()
        self.profiles_manager = ProfilesManager()
        self.excel_processor = ExcelProcessor()
        self.sending_engine = SendingEngine()
        self.sending_thread = None
        self.current_contacts_file = None
        self.sample_contact = None
        self.available_columns = []
        self.loaded_contacts = []
        self.phone_checkboxes = []

        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_layout.addWidget(main_scroll)

        container = QWidget()
        container.setObjectName("campaignContainer")
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        container.setStyleSheet("""
            #campaignContainer {
                background: #0a121a;
            }
            QGroupBox {
                background: #0f1820;
                border: 1px solid #2b3a48;
                border-radius: 12px;
                margin-top: 18px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 10px;
                color: #e5e5e5;
                font-weight: 700;
            }
            QLabel.hint-text {
                color: #9fb3c8;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: #0a121a;
                border: 1px solid #2b3a48;
                border-radius: 10px;
                padding: 8px 10px;
                font-size: 13px;
                color: #e5e5e5;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 18px;
            }
            QTextEdit {
                background: #0a121a;
                border: 1px solid #2b3a48;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                line-height: 1.5;
                color: #e5e5e5;
            }
        """)

        # Título con estilo
        title = QLabel("🚀 Gestión de Campañas")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #e5e5e5;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Configura y envía tus campañas de SMS de forma automática")
        subtitle.setStyleSheet("color: #9fb3c8; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        # Sección de configuración de campaña
        config_group = QGroupBox("⚙️ Configuración Básica")
        config_group.setObjectName("configGroup")
        config_group.setStyleSheet("""
            #configGroup {
                border: 1px solid #2b3a48;
                background: #0f1820;
            }
            #configGroup::title {
                color: #e5e5e5;
            }
        """)
        config_layout = QFormLayout()
        config_layout.setSpacing(12)

        # Nombre de campaña
        self.campaign_name_input = QLineEdit()
        self.campaign_name_input.setPlaceholderText("Ej: Campaña Enero 2025")
        self.campaign_name_input.setMinimumHeight(40)
        config_layout.addRow("📝 Nombre:", self.campaign_name_input)

        # Información de contactos automática
        self.contacts_info_label = QLabel(
            "Se usará automáticamente el último Excel procesado desde la pestaña Perfiles."
        )
        self.contacts_info_label.setWordWrap(True)
        self.contacts_info_label.setStyleSheet("color: #9fb3c8;")
        config_layout.addRow("📊 Contactos:", self.contacts_info_label)

        # Delay entre mensajes
        delay_layout = QHBoxLayout()
        self.delay_min_spin = QSpinBox()
        self.delay_min_spin.setMinimum(1)
        self.delay_min_spin.setMaximum(300)
        self.delay_min_spin.setValue(1)
        self.delay_min_spin.setSuffix(" seg")
        self.delay_min_spin.setMinimumHeight(40)
        self.delay_min_spin.valueChanged.connect(self.sync_delay_bounds)
        delay_layout.addWidget(QLabel("Entre"))
        delay_layout.addWidget(self.delay_min_spin)

        self.delay_max_spin = QSpinBox()
        self.delay_max_spin.setMinimum(1)
        self.delay_max_spin.setMaximum(300)
        self.delay_max_spin.setValue(3)
        self.delay_max_spin.setSuffix(" seg")
        self.delay_max_spin.setMinimumHeight(40)
        self.delay_max_spin.valueChanged.connect(self.sync_delay_bounds)
        delay_layout.addWidget(QLabel("y"))
        delay_layout.addWidget(self.delay_max_spin)

        self.sync_delay_bounds()

        config_layout.addRow("⏱️ Delay entre mensajes:", delay_layout)

        config_group.setLayout(config_layout)

        # Selección de teléfonos
        numbers_group = QGroupBox("📞 Teléfonos destino")
        numbers_group.setObjectName("numbersGroup")
        numbers_group.setStyleSheet("""
            #numbersGroup {
                border: 1px solid #2b3a48;
                background: #0f1820;
            }
            #numbersGroup::title {
                color: #e5e5e5;
            }
        """)
        numbers_layout = QVBoxLayout()
        numbers_layout.setSpacing(8)

        self.numbers_info_label = QLabel(
            "Cargá un Excel desde Perfiles para listar los teléfonos disponibles."
        )
        self.numbers_info_label.setStyleSheet("color: #9fb3c8;")
        self.numbers_info_label.setWordWrap(True)
        numbers_layout.addWidget(self.numbers_info_label)

        self.select_all_numbers = QCheckBox("Seleccionar todos")
        self.select_all_numbers.stateChanged.connect(self.toggle_all_numbers)
        numbers_layout.addWidget(self.select_all_numbers)

        self.numbers_container = QWidget()
        self.numbers_container_layout = QVBoxLayout(self.numbers_container)
        self.numbers_container_layout.setSpacing(6)
        self.numbers_container_layout.setContentsMargins(4, 4, 4, 4)

        numbers_scroll = QScrollArea()
        numbers_scroll.setWidgetResizable(True)
        numbers_scroll.setMaximumHeight(160)
        numbers_scroll.setWidget(self.numbers_container)
        numbers_layout.addWidget(numbers_scroll)

        numbers_group.setLayout(numbers_layout)

        # Sección de variables disponibles
        variables_group = QGroupBox("🏷️ Variables Disponibles")
        variables_group.setObjectName("variablesGroup")
        variables_group.setStyleSheet("""
            #variablesGroup {
                border: 1px solid #1f5c7a;
                background: #0b161f;
            }
            #variablesGroup::title {
                color: #56a6d7;
            }
        """)
        variables_layout = QVBoxLayout()
        variables_layout.setContentsMargins(10, 8, 10, 10)
        variables_layout.setSpacing(6)

        self.variables_label = QLabel(
            "💡 Subí un Excel desde Perfiles para ver las variables disponibles."
        )
        self.variables_label.setStyleSheet("color: #9fb3c8; font-style: italic; padding: 4px 0;")
        self.variables_label.setWordWrap(True)
        variables_layout.addWidget(self.variables_label)

        # Contenedor scrollable para variables
        variables_scroll = QScrollArea()
        variables_scroll.setWidgetResizable(True)
        variables_scroll.setMaximumHeight(80)
        variables_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        self.variables_widget = QWidget()
        self.variables_layout = QHBoxLayout(self.variables_widget)
        self.variables_layout.setAlignment(Qt.AlignLeft)
        self.variables_layout.setSpacing(4)
        self.variables_layout.setContentsMargins(2, 2, 2, 2)
        variables_scroll.setWidget(self.variables_widget)

        variables_layout.addWidget(variables_scroll)
        variables_group.setLayout(variables_layout)
        layout.addWidget(variables_group)

        # Sección de plantillas
        templates_group = QGroupBox("✍️ Mensaje de la Campaña")
        templates_group.setObjectName("templatesGroup")
        templates_group.setStyleSheet("""
            #templatesGroup {
                border: 1px solid #1f5c7a;
                background: #0f1820;
            }
            #templatesGroup::title {
                color: #56a6d7;
            }
        """)
        templates_layout = QVBoxLayout()

        # Selector de plantilla
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("📋 Plantilla:"))

        self.template_combo = QComboBox()
        self.template_combo.setMinimumHeight(32)
        self.template_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                font-size: 13px;
                border: 1px solid #2b3a48;
                border-radius: 8px;
                background: #0a121a;
                color: #e5e5e5;
            }
            QComboBox::drop-down { width: 22px; }
        """)
        self.template_combo.currentTextChanged.connect(self.load_template_content)
        selector_layout.addWidget(self.template_combo)

        templates_layout.addLayout(selector_layout)

        # Editor de plantilla
        templates_layout.addWidget(QLabel("✏️ Contenido (haz clic en las variables para insertarlas):"))

        self.template_editor = QTextEdit()
        self.template_editor.setMinimumHeight(140)
        self.template_editor.setPlaceholderText("Ejemplo: Hola {Nombre}, tu saldo es {$ Asig.}")
        self.template_editor.textChanged.connect(self.update_preview)
        templates_layout.addWidget(self.template_editor)

        # Vista previa del mensaje
        preview_group = QGroupBox("👀 Vista previa")
        preview_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: 600;
                border: 1px dashed #1f5c7a;
                border-radius: 10px;
                margin-top: 8px;
                padding-top: 10px;
                background: #0a121a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: #56a6d7;
            }
        """)
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(10, 6, 10, 10)
        self.preview_label = QLabel("Escribe el mensaje para ver la vista previa.")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet(
            "background: #0f1820; border: 1px solid #1f5c7a; border-radius: 10px;"
            "padding: 12px; color: #e5e5e5; font-size: 13px;"
        )
        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)
        templates_layout.addWidget(preview_group)

        # Botones de plantilla
        template_buttons = QHBoxLayout()

        self.save_template_btn = QPushButton("💾 Guardar plantilla")
        self.save_template_btn.setMinimumHeight(32)
        self.save_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #12354a;
                color: white;
                border: 2px solid #1f5c7a;
                border-radius: 10px;
                font-size: 12px;
                padding: 8px 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1d4f6d;
            }
        """)
        self.save_template_btn.clicked.connect(self.save_new_template)
        template_buttons.addWidget(self.save_template_btn)

        self.delete_template_btn = QPushButton("🗑️ Eliminar")
        self.delete_template_btn.setMinimumHeight(32)
        self.delete_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: 2px solid #3d566e;
                border-radius: 10px;
                font-size: 12px;
                padding: 8px 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        self.delete_template_btn.clicked.connect(self.delete_template)
        template_buttons.addWidget(self.delete_template_btn)

        templates_layout.addLayout(template_buttons)

        templates_group.setLayout(templates_layout)
        layout.addWidget(templates_group)

        # Configuración básica (reubicada debajo del mensaje)
        layout.addWidget(config_group)

        # Teléfonos disponibles desde el Excel
        layout.addWidget(numbers_group)

        # Perfiles activos - CON SELECCIÓN MÚLTIPLE
        profiles_group = QGroupBox("👥 Seleccionar Perfiles")
        profiles_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 700;
                border: 1px solid #2b3a48;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 16px;
                background: #0f1820;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 6px 8px;
            }
        """)
        profiles_layout = QVBoxLayout()

        profiles_info = QLabel("✓ Marca los perfiles que quieras usar para la campaña:")
        profiles_info.setStyleSheet("color: #9fb3c8; margin-bottom: 8px;")
        profiles_layout.addWidget(profiles_info)

        self.profile_checkboxes = []
        self.profiles_container = QWidget()
        self.profiles_container_layout = QVBoxLayout(self.profiles_container)
        self.profiles_container_layout.setSpacing(6)
        self.profiles_container_layout.setContentsMargins(4, 4, 4, 4)

        profiles_scroll = QScrollArea()
        profiles_scroll.setWidgetResizable(True)
        profiles_scroll.setMaximumHeight(150)
        profiles_scroll.setWidget(self.profiles_container)
        profiles_layout.addWidget(profiles_scroll)

        profiles_group.setLayout(profiles_layout)
        layout.addWidget(profiles_group)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        # Botón enviar ahora
        self.send_now_btn = QPushButton("🚀 ENVIAR AHORA")
        self.send_now_btn.setMinimumHeight(55)
        self.send_now_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
            }
        """)
        self.send_now_btn.clicked.connect(self.send_now)
        buttons_layout.addWidget(self.send_now_btn)

        # Botón pausar/reanudar
        self.pause_resume_btn = QPushButton("⏸️ Pausar")
        self.pause_resume_btn.setMinimumHeight(55)
        self.pause_resume_btn.setEnabled(False)
        self.pause_resume_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f1c40f, stop:1 #d4ac0d);
                font-size: 15px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f4d03f, stop:1 #f1c40f);
            }
        """)
        self.pause_resume_btn.clicked.connect(self.toggle_pause)
        buttons_layout.addWidget(self.pause_resume_btn)

        # Botón cancelar
        self.cancel_btn = QPushButton("🛑 Cancelar")
        self.cancel_btn.setMinimumHeight(55)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                font-size: 15px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:1 #e74c3c);
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_sending)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)

        # Recordatorio de progreso
        progress_note = QLabel(
            "📈 El progreso en vivo ahora se ve en la pestaña 'Estado de Envíos'."
        )
        progress_note.setStyleSheet("color: #9fb3c8; margin-top: 6px;")
        layout.addWidget(progress_note)

        layout.addStretch()
        main_scroll.setWidget(container)

    def load_available_columns(self, filename):
        """Carga las columnas disponibles del archivo seleccionado."""
        if not filename:
            self.variables_label.setText(
                "💡 Subí un Excel desde Perfiles para ver las variables disponibles."
            )
            # Limpiar botones de variables
            while self.variables_layout.count():
                child = self.variables_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.sample_contact = None
            self.update_preview()
            return

        self.load_phone_numbers(filename)

        # Cargar archivo procesado
        contacts = self.excel_processor.load_processed_file(filename)

        if not contacts or len(contacts) == 0:
            self.variables_label.setText("⚠️ No se pudieron cargar las columnas del archivo")
            return

        # Obtener columnas del primer registro
        self.available_columns = list(contacts[0].keys())
        self.sample_contact = contacts[0]

        self.variables_label.setText(f"✨ {len(self.available_columns)} variables disponibles - Haz clic para insertar:")

        # Limpiar botones anteriores
        while self.variables_layout.count():
            child = self.variables_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Crear botones para cada variable
        for column in self.available_columns:
            btn = QPushButton(f"{{{column}}}")
            btn.setStyleSheet("""
                QPushButton {
                    background: #12354a;
                    color: #e5e5e5;
                    padding: 4px 8px;
                    margin: 2px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 11px;
                    border: 1px solid #1f5c7a;
                }
                QPushButton:hover {
                    background: #1d4f6d;
                }
            """)
            btn.clicked.connect(lambda checked, col=column: self.insert_variable(col))
            self.variables_layout.addWidget(btn)

        self.update_preview()

    def insert_variable(self, column_name):
        """Inserta una variable en el editor de plantilla."""
        cursor = self.template_editor.textCursor()
        cursor.insertText(f"{{{column_name}}}")
        self.template_editor.setFocus()
        self.update_preview()

    def update_preview(self):
        """Actualiza la vista previa del mensaje."""
        content = self.template_editor.toPlainText()
        if not content:
            self.preview_label.setText("Escribe el mensaje para ver la vista previa.")
            return

        preview_content = escape(content)
        for column in self.available_columns:
            placeholder = escape(f"{{{column}}}")
            value = ""
            if self.sample_contact is not None:
                formatted = self.templates_manager.format_value(
                    column,
                    self.sample_contact.get(column, "")
                )
                value = escape(formatted)
            replacement = value or f"<span style='color:#27ae60;font-weight:700;'>{{{column}}}</span>"
            preview_content = preview_content.replace(placeholder, replacement)

        preview_content = preview_content.replace("\n", "<br>")
        self.preview_label.setText(preview_content)

    def get_selected_profiles(self):
        """Retorna los nombres de perfiles marcados."""
        return [cb.text() for cb in self.profile_checkboxes if cb.isChecked()]

    def toggle_all_numbers(self, state):
        """Marca o desmarca todos los teléfonos."""
        for checkbox in self.phone_checkboxes:
            checkbox.blockSignals(True)
            checkbox.setChecked(state == Qt.Checked)
            checkbox.blockSignals(False)

    def handle_number_checkbox(self):
        """Sincroniza el checkbox de "seleccionar todos"."""
        all_checked = all(cb.isChecked() for cb in self.phone_checkboxes) if self.phone_checkboxes else False
        self.select_all_numbers.blockSignals(True)
        self.select_all_numbers.setChecked(all_checked)
        self.select_all_numbers.blockSignals(False)

    def get_selected_numbers(self):
        """Retorna los teléfonos marcados para el envío."""
        return [cb.text() for cb in self.phone_checkboxes if cb.isChecked()]

    def sync_delay_bounds(self):
        """Asegura que el máximo nunca sea menor al mínimo."""
        self.delay_max_spin.setMinimum(self.delay_min_spin.value())

    def refresh_data(self):
        """Actualiza los datos de plantillas, contactos y perfiles."""
        # Plantillas
        self.template_combo.clear()
        templates = self.templates_manager.get_templates()
        for template in templates:
            self.template_combo.addItem(template['nombre'])

        # Contactos procesados - usar el último automáticamente
        self.update_contacts_source()

        # Perfiles - MOSTRAR TODOS (activos e inactivos)
        # Limpiar contenedor anterior
        for i in reversed(range(self.profiles_container_layout.count())):
            item = self.profiles_container_layout.takeAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self.profile_checkboxes.clear()

        all_profiles = self.profiles_manager.get_profiles()
        for profile in all_profiles:
            checkbox = QCheckBox(profile['nombre'])
            checkbox.setChecked(profile.get('activo', False))
            self.profile_checkboxes.append(checkbox)
            self.profiles_container_layout.addWidget(checkbox)

    def update_contacts_source(self):
        """Detecta y muestra el último archivo de contactos procesado."""
        latest_file = self.excel_processor.get_latest_processed_file()
        self.current_contacts_file = latest_file

        if latest_file:
            self.contacts_info_label.setText(
                f"Usando: <b>{latest_file}</b> (subido desde Perfiles)"
            )
            self.load_available_columns(latest_file)
        else:
            self.contacts_info_label.setText(
                "⚠️ No hay archivos procesados. Subí un Excel desde la pestaña Perfiles."
            )
            self.load_available_columns(None)

    def load_template_content(self, template_name):
        """Carga el contenido de una plantilla en el editor."""
        if not template_name:
            return

        template = self.templates_manager.get_template_by_name(template_name)
        if template:
            self.template_editor.setPlainText(template['contenido'])
            self.update_preview()

    def save_new_template(self):
        """Guarda el contenido actual como una nueva plantilla."""
        content = self.template_editor.toPlainText().strip()

        if not content:
            QMessageBox.warning(self, "Error", "El contenido de la plantilla está vacío")
            return

        # Pedir nombre
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self,
            "Nueva plantilla",
            "Nombre de la plantilla:"
        )

        if ok and name:
            success, message = self.templates_manager.add_template(name, content)

            if success:
                QMessageBox.information(self, "Éxito", message)
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Error", message)

    def delete_template(self):
        """Elimina la plantilla seleccionada."""
        template_name = self.template_combo.currentText()

        if not template_name:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar la plantilla '{template_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.templates_manager.delete_template(template_name):
                QMessageBox.information(self, "Éxito", "Plantilla eliminada")
                self.refresh_data()
            self.template_editor.clear()
        else:
            QMessageBox.warning(self, "Error", "No se pudo eliminar la plantilla")

    def load_phone_numbers(self, filename):
        """Carga los teléfonos disponibles del archivo procesado."""
        # Limpiar contenedor
        for i in reversed(range(self.numbers_container_layout.count())):
            item = self.numbers_container_layout.takeAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self.phone_checkboxes.clear()
        self.loaded_contacts = []

        if not filename:
            self.numbers_info_label.setText(
                "Cargá un Excel desde Perfiles para elegir los teléfonos a usar."
            )
            self.select_all_numbers.setChecked(False)
            self.select_all_numbers.setEnabled(False)
            return

        contacts = self.excel_processor.load_processed_file(filename) or []
        self.loaded_contacts = contacts

        phone_set = {
            str(contact.get('Telefono_1', '')).strip()
            for contact in contacts
            if str(contact.get('Telefono_1', '')).strip()
        }

        phone_list = sorted(phone_set)

        if not phone_list:
            self.numbers_info_label.setText(
                "No se detectaron teléfonos en el archivo cargado."
            )
            self.select_all_numbers.setChecked(False)
            self.select_all_numbers.setEnabled(False)
            return

        self.numbers_info_label.setText(
            f"Se encontraron {len(phone_list)} teléfonos. Marcá los que quieras usar (separados por '-' ya vienen desglosados)."
        )

        for phone in phone_list:
            cb = QCheckBox(phone)
            cb.setChecked(True)
            cb.stateChanged.connect(self.handle_number_checkbox)
            self.phone_checkboxes.append(cb)
            self.numbers_container_layout.addWidget(cb)

        self.select_all_numbers.setEnabled(True)
        self.select_all_numbers.setChecked(True)

    def send_now(self):
        """Inicia el envío inmediato de una campaña."""
        # Validar que haya una campaña lista
        campaign_name = self.campaign_name_input.text().strip()
        if not campaign_name:
            QMessageBox.warning(self, "Error", "Debe ingresar un nombre para la campaña")
            return

        template_content = self.template_editor.toPlainText().strip()
        if not template_content:
            QMessageBox.warning(self, "Error", "Debe seleccionar o crear una plantilla")
            return

        contacts_file = self.current_contacts_file
        if not contacts_file:
            QMessageBox.warning(
                self,
                "Error",
                "Debes cargar un Excel desde la pestaña Perfiles para usarlo en la campaña",
            )
            return

        selected_profiles = self.get_selected_profiles()
        if not selected_profiles:
            QMessageBox.warning(self, "Error", "Debe seleccionar al menos un perfil")
            return

        selected_numbers = self.get_selected_numbers()
        if not selected_numbers:
            QMessageBox.warning(self, "Error", "Debes elegir al menos un teléfono para enviar")
            return

        delay_min = self.delay_min_spin.value()
        delay_max = self.delay_max_spin.value()

        # Confirmar envío
        reply = QMessageBox.question(
            self,
            "Confirmar envío",
            f"¿Iniciar envío de campaña '{campaign_name}'?\n\n"
            f"• Perfiles: {len(selected_profiles)}\n"
            f"• Contactos: {contacts_file}\n"
            f"• Teléfonos seleccionados: {len(selected_numbers)}\n"
            f"• Delay: entre {delay_min} y {delay_max} segundos\n\n"
            "Se abrirán los navegadores automáticamente.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Crear campaña si no existe
        campaign_data = {
            'nombre': campaign_name,
            'template_name': self.template_combo.currentText() or 'Sin plantilla',
            'template_content': template_content,
            'profiles': selected_profiles,
            'contacts_file': contacts_file,
            'selected_numbers': selected_numbers,
            'delay_min': delay_min,
            'delay_max': delay_max
        }

        success, message = self.sending_engine.create_campaign(campaign_data)

        if not success:
            QMessageBox.critical(self, "Error", f"No se pudo crear la campaña: {message}")
            return

        # Extraer campaign_id del mensaje
        import re
        match = re.search(r'ID: (\d+_\d+)', message)
        if not match:
            QMessageBox.critical(self, "Error", "No se pudo obtener el ID de la campaña")
            return

        campaign_id = match.group(1)

        # Deshabilitar botones durante envío
        self.send_now_btn.setEnabled(False)
        self.send_now_btn.setText("⏳ Enviando...")

        if self.status_tab:
            self.status_tab.begin_live_campaign(campaign_id, campaign_name)
            if hasattr(self.window(), "tabs"):
                self.window().tabs.setCurrentWidget(self.status_tab)

        # Iniciar thread de envío
        self.sending_thread = SendingThread(campaign_id, self.sending_engine)
        self.sending_thread.progress.connect(self.update_progress)
        self.sending_thread.finished.connect(self.sending_finished)
        self.pause_resume_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.pause_resume_btn.setText("⏸️ Pausar")
        self.sending_thread.start()

    def toggle_pause(self):
        """Alterna entre pausar y reanudar el envío."""
        if not self.sending_thread:
            return

        if not self.pause_resume_btn.isEnabled():
            return

        if self.sending_thread.pause_event.is_set():
            self.sending_thread.resume()
            self.pause_resume_btn.setText("⏸️ Pausar")
            if self.status_tab:
                self.status_tab.append_progress("▶️ Reanudando campaña")
        else:
            self.sending_thread.pause()
            self.pause_resume_btn.setText("▶️ Reanudar")
            if self.status_tab:
                self.status_tab.append_progress("⏸️ Campaña en pausa")

    def cancel_sending(self):
        """Cancela el envío en curso."""
        if not self.sending_thread:
            return

        self.cancel_btn.setEnabled(False)
        self.pause_resume_btn.setEnabled(False)
        self.sending_thread.cancel()
        if self.status_tab:
            self.status_tab.append_progress("🛑 Cancelando campaña...")

    def update_progress(self, message):
        """Actualiza el log de progreso."""
        if self.status_tab:
            self.status_tab.append_progress(message)

    def sending_finished(self, success, message):
        """Callback cuando termina el envío."""
        self.send_now_btn.setEnabled(True)
        self.send_now_btn.setText("🚀 ENVIAR AHORA")
        self.pause_resume_btn.setEnabled(False)
        self.pause_resume_btn.setText("⏸️ Pausar")
        self.cancel_btn.setEnabled(False)
        self.sending_thread = None

        if self.status_tab:
            self.status_tab.finish_live_campaign(success, message)

        if success:
            QMessageBox.information(self, "Envío completado", message)
        else:
            QMessageBox.critical(self, "Error en envío", message)
