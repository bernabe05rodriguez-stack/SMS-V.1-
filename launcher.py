"""Pequeño lanzador con botón EJECUTAR para abrir la app principal."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox


class LauncherApp:
    """Ventana simple con un botón para ejecutar la aplicación principal."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("SMS Multi-Perfil | Lanzador")
        self.root.geometry("420x200")
        self.root.resizable(False, False)

        self.root.configure(bg="#101522")

        title = tk.Label(
            self.root,
            text="SMS Multi-Perfil Pro",
            font=("Segoe UI", 18, "bold"),
            fg="#61dafb",
            bg="#101522",
        )
        title.pack(pady=(25, 5))

        subtitle = tk.Label(
            self.root,
            text="Haz clic en EJECUTAR para abrir la aplicación",
            font=("Segoe UI", 11),
            fg="#d7dae0",
            bg="#101522",
        )
        subtitle.pack()

        self.run_button = tk.Button(
            self.root,
            text="⚡ EJECUTAR",
            font=("Segoe UI", 14, "bold"),
            fg="#ffffff",
            bg="#2ecc71",
            activebackground="#27ae60",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=self.launch_main_app,
        )
        self.run_button.pack(pady=25)

        footer = tk.Label(
            self.root,
            text="Asegúrate de haber instalado las dependencias",
            font=("Segoe UI", 9),
            fg="#8b8fa1",
            bg="#101522",
        )
        footer.pack(side=tk.BOTTOM, pady=10)

    def launch_main_app(self) -> None:
        """Ejecuta el archivo main.py en un proceso aparte."""

        def _start_main():
            script_path = os.path.join(os.path.dirname(__file__), "main.py")
            if not os.path.exists(script_path):
                raise FileNotFoundError("No se encontró main.py")

            subprocess.Popen([sys.executable, script_path])

        def _on_error(error: Exception) -> None:
            messagebox.showerror(
                "No se pudo ejecutar",
                "Ocurrió un error al intentar abrir la aplicación.\n"
                f"Detalle: {error}",
            )
            self.run_button.config(state=tk.NORMAL, text="⚡ EJECUTAR")

        self.run_button.config(state=tk.DISABLED, text="Abriendo...")

        def _worker():
            try:
                _start_main()
                # Cerrar el lanzador unos instantes después de abrir la app principal
                self.root.after(500, self.root.destroy)
            except Exception as exc:  # pragma: no cover - solo en tiempo de ejecución
                self.root.after(0, _on_error, exc)

        threading.Thread(target=_worker, daemon=True).start()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    LauncherApp().run()


if __name__ == "__main__":
    main()
