"""Допоміжні функції для створення та керування компонентами інтерфейсу."""
import customtkinter as ctk
from gui.ui_config import (
    Colors, FontSize, Spacing, 
    ENTRY_STYLE, COMBOBOX_STYLE, create_font
)


class UIHelpers:
    """Набір допоміжних методів для створення компонентів інтерфейсу."""
    
    @staticmethod
    def create_card_frame(parent, **kwargs) -> ctk.CTkFrame:
        """Створює картку з рамкою, заокругленими кутами та заданими параметрами."""
        default_kwargs = {
            "fg_color": Colors.CARD_BG,
            "border_width": 1,
            "border_color": Colors.CARD_BORDER,
            "corner_radius": 8,
        }
        default_kwargs.update(kwargs)
        return ctk.CTkFrame(parent, **default_kwargs)
    
    @staticmethod
    def create_header_label(parent, text: str, **kwargs) -> ctk.CTkLabel:
        """Створює заголовок зі стандартним оформленням і додатковими параметрами."""
        default_kwargs = {
            "text": text,
            "font": create_font(FontSize.HEADER, "bold"),
        }
        default_kwargs.update(kwargs)
        return ctk.CTkLabel(parent, **default_kwargs)
    
    @staticmethod
    def create_label_entry_pair(parent, label_text: str, row: int, 
                                placeholder: str = "", disabled: bool = False, 
                                colspan: int = 1) -> tuple:
        """Розміщує підпис і поле введення в заданому рядку сітки."""
        label = ctk.CTkLabel(
            parent,
            text=label_text,
            font=create_font(FontSize.NORMAL, "bold")
        )
        label.grid(row=row, column=0, sticky="e", padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM)
        
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            **ENTRY_STYLE
        )
        if disabled:
            entry.configure(state="disabled")
        
        entry.grid(row=row, column=1, columnspan=colspan, sticky="ew", 
                   padx=(0, Spacing.MD), pady=Spacing.SM)
        
        return label, entry
    
    @staticmethod
    def create_section_header(parent, text: str, row: int = None) -> ctk.CTkLabel:
        """Створює заголовок секції та розміщує його у сітці або пакуванні."""
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=create_font(FontSize.HEADER, "bold")
        )
        
        if row is not None:
            label.grid(row=row, column=0, sticky="w", padx=Spacing.SM, pady=(Spacing.MD, Spacing.XS))
        else:
            label.pack(anchor="w", padx=Spacing.SM, pady=(Spacing.MD, Spacing.XS))
        
        return label
    
    @staticmethod
    def create_combobox(parent, values: list, **kwargs) -> ctk.CTkComboBox:
        """Створює список із заданими значеннями та стандартним оформленням."""
        default_kwargs = {
            "values": values,
            **COMBOBOX_STYLE
        }
        default_kwargs.update(kwargs)
        return ctk.CTkComboBox(parent, **default_kwargs)
    
    @staticmethod
    def create_button(parent, text: str, style: str = "primary", **kwargs) -> ctk.CTkButton:
        """Створює кнопку з одним із наперед визначених наборів кольорів."""
        from gui.ui_config import (
            BUTTON_STYLE_PRIMARY, BUTTON_STYLE_SUCCESS,
            BUTTON_STYLE_DANGER, BUTTON_STYLE_SECONDARY,
            BUTTON_STYLE_NEUTRAL
        )
        
        styles = {
            "primary": BUTTON_STYLE_PRIMARY,
            "success": BUTTON_STYLE_SUCCESS,
            "danger": BUTTON_STYLE_DANGER,
            "secondary": BUTTON_STYLE_SECONDARY,
            "neutral": BUTTON_STYLE_NEUTRAL,
        }
        
        base_style = styles.get(style, BUTTON_STYLE_PRIMARY)
        default_kwargs = {
            "text": text,
            **base_style
        }
        default_kwargs.update(kwargs)
        return ctk.CTkButton(parent, **default_kwargs)
    
    @staticmethod
    def create_button_row(parent, buttons_config: list) -> ctk.CTkFrame:
        """Створює ряд кнопок на основі їхніх параметрів і відступів."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        for config in buttons_config:
            text = config.get("text", "Button")
            command = config.get("command")
            style = config.get("style", "primary")
            side = config.get("pack_side", "left")
            padx = config.get("padx", (Spacing.SM, 0) if side == "right" else (Spacing.SM, 0))
            
            btn = UIHelpers.create_button(parent, text, style, command=command)
            btn.pack(side=side, padx=padx)
        
        return frame
    
    @staticmethod
    def clear_frame(frame: ctk.CTkFrame):
        """Видаляє всі дочірні віджети з переданого фрейму."""
        for widget in frame.winfo_children():
            widget.destroy()


class EditableEntry:
    """Керує перемиканням поля введення між режимами перегляду та редагування."""
    
    def __init__(self, entry: ctk.CTkEntry, edit_button: ctk.CTkButton,
                 default_fg_color=None, default_hover_color=None):
        """Зберігає поле, кнопку перемикання та початкові кольори кнопки."""
        self.entry = entry
        self.button = edit_button
        self.default_fg = default_fg_color or "#1f538d"
        self.default_hover = default_hover_color or "#16396b"
        self.is_editing = False
    
    def toggle_edit(self):
        """Перемикає поле між режимами редагування та лише читання."""
        if self.is_editing:
            self.disable_edit()
        else:
            self.enable_edit()
    
    def enable_edit(self):
        """Вмикає редагування поля та змінює вигляд кнопки."""
        self.is_editing = True
        self.entry.configure(state="normal")
        self.button.configure(
            text="ЗБЕРЕГТИ ЗМІНИ",
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.entry.focus()
    
    def disable_edit(self):
        """Вимикає редагування поля та відновлює вигляд кнопки."""
        self.is_editing = False
        self.entry.configure(state="disabled")
        self.button.configure(
            text="РЕДАГУВАТИ",
            fg_color=self.default_fg,
            hover_color=self.default_hover
        )
    
    def get_value(self) -> str:
        """Повертає поточне значення поля."""
        return self.entry.get().strip()
    
    def set_value(self, value: str):
        """Замінює вміст поля переданим значенням."""
        was_disabled = self.entry.cget("state") == "disabled"
        self.entry.configure(state="normal")
        self.entry.delete(0, "end")
        self.entry.insert(0, value or "")
        if was_disabled:
            self.entry.configure(state="disabled")


class ConfirmDialog:
    """Створює діалогові вікна підтвердження дій."""
    
    @staticmethod
    def confirm_save(title: str = "Підтвердження збереження") -> bool:
        """Запитує підтвердження збереження та повертає відповідь користувача."""
        from tkinter import messagebox
        return messagebox.askyesno(
            title=title,
            message="Ви дійсно бажаєте зберегти внесені зміни?"
        )
    
    @staticmethod
    def confirm_delete(item_name: str = "елемент") -> bool:
        """Запитує підтвердження видалення елемента та повертає відповідь."""
        from tkinter import messagebox
        return messagebox.askyesno(
            title="Підтвердження видалення",
            message=f"Ви дійсно бажаєте видалити цей {item_name}?\n\nЦю дію неможливо буде скасувати!",
            icon='warning'
        )
    
    @staticmethod
    def show_success(message: str, title: str = "Успіх"):
        """Показує діалогове вікно про успішне виконання дії."""
        from tkinter import messagebox
        messagebox.showinfo(title=title, message=message)
    
    @staticmethod
    def show_error(message: str, title: str = "Помилка"):
        """Показує діалогове вікно з описом помилки."""
        from tkinter import messagebox
        messagebox.showerror(title=title, message=message)
    
    @staticmethod
    def show_warning(message: str, title: str = "Увага"):
        """Показує діалогове вікно з попередженням."""
        from tkinter import messagebox
        messagebox.showwarning(title=title, message=message)
