"""
UI компонент: Блок графиков
"""
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
from nicegui import ui
from core.state import STATE
from core.analytics import agg_period, period_by_rus


def plot_stat_all(posts, start_date, end_date, period):
    """Генерирует графики для всех метрик"""
    df = pd.DataFrame(posts)
    if df.empty:
        return []
    df = agg_period(df, period)
    grouped = df.groupby('period').agg({
        'likes': 'sum',
        'comments': 'sum',
        'reposts': 'sum',
        'views': 'sum',
        'id': 'count'
    }).rename(columns={'id':'posts'}).reset_index()
    grouped = grouped.sort_values("period")
    er_values = []
    likes = grouped["likes"].tolist()
    comments = grouped["comments"].tolist()
    reposts = grouped["reposts"].tolist()
    views = grouped["views"].tolist()
    for i in range(len(grouped)):
        t_eng = likes[i] + comments[i] + reposts[i]
        er = t_eng / views[i] * 100 if views[i] > 0 else 0
        er_values.append(er)
    grouped['ER'] = er_values

    imgs = []
    colors = ['#3778bf', '#ffa600', '#43aa8b', '#590d22', '#1e88e5', '#e74c3c']
    fields = [
        ("likes", "Лайки", colors[0]),
        ("comments", "Комментарии", colors[1]),
        ("reposts", "Репосты", colors[2]),
        ("posts", "Посты", colors[3]),
        ("views", "Просмотры", colors[4]),
        ("ER", "Engagement Rate (%)", colors[5])
    ]

    for fld, lbl, clr in fields:
        fig, ax = plt.subplots(figsize=(7, 2.35))
        x = grouped["period"].astype(str).tolist()
        ys = grouped[fld].tolist()
        ax.plot(x, ys, marker='o', color=clr)
        ax.set_title(f"{lbl} по {period_by_rus(period)}", fontsize=13)
        ax.set_xlabel(period_by_rus(period))
        ax.set_ylabel(lbl)
        ax.grid(True, alpha=0.23)
        plt.xticks(rotation=30)
        plt.tight_layout()
        fn = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(fn.name, bbox_inches='tight', dpi=100)
        plt.close(fig)
        imgs.append(fn.name)
    return imgs


def render_graphs():
    """Рендерит блок графиков"""
    graphs_card = ui.card().classes('w-full').style(
        'background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 32px; max-width: 1200px; display: none;'
    )
    
    with graphs_card:
        ui.label('Графики и аналитика').classes('text-xl font-semibold mb-6').style('color: #111827;')
        
        with ui.row().classes('w-full items-end gap-4'):
            with ui.column().classes('flex-1'):
                ui.label('Период агрегации').style('font-size: 13px; color: #6b7280; margin-bottom: 8px; font-weight: 500;')
                aggr_combo = ui.select(
                    {7: 'Неделя', 30: 'Месяц', 90: 'Квартал'},
                    value=7
                ).classes('w-full').style('font-size: 15px;')
            btn_plot = ui.button('Показать графики', color='secondary').style(
                'background: #f3f4f6; color: #111827; font-weight: 600; padding: 12px 24px; border-radius: 8px; font-size: 15px; border: 1px solid #e5e7eb;'
            )
        
        plot_zone = ui.column().classes('w-full mt-6')
        
        def on_plot():
            if not STATE.posts:
                plot_zone.clear()
                with plot_zone:
                    ui.label("Пока нет данных. Получите статистику выше.").classes('text-red-600')
                return
            period_map = {7: 'week', 30: 'month', 90: 'quarter'}
            period = period_map.get(aggr_combo.value, 'week')
            start_date = STATE.last_fetch_params.get("start_date", (datetime.date.today().replace(year=datetime.date.today().year - 1)).strftime("%Y-%m-%d"))
            end_date = STATE.last_fetch_params.get("end_date", datetime.date.today().strftime("%Y-%m-%d"))
            files = plot_stat_all(STATE.posts, start_date, end_date, period)
            plot_zone.clear()
            if files:
                # Названия графиков для скачивания
                graph_names = [
                    "Лайки", "Комментарии", "Репосты", 
                    "Посты", "Просмотры", "Engagement_Rate"
                ]
                period_map = {7: 'week', 30: 'month', 90: 'quarter'}
                period = period_map.get(aggr_combo.value, 'week')
                period_rus = period_by_rus(period)
                
                with plot_zone:
                    # Создаем контейнер с grid-разметкой используя column с grid-стилями
                    grid_wrapper = ui.column().classes('w-full plots-grid').style('''
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 20px;
                        width: 100%;
                    ''')
                    # Добавляем каждое изображение в grid-контейнер с кнопкой скачивания
                    for idx, fn in enumerate(files):
                        with grid_wrapper:
                            # Контейнер для графика и кнопки
                            with ui.column().classes('w-full').style('position: relative;'):
                                # График
                                ui.image(fn).classes('w-full').style('border-radius: 8px; width: 100%; display: block;')
                                # Кнопка скачивания - создаем ссылку только при клике
                                graph_name = graph_names[idx] if idx < len(graph_names) else f"График_{idx+1}"
                                download_filename = f"{graph_name}_{period_rus}_{start_date}_{end_date}.png".replace(' ', '_').replace('/', '_')
                                
                                # Сохраняем параметры для функции скачивания
                                file_path = fn
                                file_name = download_filename
                                
                                # Создаем кнопку, которая создает ссылку для скачивания при клике
                                with ui.button('📥 Скачать PNG', icon='download').classes('mt-2 w-full').style('''
                                    background: #059669;
                                    color: white;
                                    border-radius: 6px;
                                    padding: 8px 16px;
                                    font-size: 13px;
                                    font-weight: 500;
                                ''') as btn:
                                    def download_file(file_path=file_path, file_name=file_name):
                                        # Создаем ссылку для скачивания только при клике
                                        download_link = ui.download(file_path, filename=file_name)
                                        # Триггерим скачивание
                                        download_link.run_method('click')
                                    btn.on('click', download_file)
            else:
                with plot_zone:
                    ui.label("Нет доступных графиков.").classes('text-red-600')
        btn_plot.on('click', on_plot)
    
    return graphs_card

