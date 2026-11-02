"""Стилі, константи та параметри інтерфейсу застосунку."""
import customtkinter as ctk

# =====================================================
# ПАРАМЕТРИ ЗОВНІШНЬОГО ВИГЛЯДУ
# =====================================================
APPEARANCE_MODE = "System"
COLOR_THEME = "blue"


# =====================================================
# РОЗМІРИ ШРИФТІВ
# =====================================================
class FontSize:
    """Стандартизовані розміри шрифтів для узгодженого оформлення."""
    SMALL = 12
    NORMAL = 15
    HEADER = 18
    TITLE = 16
    LARGE = 20


# =====================================================
# КОЛЬОРИ
# =====================================================
class Colors:
    """Палітра кольорів для світлої та темної тем оформлення."""
    # Формат: (світла тема, темна тема)
    CARD_BG = ("gray95", "gray13")
    CARD_BORDER = ("gray85", "gray20")
    TEXT_PRIMARY = ("black", "white")
    TEXT_SECONDARY = ("gray40", "gray60")
    BG_LIGHT = ("gray95", "gray20")
    BG_DARK = ("gray85", "gray30")
    HOVER_LIGHT = ("gray75", "gray40")
    
    # Кольори для дій
    SUCCESS = "#10b981"
    SUCCESS_HOVER = "#059669"
    DANGER = "#ef4444"
    DANGER_HOVER = "#dc2626"
    WARNING = "#f59e0b"
    WARNING_HOVER = "#d97706"
    INFO = "#1f538d"
    NEUTRAL = "#6b7280"


# =====================================================
# СТИЛІ ВИПАДНОГО СПИСКУ
# =====================================================
OPTIONMENU_STYLE = {
    "height": 24,
    "corner_radius": 6,
    "dynamic_resizing": False,
    "fg_color": ("gray95", "gray20"),
    "button_color": ("gray85", "gray30"),
    "button_hover_color": ("gray75", "gray40"),
    "text_color": ("black", "white"),
    "dropdown_fg_color": ("gray95", "gray15"),
    "dropdown_hover_color": "#8F9397",
    "dropdown_text_color": ("black", "white"),
    "font": ("Segoe UI", FontSize.NORMAL),
    "dropdown_font": ("Segoe UI", FontSize.NORMAL)
}


# =====================================================
# ВАРІАНТИ ПОСАД
# =====================================================
POSITIONS = (
    "Асистент",
    "Викладач",
    "Старший викладач",
    "Доцент",
    "Професор",
)


# =====================================================
# ВАРІАНТИ НАУКОВИХ СТУПЕНІВ
# =====================================================
DEGREES = (
    "Без ступеня",
    "Кандидат технічних наук",
    "Доктор наук",
)


# =====================================================
# ВАРІАНТИ ВЧЕНИХ ЗВАНЬ
# =====================================================
ACADEMIC_TITLES = (
    "Без звання",
    "Доцент",
    "Професор",
)


# =====================================================
# ВІДСТУПИ ТА ІНТЕРВАЛИ
# =====================================================
class Spacing:
    """Стандартизовані значення відступів."""
    XS = 5
    SM = 10
    MD = 15
    LG = 20
    XL = 25
    

# =====================================================
# СПІЛЬНІ СТИЛІ КНОПОК
# =====================================================
BUTTON_STYLE_PRIMARY = {
    "fg_color": Colors.INFO,
    "text_color": ("black", "white"),
    "hover_color": "#16396b",
}

BUTTON_STYLE_SUCCESS = {
    "fg_color": Colors.SUCCESS,
    "text_color": ("black", "white"),
    "hover_color": Colors.SUCCESS_HOVER,
}

BUTTON_STYLE_DANGER = {
    "fg_color": Colors.DANGER,
    "text_color": ("black", "white"),
    "hover_color": Colors.DANGER_HOVER,
}

BUTTON_STYLE_NEUTRAL = {
    "fg_color": ("gray90", "gray25"),
    "text_color": ("black", "white"),
    "hover_color": ("gray80", "gray35"),
}

BUTTON_STYLE_SECONDARY = {
    "fg_color": "gray35",
    "text_color": ("black", "white"),
    "hover_color": "gray45",
}


# =====================================================
# СТИЛІ ПОЛІВ ВВЕДЕННЯ
# =====================================================
ENTRY_STYLE = {
    "fg_color": "transparent",
    "font": ("Segoe UI", FontSize.NORMAL),
}


# =====================================================
# СТИЛІ СПИСКІВ ІЗ ВВЕДЕННЯМ
# =====================================================
COMBOBOX_STYLE = {
    "fg_color": ("gray95", "gray20"),
    "font": ("Segoe UI", FontSize.NORMAL),
    "dropdown_font": ("Segoe UI", FontSize.NORMAL),
}


# =====================================================
# РОЗМІРИ ВІКОН
# =====================================================
class WindowSize:
    """Стандартні розміри головного вікна та діалогів."""
    MAIN_WIDTH = 900
    MAIN_HEIGHT = 600
    MAIN_MIN_WIDTH = 800
    MAIN_MIN_HEIGHT = 600
    
    DIALOG_WIDTH = 320
    DIALOG_HEIGHT = 220


# =====================================================
# ПАРАМЕТРИ ДІАЛОГОВИХ ВІКОН
# =====================================================
DIALOG_TITLES = {
    "confirm_save": "Підтвердження збереження",
    "confirm_delete": "Підтвердження видалення",
    "success": "Успіх",
    "error": "Помилка",
    "warning": "Увага",
}


# =====================================================
# ДОПОМІЖНА ФУНКЦІЯ СТВОРЕННЯ ШРИФТУ
# =====================================================
def create_font(size: int = FontSize.NORMAL, weight: str = "normal") -> ctk.CTkFont:
    """Створює шрифт CustomTkinter із заданими розміром і насиченістю."""
    return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)
