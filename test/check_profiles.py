import psycopg2
from psycopg2 import sql
from tabulate import tabulate

# Конфигурация подключения (должна совпадать с вашим docker-compose)
DB_CONFIG = {
    "host": "localhost",  # или "postgres" если запускаете из другого контейнера
    "port": 5432,
    "database": "dating_bot",
    "user": "botuser",
    "password": "botpass"
}


def fetch_profiles():
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Выполняем запрос
        cursor.execute("""
            SELECT 
                id, user_id, name, gender, city, 
                latitude, longitude, age, interesting_gender, 
                is_active, created_at
            FROM profiles
            LIMIT 10
        """)

        # Получаем результаты
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Выводим красиво в консоль
        if rows:
            print(tabulate(rows, headers=columns, tablefmt="grid"))
            print(f"\nНайдено записей: {len(rows)}")
        else:
            print("Таблица profiles пуста")

    except psycopg2.OperationalError as e:
        print(f"Ошибка подключения к базе данных: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    fetch_profiles()