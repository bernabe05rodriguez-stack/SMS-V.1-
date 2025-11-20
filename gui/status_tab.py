"""
Pestaña de estado de envíos.
Muestra el estado de las campañas y mensajes enviados.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QScrollArea,
                               QSizePolicy, QTextEdit, QGroupBox)
from PySide6.QtCore import Qt
from core.sending_engine import SendingEngine


class StatusTab(QWidget):
    """Pestaña para visualizar el estado de envíos."""
    
    def __init__(self):
        super().__init__()
        self.sending_engine = SendingEngine()
        self.live_campaign_id = None
        self.init_ui()
        self.load_campaigns()
    
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
        title = QLabel("Estado de Envíos")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Botón refrescar
        refresh_btn = QPushButton("Refrescar")
        refresh_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        refresh_btn.setMaximumWidth(150)
        refresh_btn.clicked.connect(self.load_campaigns)
        layout.addWidget(refresh_btn)

        # Progreso en vivo
        live_group = QGroupBox("Progreso en vivo")
        live_layout = QVBoxLayout()

        self.live_status_label = QLabel("Aún no hay envíos activos.")
        self.live_status_label.setStyleSheet("color: #95a5a6;")
        live_layout.addWidget(self.live_status_label)

        self.live_log = QTextEdit()
        self.live_log.setReadOnly(True)
        self.live_log.setMinimumHeight(160)
        self.live_log.setPlaceholderText(
            "Los mensajes de progreso aparecerán aquí cuando inicies un envío."
        )
        live_layout.addWidget(self.live_log)

        live_group.setLayout(live_layout)
        layout.addWidget(live_group)

        # Tabla de campañas
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Nombre",
            "Plantilla",
            "Total",
            "Enviados",
            "Fallidos",
            "Estado"
        ])
        
        # Configurar columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.table.setMinimumHeight(400)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.table)
        
        # Información
        info_label = QLabel(
            "💡 Esta tabla mostrará el progreso de las campañas cuando se implemente el envío automático.\n"
            "Por ahora muestra las campañas creadas con estado 'created'."
        )
        info_label.setStyleSheet("color: #888; margin: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        scroll.setWidget(container)
    
    def load_campaigns(self):
        """Carga las campañas en la tabla."""
        campaigns = self.sending_engine.get_campaigns()
        self.table.setRowCount(len(campaigns))
        
        for row, campaign in enumerate(campaigns):
            # ID
            id_item = QTableWidgetItem(campaign.get('id', ''))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, id_item)
            
            # Nombre
            name_item = QTableWidgetItem(campaign.get('nombre', ''))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, name_item)
            
            # Plantilla
            template_item = QTableWidgetItem(campaign.get('template_name', ''))
            template_item.setFlags(template_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, template_item)
            
            # Total
            total_item = QTableWidgetItem(str(campaign.get('total_messages', 0)))
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            total_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, total_item)
            
            # Enviados
            sent_item = QTableWidgetItem(str(campaign.get('sent_messages', 0)))
            sent_item.setFlags(sent_item.flags() & ~Qt.ItemIsEditable)
            sent_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, sent_item)
            
            # Fallidos
            failed_item = QTableWidgetItem(str(campaign.get('failed_messages', 0)))
            failed_item.setFlags(failed_item.flags() & ~Qt.ItemIsEditable)
            failed_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, failed_item)
            
            # Estado
            status = campaign.get('status', 'unknown')
            status_text = {
                'created': 'Creada',
                'running': 'En progreso',
                'paused': 'Pausada',
                'cancelled': 'Cancelada',
                'completed': 'Completada',
                'failed': 'Fallida'
            }.get(status, status)
            
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, status_item)

    def begin_live_campaign(self, campaign_id, campaign_name):
        """Prepara la vista de progreso para un envío en curso."""
        self.live_campaign_id = campaign_id
        self.live_status_label.setText(
            f"Enviando campaña: {campaign_name} (ID: {campaign_id})"
        )
        self.live_log.clear()
        self.live_log.append("🚀 Iniciando envío de la campaña")
        self.live_log.append("-" * 40)

    def append_progress(self, message):
        """Agrega una línea de progreso al panel en vivo."""
        self.live_log.append(message)
        self.live_log.verticalScrollBar().setValue(
            self.live_log.verticalScrollBar().maximum()
        )

    def finish_live_campaign(self, success, message):
        """Muestra el resultado final de un envío."""
        self.live_log.append("-" * 40)
        final_icon = "✅" if success else "❌"
        self.live_log.append(f"{final_icon} {message}")
        status_text = "Completada" if success else "Fallida"
        self.live_status_label.setText(
            f"Último envío finalizado ({status_text}) - ID: {self.live_campaign_id}"
        )
