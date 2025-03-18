import os  # Добавлен импорт модуля os
from database import create_database, add_company, load_data_from_file_to_db
from graph_operations import load_graph_from_db, save_graph_to_file, load_graph_from_file, find_common_connections
from visualization import visualize_with_plotly

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
            files = [f for f in os.listdir() if f.endswith(".json")]  # Теперь os определён
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