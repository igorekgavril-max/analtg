"""
UI компонент: Блок инсайтов о времени публикаций
"""
import datetime
from nicegui import ui
from core.state import STATE
from core.posting_insights import analyze_posting_times


def format_percent_diff(percent_diff: float, metric_type: str) -> str:
    """Форматирует разницу в процентах"""
    if metric_type == 'views':
        if percent_diff > 0:
            return f"на {abs(percent_diff):.1f}% больше просмотров"
        else:
            return f"на {abs(percent_diff):.1f}% меньше просмотров"
    else:  # er
        if percent_diff > 0:
            return f"на {abs(percent_diff):.1f}% выше вовлечённости"
        else:
            return f"на {abs(percent_diff):.1f}% ниже вовлечённости"


def render_posting_insights():
    """Рендерит блок инсайтов о времени публикаций"""
    insights_card = ui.card().classes('w-full').style(
        'background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 32px; max-width: 1200px; display: none;'
    )
    
    with insights_card:
        # Заголовок
        ui.label('Ценные инсайты за бесплатно').classes('text-2xl font-bold mb-2').style('color: #111827;')
        ui.label('Рекомендации на основе фактической статистики канала').classes('text-sm mb-6').style('color: #6b7280;')
        
        # Контейнер для инсайтов
        insights_container = ui.html('', sanitize=False).classes('w-full')
    
    return insights_card, insights_container


def update_posting_insights(insights_container):
    """Обновляет отображение инсайтов"""
    if not STATE.posts or not insights_container:
        return
    
    start_date = STATE.last_fetch_params.get("start_date", "")
    end_date = STATE.last_fetch_params.get("end_date", "")
    if not start_date or not end_date:
        return
    
    # Фильтруем посты по периоду
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    selected_posts = [
        post for post in STATE.posts
        if start <= datetime.datetime.strptime(post['date'], "%Y-%m-%d").date() <= end
    ]
    
    # Анализируем время публикаций
    analysis = analyze_posting_times(selected_posts)
    
    # CSS стили
    css_styles = """
    <style>
        .insights-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .insights-section {
            margin-bottom: 40px;
        }
        .insights-title {
            font-size: 18px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 20px;
        }
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }
        .insight-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }
        .insight-metric-label {
            font-size: 12px;
            font-weight: 500;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }
        .insight-main-value {
            font-size: 18px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 8px;
            line-height: 1.4;
        }
        .insight-diff {
            font-size: 14px;
            font-weight: 600;
            color: #059669;
            margin-bottom: 12px;
        }
        .insight-meta {
            font-size: 12px;
            color: #6b7280;
            margin-top: auto;
            padding-top: 12px;
            border-top: 1px solid #f3f4f6;
        }
        .insights-negative {
            margin-top: 40px;
        }
        .insufficient-data {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .insufficient-title {
            font-size: 16px;
            font-weight: 600;
            color: #111827;
            margin-bottom: 8px;
        }
        .insufficient-text {
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 8px;
        }
        .insufficient-meta {
            font-size: 12px;
            color: #9ca3af;
        }
        @media (max-width: 768px) {
            .insights-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """
    
    if not analysis.get('has_data', False):
        message = analysis.get('message', 'Нет данных для анализа')
        if analysis.get('insufficient_data', False):
            html = f"""
            {css_styles}
            <div class="insights-container">
                <div class="insufficient-data">
                    <div class="insufficient-title">Недостаточно данных</div>
                    <div class="insufficient-text">{message}</div>
                    <div class="insufficient-meta">
                        Постов: {analysis.get('posts_count', 0)} | 
                        Период: {analysis.get('days_range', 0)} дней
                    </div>
                </div>
            </div>
            """
        else:
            html = f"""
            {css_styles}
            <div class="insights-container">
                <div class="insufficient-data">
                    <div class="insufficient-text">{message}</div>
                </div>
            </div>
            """
        insights_container.content = html
        return
    
    # Формируем HTML с инсайтами
    sections = []
    
    # 1. Блок "Лучшее время публикаций"
    best_cards = []
    
    # Лучшее время для охвата
    if analysis.get('best_views'):
        best_views = analysis['best_views'][0]
        percent_diff = best_views['percent_diff']
        diff_text = format_percent_diff(percent_diff, 'views')
        
        best_cards.append(f"""
        <div class="insight-card">
            <div class="insight-metric-label">Для просмотров</div>
            <div class="insight-main-value">{best_views['day']}, {best_views['time_range']}</div>
            <div class="insight-diff">{diff_text}</div>
            <div class="insight-meta">
                Среднее: {best_views['value']:.0f} просмотров · Постов: {best_views['posts_count']}
            </div>
        </div>
        """)
    
    # Лучшее время для вовлечённости
    if analysis.get('best_er'):
        best_er = analysis['best_er'][0]
        percent_diff = best_er['percent_diff']
        diff_text = format_percent_diff(percent_diff, 'er')
        
        best_cards.append(f"""
        <div class="insight-card">
            <div class="insight-metric-label">Для ER (вовлечённости)</div>
            <div class="insight-main-value">{best_er['day']}, {best_er['time_range']}</div>
            <div class="insight-diff">{diff_text}</div>
            <div class="insight-meta">
                Средний ER: {best_er['value']:.2f}% · Постов: {best_er['posts_count']}
            </div>
        </div>
        """)
    
    if best_cards:
        sections.append(f"""
        <section class="insights-section">
            <div class="insights-title">Лучшее время публикаций</div>
            <div class="insights-grid">
                {''.join(best_cards)}
            </div>
        </section>
        """)
    
    # 2. Блок "Когда лучше не публиковать контент"
    negative_cards = []
    
    if analysis.get('worst_views'):
        worst_views = analysis['worst_views'][0]
        negative_cards.append(f"""
        <div class="insight-card">
            <div class="insight-metric-label">Минимальный охват</div>
            <div class="insight-main-value">{worst_views['day']}, {worst_views['time_range']}</div>
            <div class="insight-diff" style="color: #6b7280;">Ниже среднего</div>
            <div class="insight-meta">
                Среднее: {worst_views['value']:.0f} просмотров · Постов: {worst_views.get('posts_count', 0)}
            </div>
        </div>
        """)
    
    if analysis.get('worst_er'):
        worst_er = analysis['worst_er'][0]
        negative_cards.append(f"""
        <div class="insight-card">
            <div class="insight-metric-label">Минимальная ER</div>
            <div class="insight-main-value">{worst_er['day']}, {worst_er['time_range']}</div>
            <div class="insight-diff" style="color: #6b7280;">Ниже среднего</div>
            <div class="insight-meta">
                Средний ER: {worst_er['value']:.2f}% · Постов: {worst_er.get('posts_count', 0)}
            </div>
        </div>
        """)
    
    if negative_cards:
        sections.append(f"""
        <section class="insights-section insights-negative">
            <div class="insights-title">Когда лучше не публиковать контент</div>
            <div class="insights-grid">
                {''.join(negative_cards)}
            </div>
        </section>
        """)
    
    # Объединяем все части
    html = f"""
    {css_styles}
    <div class="insights-container">
        {''.join(sections)}
    </div>
    """
    
    insights_container.content = html

