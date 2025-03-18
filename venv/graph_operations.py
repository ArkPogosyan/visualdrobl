def save_graph_to_file(G):
    """
    Сохраняет граф в JSON-файл.
    """
    if not G.nodes or not G.edges:
        print("Граф пустой. Нечего сохранять.")
        return
    filename = input("Введите имя файла для сохранения графа (без расширения): ").strip()
    if not filename.endswith(".json"):
        filename += ".json"
    data = {
        "nodes": [{"id": node.upper(), "type": attr.get("type")} for node, attr in G.nodes(data=True)],  # Преобразование в верхний регистр
        "edges": [{"source": u.upper(), "target": v.upper(), "relation": data["relation"]} for u, v, data in G.edges(data=True)]  # Преобразование в верхний регистр
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Граф успешно сохранен в файл: {filename}")

def load_graph_from_file():
    """
    Загружает граф из JSON-файла.
    """
    import os
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
            G.add_node(node["id"].upper(), type=node["type"])  # Преобразование в верхний регистр
        for edge in data["edges"]:
            G.add_edge(edge["source"].upper(), edge["target"].upper(), relation=edge["relation"])  # Преобразование в верхний регистр
        print(f"Граф успешно загружен из файла: {selected_file}")
        return G
    except Exception as e:
        print(f"Ошибка при загрузке графа из файла: {e}")
        return None