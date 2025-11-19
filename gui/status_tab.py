"""
Pestaña de estado de envíos.
Muestra el estado de las campañas y mensajes enviados.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from core.sending_engine import SendingEngine


class StatusTab(QWidget):
    """Pestaña para visualizar el estado de envíos."""
    
    def __init__(self):
        super().__init__()
        self.sending_engine = SendingEngine()
        self.init_ui()
        self.load_campaigns()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Estado de Envíos")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Botón refrescar
        refresh_btn = QPushButton("Refrescar")
        refresh_btn.setMaximumWidth(150)
        refresh_btn.clicked.connect(self.load_campaigns)
        layout.addWidget(refresh_btn)
        
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
        layout.addWidget(self.table)
        
        # Información
        info_label = QLabel(
            "💡 Esta tabla mostrará el progreso de las campañas cuando se implemente el envío automático.\n"
            "Por ahora muestra las campañas creadas con estado 'created'."
        )
        info_label.setStyleSheet("color: #888; margin: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self.setLayout(layout)
    
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
                'completed': 'Completada',
                'failed': 'Fallida'
            }.get(status, status)
            
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, status_item)
