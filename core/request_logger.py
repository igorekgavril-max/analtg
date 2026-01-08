"""
Модуль для логирования пользовательских запросов статистики
"""
import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


def get_moscow_timestamp() -> str:
    """Возвращает текущее время в часовом поясе МСК (UTC+3)"""
    # Создаем timezone для МСК (UTC+3)
    moscow_tz = timezone(timedelta(hours=3))
    moscow_time = datetime.now(moscow_tz)
    return moscow_time.strftime('%Y-%m-%d %H:%M:%S')


def get_user_login() -> str:
    """
    Получает идентификатор пользователя для логирования.
    В веб-приложении без аутентификации использует IP адрес или 'web_user'.
    """
    try:
        from nicegui import context
        
        # Пытаемся получить IP адрес клиента через context
        if hasattr(context, 'client') and context.client:
            client_ip = getattr(context.client, 'ip', None)
            if client_ip and client_ip != '127.0.0.1':
                # Используем IP, заменяя точки на подчеркивания для безопасности
                return f"web_user_{client_ip.replace('.', '_').replace(':', '_')}"
        
        # Пытаемся получить через request, если доступен
        try:
            from nicegui import app
            if hasattr(app, 'request') and app.request:
                client_ip = app.request.client.host if hasattr(app.request.client, 'host') else None
                if client_ip and client_ip != '127.0.0.1':
                    return f"web_user_{client_ip.replace('.', '_').replace(':', '_')}"
        except Exception:
            pass
            
    except Exception:
        pass
    
    # Fallback: используем общий идентификатор
    return "web_user"


def log_statistics_request(start_date: str, end_date: str, login: str = None):
    """
    Логирует запрос на получение статистики.
    
    Args:
        start_date: Дата начала периода (YYYY-MM-DD)
        end_date: Дата окончания периода (YYYY-MM-DD)
        login: Логин пользователя (если None, будет получен автоматически)
    
    Returns:
        bool: True если логирование успешно, False в противном случае
    """
    try:
        # Получаем логин, если не передан
        if login is None:
            login = get_user_login()
        
        # Формируем запись лога
        log_entry = {
            "timestamp_msk": get_moscow_timestamp(),
            "login": login,
            "start_date": start_date,
            "end_date": end_date,
            "event": "fetch_statistics",
            "source": "web_ui"
        }
        
        # Определяем путь к файлу лога
        project_root = Path(__file__).parent.parent
        logs_dir = project_root / "logs"
        log_file = logs_dir / "stat_requests.log"
        
        # Создаем директорию, если не существует
        logs_dir.mkdir(exist_ok=True)
        
        # Записываем в файл (append mode)
        with open(log_file, "a", encoding="utf-8") as f:
            json_line = json.dumps(log_entry, ensure_ascii=False)
            f.write(json_line + "\n")
        
        return True
    
    except Exception as e:
        # В случае ошибки логируем в stderr, но не падаем
        import sys
        print(f"Warning: Failed to log statistics request: {e}", file=sys.stderr)
        return False

