"""
Модуль для аналитики и расчетов метрик
"""
import datetime
import pandas as pd
from typing import Optional


def calculate_er(likes, comments, reposts, views):
    """Рассчитывает Engagement Rate"""
    return ((likes + comments + reposts) / views * 100) if views else 0


def calculate_previous_period(start_date: str, end_date: str) -> tuple[str, str]:
    """
    Рассчитывает предыдущий период той же длины.
    
    Args:
        start_date: Начало основного периода (YYYY-MM-DD)
        end_date: Конец основного периода (YYYY-MM-DD)
    
    Returns:
        tuple: (prev_start_date, prev_end_date) в формате YYYY-MM-DD
    """
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    
    # Вычисляем длину периода в днях (включая оба конца)
    delta_days = (end - start).days + 1
    
    # Предыдущий период заканчивается за день до начала текущего
    prev_end = start - datetime.timedelta(days=1)
    
    # Предыдущий период начинается за delta_days дней до prev_end
    prev_start = prev_end - datetime.timedelta(days=delta_days - 1)
    
    return prev_start.strftime("%Y-%m-%d"), prev_end.strftime("%Y-%m-%d")


def calculate_metrics(posts: list) -> dict:
    """
    Рассчитывает метрики для списка постов.
    
    Args:
        posts: Список постов
    
    Returns:
        dict: Словарь с метриками
    """
    if not posts:
        return {
            'posts': 0,
            'views': 0,
            'likes': 0,
            'comments': 0,
            'reposts': 0,
            'avg_er': 0.0
        }
    
    total_posts = len(posts)
    total_views = sum(post.get('views', 0) for post in posts)
    total_likes = sum(post.get('likes', 0) for post in posts)
    total_comments = sum(post.get('comments', 0) for post in posts)
    total_reposts = sum(post.get('reposts', 0) for post in posts)
    
    # Рассчитываем средний ER
    er_list = []
    for p in posts:
        views = p.get('views', 0)
        if views > 0:
            er = calculate_er(
                p.get('likes', 0),
                p.get('comments', 0),
                p.get('reposts', 0),
                views
            )
            er_list.append(er)
    
    avg_er = sum(er_list) / len(er_list) if er_list else 0.0
    
    return {
        'posts': total_posts,
        'views': total_views,
        'likes': total_likes,
        'comments': total_comments,
        'reposts': total_reposts,
        'avg_er': avg_er
    }


def compare_periods(current_posts: list, previous_posts: list) -> dict:
    """
    Сравнивает метрики двух периодов и возвращает дельты.
    
    Args:
        current_posts: Посты текущего периода
        previous_posts: Посты предыдущего периода
    
    Returns:
        dict: Словарь с метриками текущего периода, предыдущего и дельтами
    """
    current_metrics = calculate_metrics(current_posts)
    previous_metrics = calculate_metrics(previous_posts)
    
    result = {
        'current': current_metrics,
        'previous': previous_metrics,
        'deltas': {}
    }
    
    # Рассчитываем дельты для каждой метрики
    for metric in ['posts', 'views', 'likes', 'comments', 'reposts', 'avg_er']:
        current_val = current_metrics[metric]
        previous_val = previous_metrics[metric]
        
        # Абсолютная дельта
        delta = current_val - previous_val
        
        # Процентная дельта (только если previous != 0)
        if previous_val != 0:
            delta_percent = (delta / previous_val) * 100
        else:
            delta_percent = None  # Не отображаем процент, если предыдущее значение 0
        
        result['deltas'][metric] = {
            'absolute': delta,
            'percent': delta_percent
        }
    
    return result


def agg_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Агрегирует данные по периоду"""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    if period == 'week':
        df['period'] = df["date"].dt.to_period('W').apply(lambda p: p.strftime('%Y-%m-%d'))
    elif period == 'month':
        df['period'] = df["date"].dt.to_period('M').apply(lambda p: p.strftime('%Y-%m'))
    elif period == 'quarter':
        df['period'] = df["date"].dt.to_period('Q').apply(lambda p: p.strftime('%Y Q%q'))
    else:
        df['period'] = df["date"].dt.strftime('%Y-%m-%d')
    return df


def period_by_rus(period: str) -> str:
    """Переводит период на русский"""
    return dict(week="Неделя", month="Месяц", quarter="Квартал", day="День").get(period, "Период")


def format_metric(num: int) -> str:
    """Форматирует число для отображения"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)


def format_delta(delta_abs: float, delta_percent: Optional[float], is_light_bg: bool = False) -> str:
    """
    Форматирует дельту для отображения.
    
    Args:
        delta_abs: Абсолютная дельта
        delta_percent: Процентная дельта (может быть None)
        is_light_bg: Если True, использует светлые цвета для темного фона
    
    Returns:
        str: HTML строка с форматированной дельтой
    """
    if delta_abs > 0:
        icon = "▲"
        if is_light_bg:
            color = "#fff"
        else:
            color = "#059669"
    elif delta_abs < 0:
        icon = "▼"
        if is_light_bg:
            color = "#ffcccc"
        else:
            color = "#dc2626"
    else:
        icon = "—"
        if is_light_bg:
            color = "#e5e7eb"
        else:
            color = "#6b7280"
    
    if delta_percent is not None:
        percent_str = f"{delta_percent:+.1f}%"
    else:
        percent_str = "—"
    
    return f"""
    <div style="display: flex; align-items: center; justify-content: center; gap: 4px; margin-top: 4px;">
        <span style="color: {color}; font-size: 14px;">{icon}</span>
        <span style="color: {color}; font-size: 13px; font-weight: 600;">{percent_str}</span>
    </div>
    """

