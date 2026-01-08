"""
UI компонент: Блок топ-постов
"""
import datetime
from nicegui import ui
from core.state import STATE
from core.services import extract_channel_username
from core.analytics import calculate_er, format_metric

# Словарь функций для сортировки по метрикам
SORT_KEYS = {
    'er': lambda p: p.get('_er', 0),
    'views': lambda p: p.get('views', 0),
    'likes': lambda p: p.get('likes', 0),
    'comments': lambda p: p.get('comments', 0),
    'reposts': lambda p: p.get('reposts', 0),
}


def format_top_posts(posts, channel='', mode='er'):
    """
    Форматирует топ-5 постов по выбранной метрике.
    
    Args:
        posts: Список постов
        channel: Имя канала
        mode: Режим сортировки ('er', 'views', 'likes', 'comments', 'reposts')
    
    Returns:
        str: HTML строка с топ-постами
    """
    if not posts:
        return "<div style='color:#6b7280; padding: 20px; text-align: center;'>Нет постов для отображения</div>"
    
    # Фильтруем посты с просмотрами > 50 (только для ER, для других метрик можно убрать)
    if mode == 'er':
        filtered_posts = [p for p in posts if p.get('views', 0) > 50]
    else:
        filtered_posts = posts.copy() if posts else []
    
    if not filtered_posts:
        return "<div style='color:#6b7280; padding: 20px; text-align: center;'>Нет постов для отображения</div>"
    
    # Убеждаемся, что ER рассчитан для всех постов (если нужно)
    for p in filtered_posts:
        if '_er' not in p:
            views = p.get('views', 0)
            p['_er'] = calculate_er(
                p.get('likes', 0),
                p.get('comments', 0),
                p.get('reposts', 0),
                views
            )
    
    # Сортируем по выбранной метрике
    sort_key = SORT_KEYS.get(mode, SORT_KEYS['er'])
    top_sorted = sorted(filtered_posts, key=sort_key, reverse=True)[:5]
    
    if not top_sorted:
        return "<div style='color:#6b7280; padding: 20px; text-align: center;'>Нет постов для отображения</div>"

    rows = """
    <div style="display:flex; flex-direction:column; gap:12px; width:100%;">
    """

    for i, p in enumerate(top_sorted, start=1):
        # Обрабатываем текст поста
        post_title = p.get('title', '')
        if post_title == "(без текста)" or not post_title:
            text_preview = "Пост не содержит текст. Вероятно медиа-контент"
        else:
            text_preview = (post_title[:35] + '…') if len(post_title) > 35 else post_title
        
        channel_username = extract_channel_username(channel) if channel else ''
        link = f"https://t.me/{channel_username}/{p['id']}" if channel_username else "#"
        
        # Получаем значение выбранной метрики для отображения
        if mode == 'er':
            metric_value = f"{p.get('_er', 0):.2f}%"
            metric_label = "ER"
        elif mode == 'views':
            metric_value = format_metric(p.get('views', 0))
            metric_label = "Просмотры"
        elif mode == 'likes':
            metric_value = format_metric(p.get('likes', 0))
            metric_label = "Лайки"
        elif mode == 'comments':
            metric_value = format_metric(p.get('comments', 0))
            metric_label = "Комментарии"
        elif mode == 'reposts':
            metric_value = format_metric(p.get('reposts', 0))
            metric_label = "Репосты"
        else:
            metric_value = f"{p.get('_er', 0):.2f}%"
            metric_label = "ER"

        rows += f"""
        <div style="
            display:grid;
            grid-template-columns:
                40px
                minmax(100px, 1fr)
                200px
                140px
                40px;
            gap:16px;
            align-items:center;
            background:#ffffff;
            border:1px solid #e5e7eb;
            border-radius:12px;
            padding:14px 18px;
        ">
            <!-- номер -->
            <div style="font-size:20px; font-weight:700; color:#059669;">
                {i}
            </div>

            <!-- текст -->
            <div style="font-size:14px; font-weight:500; color:#111827; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                {text_preview}
            </div>

            <!-- метрики -->
            <div style="display:flex; gap:18px; font-size:13px; color:#374151;">
                <div><b>{p.get('views', 0)}</b> 👁</div>
                <div><b>{p.get('likes', 0)}</b> 👍</div>
                <div><b>{p.get('comments', 0)}</b> 💬</div>
                <div><b>{p.get('reposts', 0)}</b> 🔁</div>
            </div>

            <!-- Выбранная метрика -->
            <div style="display:flex; font-size:16px; font-weight:700; color:#059669; text-align:center;">
                {metric_label}: {metric_value}
            </div>

            <!-- ссылка -->
            <a href="{link}" target="_blank"
            style="display:flex; text-decoration:none; font-size:18px;">
                🔗
            </a>
        </div>
        """

    rows += "</div>"
    return rows


