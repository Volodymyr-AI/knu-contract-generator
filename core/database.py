"""Керування базою даних організацій, факультетів, кафедр і підписантів."""
import os
import sqlite3
from typing import Optional, List, Tuple, Dict

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CORE_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, "university.db")


# =====================================================
# SQL-ЗАПИТИ (окремі константи для зручності супроводу)
# =====================================================
class SQLQueries:
    """Константи SQL-запитів, згруповані за типами даних."""
    
    # Організації
    SELECT_ORG_ALL = """
        SELECT id, name, head_role, head_surname, head_first_name, head_patronymic,
               head_surname_gen, head_first_name_gen, head_patronymic_gen
        FROM organizations ORDER BY name ASC
    """
    SELECT_ORG_NAMES = "SELECT name FROM organizations ORDER BY name ASC"
    SELECT_ORG_COUNT = "SELECT COUNT(*) FROM organizations"
    UPDATE_ORG = """
        UPDATE organizations
        SET name = ?, head_role = ?, head_surname = ?, head_first_name = ?, head_patronymic = ?,
            head_surname_gen = ?, head_first_name_gen = ?, head_patronymic_gen = ?
        WHERE id = ?
    """
    DELETE_ORG = "DELETE FROM organizations WHERE id = ?"
    INSERT_ORG = """
        INSERT INTO organizations
        (name, head_role, head_surname, head_first_name, head_patronymic,
         head_surname_gen, head_first_name_gen, head_patronymic_gen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Факультети
    SELECT_POSITIONS = "SELECT name, name_gen, name_ins FROM positions ORDER BY id"
    SELECT_FAC_ALL = """
        SELECT id, name, head_role, head_surname, head_first_name, head_patronymic,
               fac_name_gen
        FROM faculties
    """
    SELECT_FAC_BY_ORG = """
        SELECT id, name, head_role, head_surname, head_first_name, head_patronymic,
               fac_name_gen
        FROM faculties WHERE organization_id = ?
    """
    UPDATE_FAC = """
        UPDATE faculties
        SET name = ?, head_role = ?, head_surname = ?, head_first_name = ?,
            head_patronymic = ?, fac_name_gen = COALESCE(?, fac_name_gen)
        WHERE id = ?
    """
    DELETE_FAC = "DELETE FROM faculties WHERE id = ?"
    INSERT_FAC = """
        INSERT INTO faculties
        (organization_id, name, head_role, head_surname, head_first_name, head_patronymic)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    INSERT_FAC_WITH_GEN = """
        INSERT INTO faculties
        (organization_id, name, head_role, head_surname, head_first_name,
         head_patronymic, fac_name_gen)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    # Кафедри
    SELECT_DEPT_BY_FAC = """
        SELECT id, name, head_role, head_surname, head_first_name, head_patronymic
        FROM departments WHERE faculty_id = ?
    """
    SELECT_DEPT_BY_ORG_WITHOUT_FACULTY = """
        SELECT id, name, head_role, head_surname, head_first_name, head_patronymic
        FROM departments
        WHERE organization_id = ? AND faculty_id IS NULL
        ORDER BY name ASC
    """
    SELECT_DEPT_BY_ORG_NAME = """
        SELECT d.name 
        FROM departments d
        JOIN organizations o ON d.organization_id = o.id
        WHERE o.name = ?
        ORDER BY d.name ASC
    """
    SELECT_DEPT_ALL = "SELECT name FROM departments ORDER BY name ASC"
    UPDATE_DEPT = """
        UPDATE departments
        SET name = ?, head_role = ?, head_surname = ?, head_first_name = ?, head_patronymic = ?
        WHERE id = ?
    """
    DELETE_DEPT = "DELETE FROM departments WHERE id = ?"
    INSERT_DEPT = """
        INSERT INTO departments
        (organization_id, faculty_id, name, head_role, head_surname, head_first_name, head_patronymic)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    # Підписанти
    SELECT_SIG_ORG = """
        SELECT id, head_role, head_surname, head_first_name, head_patronymic
        FROM organizations
    """
    SELECT_RECTOR = """
        SELECT head_surname, head_first_name, head_patronymic,
               head_surname_gen, head_first_name_gen, head_patronymic_gen
        FROM organizations WHERE head_role = 'Ректор' ORDER BY id LIMIT 1
    """
    SELECT_SIG_GLOBAL = "SELECT id, role, full_name FROM signatories ORDER BY id"
    UPDATE_SIG_ORG = """
        UPDATE organizations
        SET head_role = ?, head_surname = ?, head_first_name = ?, head_patronymic = ?,
            head_surname_gen = CASE
                WHEN head_surname != ? OR head_first_name != ? OR head_patronymic != ?
                THEN ''
                ELSE head_surname_gen
            END,
            head_first_name_gen = CASE
                WHEN head_surname != ? OR head_first_name != ? OR head_patronymic != ?
                THEN ''
                ELSE head_first_name_gen
            END,
            head_patronymic_gen = CASE
                WHEN head_surname != ? OR head_first_name != ? OR head_patronymic != ?
                THEN ''
                ELSE head_patronymic_gen
            END
        WHERE id = ?
    """
    UPDATE_SIG_GLOBAL = "UPDATE signatories SET role = ?, full_name = ? WHERE id = ?"
    INSERT_SIG = "INSERT OR IGNORE INTO signatories (organization_id, role, full_name) VALUES (?, ?, ?)"


