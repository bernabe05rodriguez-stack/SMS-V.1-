"""
Ventana principal de la aplicación con pestañas.
Diseño moderno y atractivo.
"""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt
from gui.profiles_tab import ProfilesTab
from gui.campaigns_tab import CampaignsTab
from gui.status_tab import StatusTab


class MainWindow(QMainWindow):
    """Ventana principal con pestañas para diferentes funcionalidades."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMS Multi-Perfil Pro 💬")
        self.setGeometry(100, 100, 1200, 800)
        
        # Aplicar tema moderno
        self.apply_modern_theme()
        
        # Crear widget de pestañas
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)
        self.setCentralWidget(self.tabs)
        
        # Estilo personalizado para las pestañas
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2c3e50;
                background: #1e1e1e;
                border-radius: 8px;
            }
            
            QTabBar::tab {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                font-weight: 600;
            }
            
            QTabBar::tab:hover:!selected {
                background: #34495e;
            }
        """)
        
        # Crear e inicializar pestañas
        self.status_tab = StatusTab()
        self.profiles_tab = ProfilesTab()
        self.campaigns_tab = CampaignsTab(status_tab=self.status_tab)

        # Agregar pestañas al widget con iconos
        self.tabs.addTab(self.profiles_tab, "👤 Perfiles")
        self.tabs.addTab(self.campaigns_tab, "🚀 Campañas")
        self.tabs.addTab(self.status_tab, "📈 Estado de Envíos")

        # Refrescar datos dinámicos al cambiar de pestaña
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        """Realiza acciones adicionales según la pestaña seleccionada."""
        current_tab = self.tabs.widget(index)

        if current_tab is self.campaigns_tab:
            # Sincronizar plantillas, contactos y perfiles al abrir la pestaña
            self.campaigns_tab.refresh_data()
    
    def apply_modern_theme(self):
        """Aplica un tema moderno y atractivo a la aplicación."""
        # Paleta de colores moderna
        palette = QPalette()
        
        # Colores base - Tema oscuro moderno
        dark_bg = QColor(30, 30, 30)          # #1e1e1e
        darker_bg = QColor(25, 25, 25)        # #191919
        accent = QColor(52, 152, 219)         # #3498db (azul moderno)
        accent_hover = QColor(41, 128, 185)   # #2980b9
        text = QColor(236, 240, 241)          # #ecf0f1 (blanco suave)
        text_secondary = QColor(149, 165, 166) # #95a5a6 (gris claro)
        
        palette.setColor(QPalette.Window, dark_bg)
        palette.setColor(QPalette.WindowText, text)
        palette.setColor(QPalette.Base, darker_bg)
        palette.setColor(QPalette.AlternateBase, dark_bg)
        palette.setColor(QPalette.ToolTipBase, darker_bg)
        palette.setColor(QPalette.ToolTipText, text)
        palette.setColor(QPalette.Text, text)
        palette.setColor(QPalette.Button, QColor(44, 62, 80))  # #2c3e50
        palette.setColor(QPalette.ButtonText, text)
        palette.setColor(QPalette.BrightText, Qt.white)
        palette.setColor(QPalette.Link, accent)
        palette.setColor(QPalette.Highlight, accent)
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        self.setPalette(palette)
        
        # Estilo global moderno
        self.setStyleSheet("""
            QMainWindow {
                background: #1e1e1e;
            }
            
            QWidget {
                font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }
            
            QPushButton:pressed {
                background: #2471a3;
            }
            
            QPushButton:disabled {
                background: #34495e;
                color: #7f8c8d;
            }
            
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 6px;
                padding: 8px;
                selection-background-color: #3498db;
            }
            
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 2px solid #3498db;
            }
            
            QLabel {
                color: #ecf0f1;
            }
            
            QGroupBox {
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: 600;
                font-size: 14px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
            
            QTableWidget {
                background: #2c3e50;
                alternate-background-color: #34495e;
                color: #ecf0f1;
                gridline-color: #34495e;
                border: 1px solid #34495e;
                border-radius: 6px;
            }
            
            QTableWidget::item {
                padding: 8px;
            }
            
            QTableWidget::item:selected {
                background: #3498db;
                color: white;
            }
            
            QHeaderView::section {
                background: #34495e;
                color: #ecf0f1;
                padding: 10px;
                border: none;
                font-weight: 600;
            }
            
            QListWidget {
                background: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 6px;
                padding: 4px;
            }
            
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            
            QListWidget::item:selected {
                background: #3498db;
                color: white;
            }
            
            QListWidget::item:hover {
                background: #34495e;
            }
            
            QScrollBar:vertical {
                background: #2c3e50;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background: #34495e;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #3498db;
            }
            
            QScrollBar:horizontal {
                background: #2c3e50;
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background: #34495e;
                border-radius: 6px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: #3498db;
            }
            
            QCheckBox {
                color: #ecf0f1;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #34495e;
                border-radius: 4px;
                background: #2c3e50;
            }
            
            QCheckBox::indicator:checked {
                background: #3498db;
                border-color: #3498db;
            }
            
            QCheckBox::indicator:hover {
                border-color: #3498db;
            }
        """)
