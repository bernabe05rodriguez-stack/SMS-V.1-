"""
Pestaña de procesamiento de Excel y gestión de contactos.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QListWidget, QMessageBox, QTextEdit,
                               QFileDialog, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt
from core.excel_processor import ExcelProcessor
import shutil
import os


class ExcelTab(QWidget):
    """Pestaña para procesar archivos Excel/CSV."""
    
    def __init__(self):
        super().__init__()
        self.processor = ExcelProcessor()
        self.init_ui()
        self.refresh_files()
    
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
        title = QLabel("Procesamiento de Excel / Contactos")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Botón para subir archivo
        upload_btn = QPushButton("Subir archivo Excel/CSV")
        upload_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        upload_btn.setMinimumHeight(40)
        upload_btn.clicked.connect(self.upload_file)
        layout.addWidget(upload_btn)
        
        # Sección de archivos subidos
        layout.addWidget(QLabel("Archivos subidos:"))
        
        self.uploaded_list = QListWidget()
        self.uploaded_list.setMinimumHeight(150)
        self.uploaded_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.uploaded_list)
        
        # Botón procesar
        process_btn = QPushButton("Procesar archivo seleccionado")
        process_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        process_btn.setMinimumHeight(40)
        process_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        process_btn.clicked.connect(self.process_selected_file)
        layout.addWidget(process_btn)
        
        # Sección de archivos procesados
        layout.addWidget(QLabel("Archivos procesados:"))
        
        self.processed_list = QListWidget()
        self.processed_list.setMinimumHeight(150)
        self.processed_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.processed_list)
        
        # Información de procesamiento
        layout.addWidget(QLabel("Reglas de procesamiento:"))
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(150)
        self.info_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.info_text.setPlainText(
            "📋 Reglas aplicadas al procesar:\n\n"
            "• Se usa la columna Telefono_1 por defecto\n"
            "• Si un teléfono contiene guión (ej: 1167206128-1156925321), se separa y duplica la fila\n"
            "• Las columnas $ Hist. y $ Asig. se convierten a números\n"
            "• Los registros se ordenan por $ Asig. de mayor a menor\n"
            "• El resultado se guarda como JSON en data/processed/\n"
        )
        layout.addWidget(self.info_text)

        layout.addStretch()
        scroll.setWidget(container)
    
    def upload_file(self):
        """Permite al usuario subir un archivo Excel/CSV."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo Excel/CSV",
            "",
            "Archivos Excel/CSV (*.xlsx *.xls *.csv)"
        )
        
        if file_path:
            try:
                # Copiar archivo a directorio de uploads
                filename = os.path.basename(file_path)
                dest_path = os.path.join(self.processor.uploads_dir, filename)
                
                shutil.copy2(file_path, dest_path)
                
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Archivo '{filename}' subido correctamente"
                )
                
                self.refresh_files()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo subir el archivo:\n{str(e)}"
                )
    
    def process_selected_file(self):
        """Procesa el archivo seleccionado."""
        selected_items = self.uploaded_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(
                self,
                "Advertencia",
                "Debe seleccionar un archivo para procesar"
            )
            return
        
        filename = selected_items[0].text()
        
        # Procesar archivo
        success, message, count = self.processor.process_file(filename)
        
        if success:
            QMessageBox.information(
                self,
                "Éxito",
                f"{message}\n\nRegistros procesados: {count}"
            )
            self.refresh_files()
        else:
            QMessageBox.critical(
                self,
                "Error",
                message
            )
    
    def refresh_files(self):
        """Actualiza las listas de archivos."""
        # Archivos subidos
        self.uploaded_list.clear()
        uploaded_files = self.processor.get_uploaded_files()
        self.uploaded_list.addItems(uploaded_files)
        
        # Archivos procesados
        self.processed_list.clear()
        processed_files = self.processor.get_processed_files()
        self.processed_list.addItems(processed_files)