class DataManager:
    """Керує операціями з організаціями, факультетами, кафедрами й підписантами."""
    
    def __init__(self, db_name: str = DB_PATH):
        """Ініціалізує менеджер бази даних і виконує необхідні міграції."""
        self.db_name = db_name
        self.create_tables()
        self.seed_initial_data()
        self.migrate_head_names()
        self.migrate_organization_genitive_names()
        self.migrate_faculty_genitive_names()

    def get_connection(self) -> sqlite3.Connection:
        """Відкриває з'єднання з базою даних і вмикає перевірку зовнішніх ключів."""
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    # =====================================================
    # ІНІЦІАЛІЗАЦІЯ БАЗИ ДАНИХ
    # =====================================================

    def create_tables(self):
        """Створює відсутні таблиці та початкові записи."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Організації (університети та інститути)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    head_role TEXT NOT NULL DEFAULT 'Ректор',
                    head_surname TEXT NOT NULL DEFAULT '',
                    head_first_name TEXT NOT NULL DEFAULT '',
                    head_patronymic TEXT NOT NULL DEFAULT '',
                    head_surname_gen TEXT NOT NULL DEFAULT '',
                    head_first_name_gen TEXT NOT NULL DEFAULT '',
                    head_patronymic_gen TEXT NOT NULL DEFAULT ''
                )
            """)

            # Факультети
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faculties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    head_role TEXT NOT NULL DEFAULT 'Декан',
                    head_surname TEXT NOT NULL DEFAULT '',
                    head_first_name TEXT NOT NULL DEFAULT '',
                    head_patronymic TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (organization_id) REFERENCES organizations (id) ON DELETE CASCADE,
                    UNIQUE (name, organization_id)
                )
            """)

            # Кафедри
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_id INTEGER NOT NULL,
                    faculty_id INTEGER,
                    name TEXT NOT NULL,
                    head_role TEXT NOT NULL DEFAULT 'Завідувач кафедри',
                    head_surname TEXT NOT NULL DEFAULT '',
                    head_first_name TEXT NOT NULL DEFAULT '',
                    head_patronymic TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (organization_id) REFERENCES organizations (id) ON DELETE CASCADE,
                    FOREIGN KEY (faculty_id) REFERENCES faculties (id) ON DELETE CASCADE,
                    UNIQUE (name, organization_id)
                )
            """)

            # Підписанти, чиї дані використовуються в контрактах
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signatories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    FOREIGN KEY (organization_id) REFERENCES organizations (id) ON DELETE CASCADE,
                    UNIQUE (role, organization_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    name_gen TEXT NOT NULL,
                    name_ins TEXT NOT NULL DEFAULT ''
                )
            """)
            position_columns = {
                row[1] for row in cursor.execute("PRAGMA table_info(positions)")
            }
            if "name_ins" not in position_columns:
                cursor.execute(
                    "ALTER TABLE positions ADD COLUMN name_ins TEXT NOT NULL DEFAULT ''"
                )

            positions = (
                ("Асистент", "асистента", "асистентом"),
                ("Викладач", "викладача", "викладачем"),
                ("Старший викладач", "старшого викладача", "старшим викладачем"),
                ("Доцент", "доцента", "доцентом"),
                ("Професор", "професора", "професором"),
            )
            cursor.executemany(
                """
                INSERT OR IGNORE INTO positions (name, name_gen, name_ins)
                VALUES (?, ?, ?)
                """,
                positions,
            )
            cursor.executemany(
                """
                UPDATE positions
                SET name_ins = ?
                WHERE name = ? AND name_ins = ''
                """,
                ((name_ins, name) for name, _, name_ins in positions),
            )

            conn.commit()

    def migrate_head_names(self):
        """Додає окремі складові ПІБ керівників і переносить наявні дані."""
        columns = ("head_surname", "head_first_name", "head_patronymic")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table in ("organizations", "faculties", "departments"):
                existing = {
                    row[1] for row in cursor.execute(f"PRAGMA table_info({table})")
                }
                for column in columns:
                    if column not in existing:
                        cursor.execute(
                            f"ALTER TABLE {table} ADD COLUMN {column} TEXT NOT NULL DEFAULT ''"
                        )

                if "head_name" in existing:
                    rows = cursor.execute(
                        f"""
                        SELECT id, head_name FROM {table}
                        WHERE head_surname = '' AND head_first_name = '' AND head_patronymic = ''
                        """
                    ).fetchall()
                    for row_id, legacy_name in rows:
                        surname, first_name, patronymic = self._split_legacy_head_name(legacy_name)
                        cursor.execute(
                            f"""
                            UPDATE {table}
                            SET head_surname = ?, head_first_name = ?, head_patronymic = ?
                            WHERE id = ?
                            """,
                            (surname, first_name, patronymic, row_id),
                        )
                    cursor.execute(f"ALTER TABLE {table} DROP COLUMN head_name")
                for row_id, surname in cursor.execute(
                    f"SELECT id, head_surname FROM {table}"
                ).fetchall():
                    cursor.execute(
                        f"UPDATE {table} SET head_surname = ? WHERE id = ?",
                        (surname.strip().upper(), row_id),
                    )

    def migrate_faculty_genitive_names(self):
        """Додає та заповнює родові назви факультетів для шаблонів контрактів."""
        faculty_names = {
            "гірничо-металургійний факультет": "гірничо-металургійного факультету",
            "факультет механічної інженерії та транспорту": "факультету механічної інженерії та транспорту",
            "електротехнічний факультет": "електротехнічного факультету",
            "будівельний факультет": "будівельного факультету",
            "факультет інформаційних технологій": "факультету інформаційних технологій",
            "факультет економіки та управління бізнесом": "факультету економіки та управління бізнесом",
        }
        with self.get_connection() as conn:
            cursor = conn.cursor()
            existing = {
                row[1] for row in cursor.execute("PRAGMA table_info(faculties)")
            }
            if "fac_name_gen" not in existing and "dep_name_gen" in existing:
                cursor.execute(
                    "ALTER TABLE faculties RENAME COLUMN dep_name_gen TO fac_name_gen"
                )
                existing.remove("dep_name_gen")
                existing.add("fac_name_gen")
            elif "fac_name_gen" in existing and "dep_name_gen" in existing:
                cursor.execute(
                    """
                    UPDATE faculties
                    SET fac_name_gen = dep_name_gen
                    WHERE fac_name_gen = '' AND dep_name_gen != ''
                    """
                )
                cursor.execute("ALTER TABLE faculties DROP COLUMN dep_name_gen")
                existing.remove("dep_name_gen")

            if "fac_name_gen" not in existing:
                cursor.execute(
                    "ALTER TABLE faculties ADD COLUMN fac_name_gen TEXT NOT NULL DEFAULT ''"
                )

            for faculty_name, genitive_name in faculty_names.items():
                cursor.execute(
                    """
                    UPDATE faculties
                    SET fac_name_gen = ?
                    WHERE name = ? AND fac_name_gen = ''
                    """,
                    (genitive_name, faculty_name),
                )
            cursor.execute(
                """
                UPDATE faculties
                SET fac_name_gen = ?
                WHERE name = ? AND fac_name_gen = ?
                """,
                (
                    faculty_names["факультет механічної інженерії та транспорту"],
                    "факультет механічної інженерії та транспорту",
                    "факультету маханічної інженерії та транспорту",
                ),
            )

    def migrate_organization_genitive_names(self):
        """Зберігає родові форми ПІБ керівників організацій в окремих полях."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            columns = {row[1] for row in cursor.execute("PRAGMA table_info(organizations)")}
            for column in (
                "head_surname_gen",
                "head_first_name_gen",
                "head_patronymic_gen",
            ):
                if column not in columns:
                    cursor.execute(
                        f"ALTER TABLE organizations ADD COLUMN {column} TEXT NOT NULL DEFAULT ''"
                    )

            if "head_name_gen" in columns:
                rows = cursor.execute(
                    """
                    SELECT id, head_name_gen
                    FROM organizations
                    WHERE head_name_gen != ''
                        AND head_surname_gen = ''
                        AND head_first_name_gen = ''
                        AND head_patronymic_gen = ''
                    """
                ).fetchall()
                for org_id, legacy_name in rows:
                    surname, first_name, patronymic = self._split_legacy_head_name(legacy_name)
                    cursor.execute(
                        """
                        UPDATE organizations
                        SET head_surname_gen = ?, head_first_name_gen = ?,
                            head_patronymic_gen = ?
                        WHERE id = ?
                        """,
                        (surname.capitalize(), first_name, patronymic, org_id),
                    )
                cursor.execute("ALTER TABLE organizations DROP COLUMN head_name_gen")
            cursor.execute(
                """
                UPDATE organizations
                SET head_surname_gen = 'Ступніка',
                    head_first_name_gen = 'Миколи',
                    head_patronymic_gen = CASE
                        WHEN head_patronymic = 'Іванович' THEN 'Івановича'
                        ELSE ''
                    END
                WHERE name = 'Криворізький національний університет'
                    AND head_role = 'Ректор'
                    AND head_surname = 'СТУПНІК'
                    AND head_first_name = 'Микола'
                    AND head_surname_gen = ''
                    AND head_first_name_gen = ''
                    AND head_patronymic_gen = ''
                """
            )

    @staticmethod
    def _split_legacy_head_name(full_name: str) -> Tuple[str, str, str]:
        """Розбирає старий формат «Ім'я [по батькові] ПРІЗВИЩЕ» на складові."""
        parts = (full_name or "").split()
        if not parts or parts == ["---"]:
            return "", "", ""
        if len(parts) == 1:
            return "", parts[0], ""

        surname_index = next(
            (
                index for index, part in enumerate(parts)
                if any(char.isalpha() for char in part) and part.isupper()
            ),
            len(parts) - 1,
        )
        surname = parts[surname_index]
        remaining = parts[:surname_index] + parts[surname_index + 1:]
        first_name = remaining[0] if remaining else ""
        patronymic = " ".join(remaining[1:])
        return surname, first_name, patronymic

    @staticmethod
    def format_head_name(surname: str, first_name: str, patronymic: str = "") -> str:
        """Форматує ПІБ із окремих складових у звичному порядку."""
        return " ".join(part.strip() for part in (surname, first_name, patronymic) if part and part.strip())

    @staticmethod
    def format_short_head_name(surname: str, first_name: str) -> str:
        """Форматує коротке ім'я як ім'я та прізвище."""
        return " ".join(part.strip() for part in (first_name, surname) if part and part.strip())

    def seed_initial_data(self):
        """Заповнює порожню базу типовими організаціями, факультетами й кафедрами."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(SQLQueries.SELECT_ORG_COUNT)
            if cursor.fetchone()[0] > 0:
                return  # База вже містить записи

            # 1. Додаємо організації
            cursor.execute(
                SQLQueries.INSERT_ORG,
                (
                    "Криворізький національний університет", "Ректор",
                    "СТУПНІК", "Микола", "",
                    "Ступніка", "Миколи", "Івановича",
                )
            )
            univ_id = cursor.lastrowid

            cursor.execute(
                SQLQueries.INSERT_ORG,
                ("Навчально-науковий інститут економіки і торгівлі імені Михайла Туган-Барановського", 
                 "Директор", "КОЖУХОВА", "Тетяна", "", "", "", "")
            )
            inst_id = cursor.lastrowid

            # 2. Додаємо типових підписантів
            default_roles = [
                ("Перший проректор", "Владислав ЧУБАРОВ"),
                ("Головний бухгалтер", "Ірина ЛЕОНОВА"),
                ("Завідувач навчально-методичного відділу", "Світлана ІВАШУРА"),
                ("Начальник юридичного відділу", "Ольга БАРЧАК"),
                ("Начальник планового відділу", "Ганна НАЗАРОВА"),
                ("Начальник відділу кадрів", "Наталія ЗАЙЦЕВА")
            ]
            for role, full_name in default_roles:
                cursor.execute(SQLQueries.INSERT_SIG, (univ_id, role, full_name))

            # 3. Додаємо факультети
            faculties_data = {
                "гірничо-металургійний факультет": "Іван КУШНЕРЬОВ",
                "факультет механічної інженерії та транспорту": "Андрій ПІКІЛЬНЯК",
                "електротехнічний факультет": "Владислав ФЕДОТОВ",
                "будівельний факультет": "Дмитро ПОПРУГА",
                "факультет інформаційних технологій": "Іван МУЗИКА",
                "факультет економіки та управління бізнесом": "Юлія КАШУБІНА",
            }
            
            faculty_ids = {}
            for fac_name, dean_name in faculties_data.items():
                cursor.execute(
                    SQLQueries.INSERT_FAC,
                    (univ_id, fac_name, 'Декан', *self._split_legacy_head_name(dean_name))
                )
                faculty_ids[fac_name] = cursor.lastrowid

            # 4. Додаємо кафедри
            structure = {
                "гірничо-металургійний факультет": {
                    "підземної розробки родовищ корисних копалин": "Михайло ФЕДЬКО",
                    "відкритих гірничих робіт": "Сергій ЖУКОВ",
                    "охорони праці та цивільної безпеки": "Наталія ШВАГЕР",
                    "будівельних геотехнологій": "Борис АНДРЄЄВ",
                    "маркшейдерії": "Олександр ДОЛГІХ",
                    "збагачення корисних копалин і хімії": "Тетяна ОЛІЙНИК",
                    "металургії чорних металів і ливарного виробництва": "Сергій САВЕЛЬЄВ",
                    "геології та екології": "Світлана ПАНОВА"
                },
                "факультет механічної інженерії та транспорту": {
                    "технології машинобудування": "Антон РЯЗАНЦЕВ",
                    "гірничих машин та обладнання": "Андрій ХРУЦЬКИЙ",
                    "автомобільного транспорту": "Юрій МОНАСТИРСЬКИЙ",
                    "фізичного виховання": "Ігор ПОСЛУШНОЙ"
                },
                "електротехнічний факультет": {
                    "електричної інженерії": "Олег СІНЧУК",
                    "теплоенергетики": "Олег ЗАМИЦЬКИЙ",
                    "електромеханіки": "Станіслав ТОЛМАЧОВ"
                },
                "будівельний факультет": {
                    "теплогазоводопостачання, водовідведення і вентиляції": "---",
                    "технології будівельних виробів, матеріалів та конструкцій": "Олександра ШИШКІНА",
                    "промислового, цивільного і міського будівництва": "Олександр ВАЛОВОЙ",
                    "геодезії": "Володимир ПЕРЕГУДОВ"
                },
                "факультет інформаційних технологій": {
                    "моделювання та програмного забезпечення": "Андрій СТРЮК",
                    "автоматизації, комп'ютерних наук і технологій": "Сергій РУБАН",
                    "комп'ютерних систем та мереж": "Андрій КУПІН",
                    "професійної та соціально-гуманітарної освіти": "Світлана ХОЦКІНА",
                    "іноземних мов": "Надія Голівер",
                    "вищої математики та физики": "Іван МАКСИМОВ"
                },
                "факультет економіки та управління бізнесом": {
                    "менеджменту та адміністрування": "Лариса ВАРАВА",
                    "економіки, організації та управління підприємствами": "Альона ШАХНО",
                    "фінансів  суб'єктів господарювання та інноваційного розвитку": "Ріта КОРОЛЕНКО",
                    "маркетингу, обліку, оподаткування та публічного управління": "Вікторія АДАМОВСЬКА",
                    "права": "Валерій ЮСУПОВ"
                }
            }

            for fac_name, depts in structure.items():
                fac_id = faculty_ids.get(fac_name)
                if fac_id:
                    for dept_name, head_name in depts.items():
                        cursor.execute(
                            SQLQueries.INSERT_DEPT,
                            (univ_id, fac_id, dept_name, 'Завідувач кафедри', *self._split_legacy_head_name(head_name))
                        )

            conn.commit()

    # =====================================================
    # ОПЕРАЦІЇ З ОРГАНІЗАЦІЯМИ
    # =====================================================

    def get_organizations(self) -> List[Tuple]:
        """Повертає організації з назвами та складовими ПІБ керівників."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(SQLQueries.SELECT_ORG_ALL)
                return cursor.fetchall()
        except Exception as e:
            self._log_error("Завантаження організацій", e)
            return []

    def get_organization_names(self) -> List[str]:
        """Повертає назви всіх організацій."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(SQLQueries.SELECT_ORG_NAMES)
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self._log_error("Завантаження назв організацій", e)
            return []

    def add_organization(
        self, name: str, head_role: str,
        head_surname: str, head_first_name: str, head_patronymic: str,
        head_surname_gen: str = "", head_first_name_gen: str = "",
        head_patronymic_gen: str = ""
    ) -> bool:
        """Додає організацію та дані її керівника."""
        return self._execute_insert(
            SQLQueries.INSERT_ORG,
            (name.strip(), head_role.strip(), head_surname.strip().upper(),
             head_first_name.strip(), head_patronymic.strip(),
             head_surname_gen.strip().capitalize(), head_first_name_gen.strip(),
             head_patronymic_gen.strip()),
            "додавання організації"
        )

    def update_organization(
        self, org_id: int, name: str, head_role: str,
        head_surname: str, head_first_name: str, head_patronymic: str,
        head_surname_gen: str = "", head_first_name_gen: str = "",
        head_patronymic_gen: str = ""
    ) -> bool:
        """Оновлює назву організації та дані її керівника."""
        return self._execute_update(
            SQLQueries.UPDATE_ORG,
            (name.strip(), head_role.strip(), head_surname.strip().upper(),
             head_first_name.strip(), head_patronymic.strip(),
             head_surname_gen.strip().capitalize(), head_first_name_gen.strip(),
             head_patronymic_gen.strip(), org_id),
            "оновлення організації"
        )

    def delete_organization(self, org_id: int) -> bool:
        """Видаляє організацію."""
        return self._execute_delete(
            SQLQueries.DELETE_ORG,
            (org_id,),
            f"видалення організації #{org_id}"
        )

    # =====================================================
    # ОПЕРАЦІЇ З ФАКУЛЬТЕТАМИ
    # =====================================================

    def get_positions(self) -> List[Tuple[str, str, str]]:
        """Повертає назви посад у називному, родовому та орудному відмінках."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(SQLQueries.SELECT_POSITIONS)
                return cursor.fetchall()
        except Exception as e:
            self._log_error("Завантаження посад", e)
            return []

    def get_all_faculties(self) -> List[Tuple]:
        """Повертає всі факультети."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(SQLQueries.SELECT_FAC_ALL)
                return cursor.fetchall()
        except Exception as e:
            self._log_error("Завантаження факультетів", e)
            return []

    def get_faculties_by_organization(self, org_id: int) -> List[Tuple]:
        """Повертає факультети, що належать до вказаної організації."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(SQLQueries.SELECT_FAC_BY_ORG, (org_id,))
                return cursor.fetchall()
        except Exception as e:
            self._log_error("Завантаження факультетів", e)
            return []

    def add_faculty(
        self, org_id: int, name: str, head_role: str,
        head_surname: str, head_first_name: str, head_patronymic: str,
        name_gen: str = ""
    ) -> bool:
        """Додає факультет, його родову назву та дані декана."""
        return self._execute_insert(
            SQLQueries.INSERT_FAC_WITH_GEN,
            (org_id, name.strip(), head_role.strip(), head_surname.strip().upper(),
             head_first_name.strip(), head_patronymic.strip(), name_gen.strip()),
            "додавання факультету"
        )

    def update_faculty(
        self, fac_id: int, name: str, head_role: str,
        head_surname: str, head_first_name: str, head_patronymic: str,
        name_gen: Optional[str] = None
    ) -> bool:
        """Оновлює назву факультету, її родову форму та дані декана."""
        return self._execute_update(
            SQLQueries.UPDATE_FAC,
            (name.strip(), head_role.strip(), head_surname.strip().upper(),
             head_first_name.strip(), head_patronymic.strip(),
             name_gen.strip() if name_gen is not None else None, fac_id),
            "оновлення факультету"
        )

    def delete_faculty(self, fac_id: int) -> bool:
        """Видаляє факультет."""
        return self._execute_delete(
            SQLQueries.DELETE_FAC,
            (fac_id,),
            f"видалення факультету #{fac_id}"
        )

    # =====================================================
    # ОПЕРАЦІЇ З КАФЕДРАМИ
    # =====================================================

    def get_departments_by_faculty(self, faculty_id: int) -> List[Tuple]:
        """Повертає кафедри вказаного факультету."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(SQLQueries.SELECT_DEPT_BY_FAC, (faculty_id,))
                return cursor.fetchall()
        except Exception as e:
            self._log_error("Завантаження кафедр", e)
            return []

    def get_departments_without_faculty(self, org_id: int) -> List[Tuple]:
        """Повертає кафедри організації, які не належать до факультету."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(SQLQueries.SELECT_DEPT_BY_ORG_WITHOUT_FACULTY, (org_id,))
                return cursor.fetchall()
        except Exception as e:
            self._log_error("Завантаження кафедр без факультету", e)
            return []

    def get_departments_list(self, org_name: Optional[str] = None) -> List[str]:
        """Повертає назви кафедр, за потреби відфільтровані за організацією."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if org_name:
                    cursor.execute(SQLQueries.SELECT_DEPT_BY_ORG_NAME, (org_name,))
                else:
                    cursor.execute(SQLQueries.SELECT_DEPT_ALL)
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self._log_error("Завантаження списку кафедр", e)
            return []

    def add_department(
        self, org_id: int, faculty_id: Optional[int], name: str, head_role: str,
        head_surname: str, head_first_name: str, head_patronymic: str
    ) -> bool:
        """Додає кафедру та дані її керівника."""
        return self._execute_insert(
            SQLQueries.INSERT_DEPT,
            (org_id, faculty_id, name.strip(), head_role.strip(), head_surname.strip().upper(),
             head_first_name.strip(), head_patronymic.strip()),
            "додавання кафедри"
        )

    def update_department(
        self, dept_id: int, name: str, head_role: str,
        head_surname: str, head_first_name: str, head_patronymic: str
    ) -> bool:
        """Оновлює назву кафедри та дані її керівника."""
        return self._execute_update(
            SQLQueries.UPDATE_DEPT,
            (name.strip(), head_role.strip(), head_surname.strip().upper(),
             head_first_name.strip(), head_patronymic.strip(), dept_id),
            "оновлення кафедри"
        )

    def delete_department(self, dept_id: int) -> bool:
        """Видаляє кафедру."""
        return self._execute_delete(
            SQLQueries.DELETE_DEPT,
            (dept_id,),
            f"видалення кафедри #{dept_id}"
        )

    # =====================================================
    # ОПЕРАЦІЇ З ПІДПИСАНТАМИ
    # =====================================================

    def get_all_signatories(self) -> List[Tuple]:
        """Повертає керівників організацій і загальний список підписантів."""
        signatories = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(SQLQueries.SELECT_SIG_ORG)
                for row in cursor.fetchall():
                    if row[1].strip().casefold() in {"ректор", "директор"}:
                        display_name = self.format_short_head_name(row[2], row[3])
                    else:
                        display_name = self.format_head_name(row[2], row[3], row[4])
                    signatories.append(("org", row[0], row[1], display_name))

                cursor.execute(SQLQueries.SELECT_SIG_GLOBAL)
                for row in cursor.fetchall():
                    signatories.append(("global", row[0], row[1], row[2]))
        except Exception as e:
            self._log_error("Завантаження підписантів", e)
        
        return signatories

    def get_rector_names(self) -> Tuple[str, str, str]:
        """Повертає коротке, повне в називному та збережене повне родове ПІБ ректора."""
        try:
            with self.get_connection() as conn:
                row = conn.execute(SQLQueries.SELECT_RECTOR).fetchone()
            if row:
                surname, first_name, patronymic = row[:3]
                full_name = self.format_head_name(surname, first_name, patronymic)
                short_name = self.format_short_head_name(surname, first_name)
                surname_gen, first_name_gen, patronymic_gen = row[3:]
                full_name_gen = " ".join(
                    part for part in (surname_gen, first_name_gen, patronymic_gen) if part
                )
                return short_name, full_name, full_name_gen or ""
        except Exception as e:
            self._log_error("Завантаження ПІБ ректора", e)
        return "", "", ""

    def update_signatory(self, source_type: str, sig_id: int, role: str, full_name: str) -> bool:
        """Оновлює посаду та ім'я підписанта."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if source_type == "org":
                    surname, first_name, patronymic = self._split_legacy_head_name(full_name)
                    cursor.execute(
                        SQLQueries.UPDATE_SIG_ORG,
                        (
                            role, surname.upper(), first_name, patronymic,
                            *((
                                surname.upper(), first_name, patronymic,
                            ) * 3),
                            sig_id,
                        ),
                    )
                else:
                    cursor.execute(
                        SQLQueries.UPDATE_SIG_GLOBAL, (role, full_name, sig_id)
                    )
                conn.commit()
                return True
        except Exception as e:
            self._log_error(f"Оновлення підписанта (тип: {source_type})", e)
            return False

    # =====================================================
    # ДОПОМІЖНІ МЕТОДИ
    # =====================================================

    def get_department_info(self, dept_name: str) -> Dict:
        """Повертає дані кафедри, її факультету, керівників та організації."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        d.id, d.name, d.head_role, d.head_surname, d.head_first_name, d.head_patronymic,
                        f.id, f.name, f.fac_name_gen, f.head_role, f.head_surname, f.head_first_name, f.head_patronymic,
                        o.id, o.name, o.head_role, o.head_surname, o.head_first_name, o.head_patronymic
                    FROM departments d
                    LEFT JOIN faculties f ON d.faculty_id = f.id
                    JOIN organizations o ON d.organization_id = o.id
                    WHERE d.name = ?
                ''', (dept_name,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "department_id": row[0],
                        "department_name": row[1],
                        "department_role": row[2] or "Завідувач кафедри",
                        "department_head": self.format_short_head_name(row[3], row[4]),
                        "department_head_full": self.format_head_name(row[3], row[4], row[5]),
                        "faculty_id": row[6],
                        "faculty_name": row[7] or "",
                        "faculty_name_gen": row[8] or "",
                        "faculty_role": row[9] or "",
                        "faculty_head": self.format_short_head_name(row[10], row[11]),
                        "faculty_head_full": self.format_head_name(row[10], row[11], row[12]),
                        "organization_id": row[13],
                        "organization_name": row[14] or "",
                        "organization_role": row[15] or "",
                        "organization_head": self.format_short_head_name(row[16], row[17]),
                        "organization_head_full": self.format_head_name(row[16], row[17], row[18])
                    }
        except Exception as e:
            self._log_error("Завантаження інформації кафедри", e)
        
        return {}

    # =====================================================
    # ВНУТРІШНІ ДОПОМІЖНІ МЕТОДИ
    # =====================================================

    def _execute_insert(self, query: str, params: tuple, operation: str) -> bool:
        """Виконує запит додавання та обробляє помилки бази даних."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            self._log_error(operation, e)
            return False

    def _execute_update(self, query: str, params: tuple, operation: str) -> bool:
        """Виконує запит оновлення та обробляє помилки бази даних."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self._log_error(operation, e)
            return False

    def _execute_delete(self, query: str, params: tuple, operation: str) -> bool:
        """Виконує запит видалення та обробляє помилки бази даних."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self._log_error(operation, e)
            return False

    @staticmethod
    def _log_error(operation: str, error: Exception):
        """Записує помилку операції з базою даних у журнал."""
        print(f"❌ Помилка при {operation}: {str(error)}")
