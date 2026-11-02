"""Запускає графічний інтерфейс генератора контрактів."""

from gui.main_window import ContractApp

if __name__ == "__main__":
    app = ContractApp()
    app.mainloop()