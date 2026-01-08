"""
Утилита для генерации Telegram сессии (StringSession)

Использование:
1. Запустите: python generate_session.py
2. Введите код из Telegram (придет в сообщениях или по SMS)
3. Скопируйте выведенную строку
4. Вставьте её в idandhash.env в поле TG_SESSION
"""
import os
import sys
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession


def get_env_path():
    """Получает путь к файлу .env"""
    if '__file__' in globals():
        return os.path.join(os.path.dirname(__file__), 'idandhash.env')
    return os.path.join(os.getcwd(), 'idandhash.env')


def main():
    """Генерирует StringSession для Telegram"""
    # Загружаем конфигурацию
    load_dotenv(get_env_path())
    api_id = os.getenv('API_ID', '')
    api_hash = os.getenv('API_HASH', '')
    
    if not api_id or not api_hash:
        print("❌ Ошибка: API_ID и API_HASH должны быть указаны в idandhash.env")
        sys.exit(1)
    
    print("=" * 60)
    print("🔐 Генерация Telegram сессии")
    print("=" * 60)
    print("\n📱 Telegram запросит код авторизации.")
    print("   Код придет в приложение Telegram или по SMS.")
    print("\n⏳ Ожидание авторизации...\n")
    
    # Создаем клиент с пустой StringSession
    with TelegramClient(StringSession(), int(api_id), api_hash) as client:
        # Авторизуемся (TelegramClient автоматически запросит код)
        client.start()
        
        # Получаем строку сессии
        session_string = client.session.save()
        
        print("\n" + "=" * 60)
        print("✅ Авторизация успешна!")
        print("=" * 60)
        print("\n📋 Скопируйте следующую строку и вставьте в idandhash.env:")
        print("\n" + "-" * 60)
        print(f"TG_SESSION={session_string}")
        print("-" * 60)
        print("\n💡 После этого перезапустите приложение.")
        print("   Telegram больше не будет запрашивать код авторизации.\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        sys.exit(1)

