"""
UI компонент: Блок статистики
"""
import datetime
from nicegui import ui
from core.analytics import calculate_er, calculate_previous_period, format_metric, format_delta
from typing import Optional


def stats_html(posts, start_date, end_date, channel='', comparison_data=None):
    """
    Генерирует HTML со статистикой.
    
    Args:
        posts: Список всех постов
        start_date: Начало периода (YYYY-MM-DD)
        end_date: Конец периода (YYYY-MM-DD)
        channel: Имя канала
        comparison_data: Данные сравнения (результат compare_periods) или None
    """
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    selected_posts = [
        post for post in posts
        if start <= datetime.datetime.strptime(post['date'], "%Y-%m-%d").date() <= end
    ]
    
    # Используем данные сравнения, если они есть, иначе рассчитываем метрики
    if comparison_data:
        current_metrics = comparison_data['current']
        total_posts = current_metrics['posts']
        total_views = current_metrics['views']
        total_likes = current_metrics['likes']
        total_comments = current_metrics['comments']
        total_reposts = current_metrics['reposts']
        avg_er = current_metrics['avg_er']
        deltas = comparison_data['deltas']
    else:
        total_posts = len(selected_posts)
        total_views = sum(post.get('views', 0) for post in selected_posts)
        total_likes = sum(post['likes'] for post in selected_posts)
        total_comments = sum(post['comments'] for post in selected_posts)
        total_reposts = sum(post['reposts'] for post in selected_posts)
        er_list = []
        for p in selected_posts:
            views = p.get('views', 0)
            er = calculate_er(p.get('likes',0), p.get('comments',0), p.get('reposts',0), views)
            er_list.append(er)
        avg_er = sum(er_list)/len(er_list) if er_list else 0
        deltas = None
    
    # Обновляем _er для постов (нужно для format_top_posts) - считаем один раз
    for p in selected_posts:
        if '_er' not in p:  # Кешируем ER, чтобы не пересчитывать
            views = p.get('views', 0)
            p['_er'] = calculate_er(p.get('likes',0), p.get('comments',0), p.get('reposts',0), views)

    blocks = [
        ("Постов", total_posts, "posts"),
        ("Просмотров", total_views, "views"),
        ("Лайков", total_likes, "likes"),
        ("Комментариев", total_comments, "comments"),
        ("Репостов", total_reposts, "reposts"),
        ("Средний ER", f"{avg_er:.2f}%", "avg_er"),
    ]

    metrics = []
    for label, value, metric_key in blocks[:-1]:
        delta_html = ""
        if deltas and metric_key in deltas:
            delta = deltas[metric_key]
            delta_html = format_delta(delta['absolute'], delta['percent'])
        
        metrics.append(f"""
        <div style='
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 18px 10px 10px 10px;
            display: flex; flex-direction:column; align-items:center;'>
            <div style='font-size:12px; color:#6b7280; margin-bottom: 7px;'>{label}</div>
            <div style='font-size:26px; font-weight:700; color:#111827;'>{format_metric(value)}</div>
            {delta_html}
        </div>
        """)

    # ER карточка с дельтой
    er_delta_html = ""
    if deltas and "avg_er" in deltas:
        delta = deltas["avg_er"]
        er_delta_html = format_delta(delta['absolute'], delta['percent'], is_light_bg=True)
    
    metrics.append(f"""
        <div style='
            background: linear-gradient(135deg, #059669 25%, #047857 100%);
            border-radius: 12px; padding: 18px 10px 10px 10px; color: #fff; display:flex; flex-direction:column; align-items:center;'>
            <div style='font-size:12px; opacity: 0.85; margin-bottom: 7px;'>Средний ER</div>
            <div style='font-size:26px; font-weight:700;'>{blocks[-1][1]}</div>
            {er_delta_html}
        </div>""")

    # Формируем заголовок
    if comparison_data:
        prev_start, prev_end = calculate_previous_period(start_date, end_date)
        header = f"""
        <h2 style="font-size:24px; font-weight:700; color:#111827; font-family:sans-serif; margin-bottom: 8px;">
            Саммари за период {start_date} — {end_date}
        </h2>
        <div style="font-size:14px; color:#6b7280; margin-bottom: 16px;">
            📊 Сравнение с предыдущим периодом: {prev_start} — {prev_end}
        </div>
        """
    else:
        header = f"""
        <h2 style="font-size:24px; font-weight:700; color:#111827; font-family:sans-serif;">
            Саммари за период {start_date} — {end_date}
        </h2>
        """
    
    return f"""
    <div style="margin: 0 auto; max-width:1200px;">
        {header}
        <div style="display: grid; grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); gap: 13px; margin-bottom: 35px;">
            {''.join(metrics)}
        </div>
    </div>"""


def render_stats():
    """Рендерит блок статистики"""
    stats_card = ui.card().classes('w-full').style(
        'background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 32px; max-width: 1200px; display: none;'
    )
    with stats_card:
        stats_container = ui.html('', sanitize=False).classes('w-full')
    
    return stats_card, stats_container

