"""
Pestaña de gestión de campañas.
Permite crear campañas seleccionando plantillas, perfiles y contactos.
Diseño moderno y atractivo.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QComboBox, QTextEdit, QLineEdit,
                               QSpinBox, QMessageBox, QListWidget, QGroupBox,
                               QFormLayout, QCheckBox, QScrollArea)
from PySide6.QtCore import Qt, QThread, Signal
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
    
    def run(self):
        """Ejecuta el envío de la campaña."""
        try:
            success, message = self.sending_engine.start_campaign(self.campaign_id, self.progress)
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"Error en el envío: {str(e)}")


class CampaignsTab(QWidget):
    """Pestaña para crear y gestionar campañas de envío."""
    
    def __init__(self):
        super().__init__()
        self.templates_manager = TemplatesManager()
        self.profiles_manager = ProfilesManager()
        self.excel_processor = ExcelProcessor()
        self.sending_engine = SendingEngine()
        self.sending_thread = None
        self.available_columns = []
        
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título con estilo
        title = QLabel("🚀 Gestión de Campañas")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #3498db;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        subtitle = QLabel("Configura y envía tus campañas de SMS de forma automática")
        subtitle.setStyleSheet("color: #95a5a6; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Sección de configuración de campaña
        config_group = QGroupBox("⚙️ Configuración Básica")
        config_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #3498db;
            }
        """)
        config_layout = QFormLayout()
        config_layout.setSpacing(12)
        
        # Nombre de campaña
        self.campaign_name_input = QLineEdit()
        self.campaign_name_input.setPlaceholderText("Ej: Campaña Enero 2025")
        self.campaign_name_input.setMinimumHeight(40)
        config_layout.addRow("📝 Nombre:", self.campaign_name_input)
        
        # Archivo de contactos
        contacts_layout = QHBoxLayout()
        self.contacts_combo = QComboBox()
        self.contacts_combo.setMinimumHeight(40)
        self.contacts_combo.currentTextChanged.connect(self.load_available_columns)
        contacts_layout.addWidget(self.contacts_combo)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(50)
        refresh_btn.setMinimumHeight(40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #34495e;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #3498db;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        contacts_layout.addWidget(refresh_btn)
        
        config_layout.addRow("📊 Lista de contactos:", contacts_layout)
        
        # Delay entre mensajes
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(1)
        self.delay_spin.setMaximum(300)
        self.delay_spin.setValue(5)
        self.delay_spin.setSuffix(" segundos")
        self.delay_spin.setMinimumHeight(40)
        config_layout.addRow("⏱️ Delay entre mensajes:", self.delay_spin)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Sección de variables disponibles
        variables_group = QGroupBox("🏷️ Variables Disponibles")
        variables_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                border: 2px solid #9b59b6;
                border-radius: 10px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #9b59b6;
            }
        """)
        variables_layout = QVBoxLayout()
        
        self.variables_label = QLabel("💡 Selecciona un archivo de contactos para ver las variables")
        self.variables_label.setStyleSheet("color: #95a5a6; font-style: italic; padding: 8px;")
        self.variables_label.setWordWrap(True)
        variables_layout.addWidget(self.variables_label)
        
        # Contenedor scrollable para variables
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(100)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        self.variables_widget = QWidget()
        self.variables_layout = QHBoxLayout(self.variables_widget)
        self.variables_layout.setAlignment(Qt.AlignLeft)
        scroll.setWidget(self.variables_widget)
        
        variables_layout.addWidget(scroll)
        variables_group.setLayout(variables_layout)
        layout.addWidget(variables_group)
        
        # Sección de plantillas
        templates_group = QGroupBox("✍️ Mensaje de la Campaña")
        templates_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                border: 2px solid #27ae60;
                border-radius: 10px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #27ae60;
            }
        """)
        templates_layout = QVBoxLayout()
        
        # Selector de plantilla
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("📋 Plantilla:"))
        
        self.template_combo = QComboBox()
        self.template_combo.setMinimumHeight(40)
        self.template_combo.currentTextChanged.connect(self.load_template_content)
        selector_layout.addWidget(self.template_combo)
        
        templates_layout.addLayout(selector_layout)
        
        # Editor de plantilla
        templates_layout.addWidget(QLabel("✏️ Contenido (haz clic en las variables para insertarlas):"))
        
        self.template_editor = QTextEdit()
        self.template_editor.setMinimumHeight(140)
        self.template_editor.setPlaceholderText("Ejemplo: Hola {Nombre}, tu saldo es {$ Asig.}")
        self.template_editor.setStyleSheet("""
            QTextEdit {
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        templates_layout.addWidget(self.template_editor)
        
        # Botones de plantilla
        template_buttons = QHBoxLayout()
        
        self.save_template_btn = QPushButton("💾 Guardar como nueva plantilla")
        self.save_template_btn.setMinimumHeight(40)
        self.save_template_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
            }
        """)
        self.save_template_btn.clicked.connect(self.save_new_template)
        template_buttons.addWidget(self.save_template_btn)
        
        self.delete_template_btn = QPushButton("🗑️ Eliminar plantilla")
        self.delete_template_btn.setMinimumHeight(40)
        self.delete_template_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:1 #e74c3c);
            }
        """)
        self.delete_template_btn.clicked.connect(self.delete_template)
        template_buttons.addWidget(self.delete_template_btn)
        
        templates_layout.addLayout(template_buttons)
        
        templates_group.setLayout(templates_layout)
        layout.addWidget(templates_group)
        
        # Perfiles activos - CON SELECCIÓN MÚLTIPLE
        profiles_group = QGroupBox("👥 Seleccionar Perfiles")
        profiles_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                border: 2px solid #e67e22;
                border-radius: 10px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #e67e22;
            }
        """)
        profiles_layout = QVBoxLayout()
        
        profiles_info = QLabel("✓ Selecciona uno o más perfiles (Ctrl+Click para múltiples):")
        profiles_info.setStyleSheet("color: #95a5a6; margin-bottom: 8px;")
        profiles_layout.addWidget(profiles_info)
        
        self.profiles_list = QListWidget()
        self.profiles_list.setSelectionMode(QListWidget.MultiSelection)
        self.profiles_list.setMinimumHeight(120)
        profiles_layout.addWidget(self.profiles_list)
        
        profiles_group.setLayout(profiles_layout)
        layout.addWidget(profiles_group)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Botón crear campaña
        create_campaign_btn = QPushButton("💾 Crear Campaña")
        create_campaign_btn.setMinimumHeight(55)
        create_campaign_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }
        """)
        create_campaign_btn.clicked.connect(self.create_campaign)
        buttons_layout.addWidget(create_campaign_btn)
        
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
        
        layout.addLayout(buttons_layout)
        
        # Log de progreso
        log_label = QLabel("📋 Progreso de Envío:")
        log_label.setStyleSheet("font-weight: 600; font-size: 14px; margin-top: 10px;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(180)
        self.log_text.setPlaceholderText("Los mensajes de progreso aparecerán aquí...")
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
    
    def load_available_columns(self, filename):
        """Carga las columnas disponibles del archivo seleccionado."""
        if not filename:
            self.variables_label.setText("💡 Selecciona un archivo de contactos para ver las variables")
            # Limpiar botones de variables
            while self.variables_layout.count():
                child = self.variables_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            return
        
        # Cargar archivo procesado
        contacts = self.excel_processor.load_processed_file(filename)
        
        if not contacts or len(contacts) == 0:
            self.variables_label.setText("⚠️ No se pudieron cargar las columnas del archivo")
            return
        
        # Obtener columnas del primer registro
        self.available_columns = list(contacts[0].keys())
        
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
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #9b59b6, stop:1 #8e44ad);
                    color: white;
                    padding: 8px 14px;
                    margin: 3px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #af7ac5, stop:1 #9b59b6);
                }
            """)
            btn.clicked.connect(lambda checked, col=column: self.insert_variable(col))
            self.variables_layout.addWidget(btn)
    
    def insert_variable(self, column_name):
        """Inserta una variable en el editor de plantilla."""
        cursor = self.template_editor.textCursor()
        cursor.insertText(f"{{{column_name}}}")
        self.template_editor.setFocus()
    
    def refresh_data(self):
        """Actualiza los datos de plantillas, contactos y perfiles."""
        # Plantillas
        self.template_combo.clear()
        templates = self.templates_manager.get_templates()
        for template in templates:
            self.template_combo.addItem(template['nombre'])
        
        # Contactos procesados
        current_file = self.contacts_combo.currentText()
        self.contacts_combo.clear()
        processed_files = self.excel_processor.get_processed_files()
        self.contacts_combo.addItems(processed_files)
        
        # Restaurar selección si existe
        if current_file and current_file in processed_files:
            self.contacts_combo.setCurrentText(current_file)
        
        # Perfiles - MOSTRAR TODOS (activos e inactivos)
        self.profiles_list.clear()
        all_profiles = self.profiles_manager.get_profiles()
        for profile in all_profiles:
            self.profiles_list.addItem(profile['nombre'])
            # Pre-seleccionar los activos
            if profile.get('activo', False):
                items = self.profiles_list.findItems(profile['nombre'], Qt.MatchExactly)
                if items:
                    items[0].setSelected(True)
    
    def load_template_content(self, template_name):
        """Carga el contenido de una plantilla en el editor."""
        if not template_name:
            return
        
        template = self.templates_manager.get_template_by_name(template_name)
        if template:
            self.template_editor.setPlainText(template['contenido'])
    
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
    
    def create_campaign(self):
        """Crea una nueva campaña."""
        # Validaciones
        campaign_name = self.campaign_name_input.text().strip()
        if not campaign_name:
            QMessageBox.warning(self, "Error", "Debe ingresar un nombre para la campaña")
            return
        
        template_content = self.template_editor.toPlainText().strip()
        if not template_content:
            QMessageBox.warning(self, "Error", "Debe seleccionar o crear una plantilla")
            return
        
        contacts_file = self.contacts_combo.currentText()
        if not contacts_file:
            QMessageBox.warning(self, "Error", "Debe seleccionar una lista de contactos")
            return
        
        # Obtener perfiles seleccionados
        selected_profiles = [item.text() for item in self.profiles_list.selectedItems()]
        if not selected_profiles:
            QMessageBox.warning(self, "Error", "Debe seleccionar al menos un perfil")
            return
        
        # Crear campaña
        campaign_data = {
            'nombre': campaign_name,
            'template_name': self.template_combo.currentText(),
            'template_content': template_content,
            'profiles': selected_profiles,
            'contacts_file': contacts_file,
            'delay': self.delay_spin.value()
        }
        
        success, message = self.sending_engine.create_campaign(campaign_data)
        
        if success:
            QMessageBox.information(
                self,
                "Éxito",
                f"{message}\n\nPuedes hacer clic en 'ENVIAR AHORA' para iniciar el envío."
            )
            self.log_text.append(f"✅ Campaña '{campaign_name}' creada exitosamente")
        else:
            QMessageBox.critical(self, "Error", message)
    
    def send_now(self):
        """Inicia el envío inmediato de una campaña."""
        # Validar que haya una campaña lista
        campaign_name = self.campaign_name_input.text().strip()
        template_content = self.template_editor.toPlainText().strip()
        contacts_file = self.contacts_combo.currentText()
        selected_profiles = [item.text() for item in self.profiles_list.selectedItems()]
        
        if not all([campaign_name, template_content, contacts_file, selected_profiles]):
            QMessageBox.warning(
                self,
                "Campaña incompleta",
                "Primero debes configurar todos los campos y crear la campaña"
            )
            return
        
        # Confirmar envío
        reply = QMessageBox.question(
            self,
            "Confirmar envío",
            f"¿Iniciar envío de campaña '{campaign_name}'?\n\n"
            f"• Perfiles: {len(selected_profiles)}\n"
            f"• Contactos: {contacts_file}\n"
            f"• Delay: {self.delay_spin.value()} segundos\n\n"
            "Se abrirán los navegadores automáticamente.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Crear campaña si no existe
        campaign_data = {
            'nombre': campaign_name,
            'template_name': self.template_combo.currentText() or "Sin plantilla",
            'template_content': template_content,
            'profiles': selected_profiles,
            'contacts_file': contacts_file,
            'delay': self.delay_spin.value()
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
        
        self.log_text.clear()
        self.log_text.append(f"🚀 Iniciando envío de campaña: {campaign_name}")
        self.log_text.append(f"📋 ID: {campaign_id}")
        self.log_text.append("-" * 50)
        
        # Iniciar thread de envío
        self.sending_thread = SendingThread(campaign_id, self.sending_engine)
        self.sending_thread.progress.connect(self.update_progress)
        self.sending_thread.finished.connect(self.sending_finished)
        self.sending_thread.start()
    
    def update_progress(self, message):
        """Actualiza el log de progreso."""
        self.log_text.append(message)
        # Auto-scroll al final
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def sending_finished(self, success, message):
        """Callback cuando termina el envío."""
        self.send_now_btn.setEnabled(True)
        self.send_now_btn.setText("🚀 ENVIAR AHORA")
        
        if success:
            self.log_text.append("-" * 50)
            self.log_text.append(f"✅ {message}")
            QMessageBox.information(self, "Envío completado", message)
        else:
            self.log_text.append("-" * 50)
            self.log_text.append(f"❌ {message}")
            QMessageBox.critical(self, "Error en envío", message)
