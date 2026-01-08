"""
Сервисы для работы с Telegram API
"""
import os
import datetime
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageService


def get_env_path():
    """Получает путь к файлу .env (использует тот же метод, что и main.py)"""
    if '__file__' in globals():
        # Если вызывается из модуля, поднимаемся на уровень выше
        core_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(core_dir)
        return os.path.join(project_root, 'idandhash.env')
    return os.path.join(os.getcwd(), 'idandhash.env')


def extract_channel_username(link: str) -> str:
    """Извлекает username канала из ссылки"""
    if link.startswith("https://t.me/"):
        return link[len("https://t.me/"):]
    elif link.startswith("@"):
        return link[1:]
    else:
        return link


async def fetch_posts_async(
    api_id,
    api_hash,
    channel_link,
    start_date,
    end_date,
    limit=1000,
    progress_callback=None
):
    """
    Асинхронно загружает посты из Telegram канала
    
    Args:
        api_id: API ID Telegram
        api_hash: API Hash Telegram
        channel_link: Ссылка на канал
        start_date: Начало периода (YYYY-MM-DD)
        end_date: Конец периода (YYYY-MM-DD)
        limit: Максимальное количество постов
        progress_callback: Функция для обновления прогресса
    
    Returns:
        list: Список постов
    """
    channel_username = extract_channel_username(channel_link)
    
    # Загружаем переменные окружения перед использованием
    env_path = get_env_path()
    load_dotenv(env_path, override=True)  # Используем override=True для гарантированной загрузки
    
    # Используем StringSession для сохранения авторизации между запросами
    # Сессия загружается из переменной окружения TG_SESSION
    tg_session = os.getenv('TG_SESSION', '').strip()
    
    # Если переменная не найдена через dotenv, пробуем прочитать файл напрямую
    if not tg_session and os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('TG_SESSION='):
                        tg_session = line.split('=', 1)[1].strip()
                        # Убираем кавычки, если есть
                        if tg_session.startswith('"') and tg_session.endswith('"'):
                            tg_session = tg_session[1:-1]
                        elif tg_session.startswith("'") and tg_session.endswith("'"):
                            tg_session = tg_session[1:-1]
                        break
        except Exception as e:
            # Игнорируем ошибки чтения файла, используем стандартную ошибку
            pass
    
    if not tg_session:
        raise ValueError(
            f"TG_SESSION не найдена в idandhash.env (путь: {env_path}). "
            "Запустите generate_session.py для генерации сессии."
        )
    
    session = StringSession(tg_session)
    client = TelegramClient(session, int(api_id), api_hash)
    
    try:
        # Подключаемся к Telegram (неинтерактивный режим для веб-приложения)
        await client.connect()
        
        # Проверяем, авторизован ли клиент
        if not await client.is_user_authorized():
            raise ValueError(
                "Клиент не авторизован. "
                "Проверьте TG_SESSION в idandhash.env или запустите generate_session.py заново."
            )
        posts, total = [], 0
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")

        async for message in client.iter_messages(channel_username, limit=limit, reverse=True):
            if isinstance(message, MessageService):
                continue
            if not message.date:
                continue
            msg_date = message.date.replace(tzinfo=None)
            if msg_date < start or msg_date > end:
                continue
            posts.append({
                "id": message.id,
                "date": msg_date.strftime("%Y-%m-%d"),
                "datetime": msg_date,  # Полная дата и время для анализа времени публикации
                "title": (message.text[:70] if message.text else "(без текста)"),
                "likes": getattr(message, 'reactions', None) and sum([r.count for r in message.reactions.results]) or 0,
                "comments": message.replies.replies if message.replies and message.replies.replies is not None else 0,
                "reposts": getattr(message, "forwards", 0),
                "views": getattr(message, "views", 0) if hasattr(message, "views") and message.views is not None else 0
            })
            total += 1
            if progress_callback and total % 20 == 0:
                await progress_callback(f'Загружено сообщений: {total}')
    finally:
        # Гарантируем закрытие клиента даже при ошибках
        await client.disconnect()
    
    return posts

