"""Punto de entrada de la aplicación MuniCertificados."""

from __future__ import annotations

from src.database.connection import init_db
from src.ui.app_window import AppWindow


def main() -> None:
    """Inicializa la base de datos local y lanza la interfaz gráfica."""
    init_db()
    app = AppWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
