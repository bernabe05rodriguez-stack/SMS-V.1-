"""
SMS Multi-Perfil Local
Aplicación de escritorio para gestión de perfiles, procesamiento de Excel
y preparación de campañas de SMS masivos.
"""

import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Punto de entrada principal de la aplicación."""
    app = QApplication(sys.argv)
    
    # Configurar estilo oscuro
    app.setStyle("Fusion")
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
