import os
import json
import sqlite3
import networkx as nx
import plotly.graph_objects as go

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


def load_graph_from_db():
    """
    Загружает данные из базы данных и создает граф.
    """
    G = nx.DiGraph()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Загружаем компании
    cursor.execute("SELECT id, name FROM companies")
    for row in cursor.fetchall():
        company_id, company_name = row
        G.add_node(company_name, type="company")

    # Загружаем людей
    cursor.execute("SELECT id, name FROM people")
    for row in cursor.fetchall():
        person_id, person_name = row
        G.add_node(person_name, type="person")

    # Загружаем связи
    cursor.execute("""
        SELECT p.name AS person_name, c.name AS company_name, r.relation_type
        FROM relations r
        JOIN people p ON r.person_id = p.id
        JOIN companies c ON r.company_id = c.id
    """)
    for row in cursor.fetchall():
        person_name, company_name, relation_type = row
        G.add_edge(person_name, company_name, relation=relation_type)

    conn.close()
    return G


def save_graph_to_file(G):
    """
    Сохраняет граф в JSON-файл.
    """
    filename = input("Введите имя файла для сохранения графа (без расширения): ").strip()
    if not filename.endswith(".json"):
        filename += ".json"

    data = {
        "nodes": [{"id": node, "type": attr.get("type")} for node, attr in G.nodes(data=True)],
        "edges": [{"source": u, "target": v, "relation": data["relation"]} for u, v, data in G.edges(data=True)]
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Граф успешно сохранен в файл: {filename}")


def load_graph_from_file():
    """
    Загружает граф из JSON-файла.
    """
    files = [f for f in os.listdir() if f.endswith(".json")]
    if not files:
        print("Файлы с данными не найдены.")
        return None

    print("Найдены следующие файлы с данными:")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")
    choice = input("Введите номер файла для загрузки графа: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(files)):
        print("Некорректный выбор.")
        return None

    selected_file = files[int(choice) - 1]
    try:
        with open(selected_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        G = nx.DiGraph()
        for node in data["nodes"]:
            G.add_node(node["id"], type=node["type"])
        for edge in data["edges"]:
            G.add_edge(edge["source"], edge["target"], relation=edge["relation"])

        print(f"Граф успешно загружен из файла: {selected_file}")
        return G
    except Exception as e:
        print(f"Ошибка при загрузке графа из файла: {e}")
        return None


def visualize_with_plotly(G):
    """
    Визуализирует граф с помощью Plotly.
    """
    pos = nx.spring_layout(G, seed=42, k=0.5)

    edge_x = []
    edge_y = []
    edge_labels = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_labels.append(edge[2]["relation"])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color="gray"),
        hoverinfo="text",
        mode="lines",
        text=edge_labels,
        textposition="top center"
    )

    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_shape = []
    for node, attributes in G.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node}<br>{attributes.get('type', '')}")
        if attributes.get("type") == "company":
            node_color.append("lightblue")
            node_shape.append("square")
        else:
            node_color.append("orange")
            node_shape.append("circle")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=[node.title() for node in G.nodes()],
        textposition="top center",
        hoverinfo="text",
        hovertext=node_text,
        marker=dict(
            size=15,
            color=node_color,
            symbol=node_shape,
            line=dict(width=2, color="black")
        )
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="Граф связей между юридическими и физическими лицами",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )

    fig.show()


def main():
    # Создаем базу данных и таблицы
    create_database()

    # Главное меню
    while True:
        print("\nГлавное меню:")
        print("1. Добавить юридическое лицо")
        print("2. Построить визуализацию из базы данных")
        print("3. Сохранить граф в файл")
        print("4. Загрузить граф из файла для визуализации")
        print("5. Загрузить данные из файла в базу данных")
        print("6. Выход")
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            add_company()
        elif choice == "2":
            G = load_graph_from_db()
            visualize_with_plotly(G)
        elif choice == "3":
            G = load_graph_from_db()
            save_graph_to_file(G)
        elif choice == "4":
            G = load_graph_from_file()
            if G is not None:
                visualize_with_plotly(G)
        elif choice == "5":
            files = [f for f in os.listdir() if f.endswith(".json")]
            if not files:
                print("Файлы с данными не найдены.")
                continue

            print("Найдены следующие файлы с данными:")
            for i, file in enumerate(files, 1):
                print(f"{i}. {file}")
            choice = input("Введите номер файла для загрузки данных в базу данных: ").strip()
            if not choice.isdigit() or not (1 <= int(choice) <= len(files)):
                print("Некорректный выбор.")
                continue
            selected_file = files[int(choice) - 1]
            load_data_from_file_to_db(selected_file)
        elif choice == "6":
            print("Завершение программы.")
            break
        else:
            print("Некорректный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
