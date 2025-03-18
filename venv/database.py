import sqlite3
import json

# Имя файла базы данных
DB_FILE = "graph_data.db"

def create_database():
    """
    Создает базу данных и таблицы, если они не существуют.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Таблица для компаний
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    # Таблица для людей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    # Таблица для связей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            company_id INTEGER,
            relation_type TEXT NOT NULL,
            FOREIGN KEY (person_id) REFERENCES people (id),
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_company():
    """
    Добавляет новое юридическое лицо и автоматически создает связи с участниками и руководителем.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    company_name = input("Введите название юридического лица: ").strip().capitalize()
    if not company_name:
        print("Название не может быть пустым.")
        return
    try:
        cursor.execute("INSERT INTO companies (name) VALUES (?)", (company_name,))
        conn.commit()
        print(f"Юридическое лицо '{company_name}' успешно добавлено.")
    except sqlite3.IntegrityError:
        print(f"Юридическое лицо '{company_name}' уже существует.")
        conn.close()
        return
    company_id = cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,)).fetchone()[0]
    # Запрос участников
    while True:
        shareholders_input = input(f"Введите участников {company_name} (через запятую): ").strip()
        shareholders = [name.strip().capitalize() for name in shareholders_input.split(",") if name.strip()]
        if not shareholders:
            print("У юридического лица должен быть хотя бы один участник.")
            continue
        # Добавляем участников и создаем связи
        for shareholder in shareholders:
            cursor.execute("SELECT id FROM people WHERE name = ?", (shareholder,))
            person_id = cursor.fetchone()
            if not person_id:
                cursor.execute("INSERT INTO people (name) VALUES (?)", (shareholder,))
                person_id = cursor.lastrowid
                print(f"Физическое лицо '{shareholder}' успешно добавлено.")
            else:
                person_id = person_id[0]
            # Создаем связь "учредитель"
            cursor.execute(
                "INSERT INTO relations (person_id, company_id, relation_type) VALUES (?, ?, ?)",
                (person_id, company_id, "shareholder")
            )
        conn.commit()
        print(f"Участники для '{company_name}' успешно добавлены.")
        break
    # Запрос руководителя
    while True:
        director = input(f"Введите руководителя {company_name}: ").strip().capitalize()
        if not director:
            print("У юридического лица должен быть руководитель.")
            continue
        # Добавляем руководителя и создаем связь
        cursor.execute("SELECT id FROM people WHERE name = ?", (director,))
        person_id = cursor.fetchone()
        if not person_id:
            cursor.execute("INSERT INTO people (name) VALUES (?)", (director,))
            person_id = cursor.lastrowid
            print(f"Физическое лицо '{director}' успешно добавлено.")
        else:
            person_id = person_id[0]
        # Создаем связь "руководитель"
        cursor.execute(
            "INSERT INTO relations (person_id, company_id, relation_type) VALUES (?, ?, ?)",
            (person_id, company_id, "director")
        )
        conn.commit()
        print(f"Руководитель для '{company_name}' успешно добавлен.")
        break
    conn.close()

def load_data_from_file_to_db(filename):
    """
    Загружает данные из JSON-файла в базу данных.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Очищаем таблицы перед загрузкой новых данных
        cursor.execute("DELETE FROM relations")
        cursor.execute("DELETE FROM people")
        cursor.execute("DELETE FROM companies")
        # Загружаем компании
        for node in data["nodes"]:
            if node["type"] == "company":
                cursor.execute("INSERT OR IGNORE INTO companies (name) VALUES (?)", (node["id"],))
        # Загружаем людей
        for node in data["nodes"]:
            if node["type"] == "person":
                cursor.execute("INSERT OR IGNORE INTO people (name) VALUES (?)", (node["id"],))
        # Загружаем связи
        for edge in data["edges"]:
            cursor.execute("SELECT id FROM people WHERE name = ?", (edge["source"],))
            person_id = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM companies WHERE name = ?", (edge["target"],))
            company_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO relations (person_id, company_id, relation_type) VALUES (?, ?, ?)",
                (person_id, company_id, edge["relation"])
            )
        conn.commit()
        conn.close()
        print(f"Данные успешно загружены из файла: {filename}")
    except Exception as e:
        print(f"Ошибка при загрузке данных из файла: {e}")