# Глобальные переменные для хранения компонентов
_metric_buttons = {}
_top_posts_container = None


def update_top_posts(mode: str):
    """Обновляет отображение топ-постов по выбранной метрике"""
    global _top_posts_container, _metric_buttons
    
    # Проверяем наличие данных
    if not STATE.posts:
        if _top_posts_container:
            _top_posts_container.content = "<div style='color:#6b7280; padding: 20px; text-align: center;'>Нет данных для отображения</div>"
        return
    
    # Проверяем наличие контейнера
    if not _top_posts_container:
        # Контейнер еще не инициализирован, пропускаем обновление
        return
    
    start_date = STATE.last_fetch_params.get("start_date", "")
    end_date = STATE.last_fetch_params.get("end_date", "")
    if not start_date or not end_date:
        _top_posts_container.content = "<div style='color:#6b7280; padding: 20px; text-align: center;'>Период не выбран</div>"
        return
    
    try:
        # Фильтруем посты по периоду
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        selected_posts = [
            post for post in STATE.posts
            if start <= datetime.datetime.strptime(post['date'], "%Y-%m-%d").date() <= end
        ]
        
        # Убеждаемся, что ER рассчитан для всех постов (кешируем)
        for p in selected_posts:
            if '_er' not in p:
                views = p.get('views', 0)
                p['_er'] = calculate_er(
                    p.get('likes', 0),
                    p.get('comments', 0),
                    p.get('reposts', 0),
                    views
                )
        
        # Обновляем HTML с топ-постами
        html = format_top_posts(selected_posts, STATE.last_channel, mode)
        _top_posts_container.content = html
        
        # Обновляем стили кнопок
        for m, btn in _metric_buttons.items():
            if m == mode:
                btn.style('background: #111827; color: #fff; border-color: #111827;')
            else:
                btn.style('background: #fff; color: #111827; border: 1px solid #e5e7eb;')
    except Exception as e:
        # В случае ошибки показываем сообщение
        if _top_posts_container:
            _top_posts_container.content = f"<div style='color:#dc2626; padding: 20px; text-align: center;'>Ошибка при обновлении: {str(e)}</div>"


def render_top_posts():
    """Рендерит блок топ-постов"""
    global _metric_buttons, _top_posts_container
    
    # Сбрасываем глобальные переменные для чистого состояния
    _metric_buttons = {}
    _top_posts_container = None
    
    top_posts_card = ui.card().classes('w-full').style(
        'background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 32px; max-width: 1200px; display: none;'
    )
    
    with top_posts_card:
        ui.label('Топ-5 постов').classes('text-xl font-semibold mb-4').style('color: #111827;')
        ui.label('Выберите метрику для сортировки').classes('text-sm mb-4').style('color: #6b7280;')
        
        # Контейнер для кнопок переключения метрик
        metric_buttons_container = ui.row().classes('w-full gap-2 mb-4').style('flex-wrap: wrap;')
        
        # Создаем кнопки для каждой метрики
        metrics_config = [
            ('er', 'ER'),
            ('views', 'Просмотры'),
            ('likes', 'Лайки'),
            ('comments', 'Комментарии'),
            ('reposts', 'Репосты')
        ]
        
        for mode, label in metrics_config:
            with metric_buttons_container:
                btn = ui.button(label).classes('px-4 py-2').style(
                    'border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; color: #111827; font-size: 14px; font-weight: 500;'
                )
                if mode == 'er':
                    btn.style('background: #111827; color: #fff; border-color: #111827;')
                _metric_buttons[mode] = btn
        
        # Контейнер для топ-постов - инициализируем с пустым содержимым
        _top_posts_container = ui.html('', sanitize=False).classes('w-full')
    
    # Привязываем обработчики к кнопкам
    def make_handler(m):
        return lambda: update_top_posts(m)
    
    for mode, btn in _metric_buttons.items():
        btn.on('click', make_handler(mode))
    
    return top_posts_card

