"""
UI компонент: Footer с Telegram виджетом
"""
from nicegui import ui


def render_footer():
    """Рендерит footer с Telegram виджетом"""
    with ui.column().classes('w-full items-center mt-8').style('margin-top: 60px; padding: 40px 20px; border-top: 1px solid #e5e7eb;'):
        # Создаем контейнер для виджета с уникальным ID
        widget_container_id = 'telegram-widget-container'
        ui.html(f'''
        <div id="{widget_container_id}" style="margin-top:40px; width: 100%; max-width: 800px;">
        </div>
        ''', sanitize=False).classes('w-full').style('max-width: 800px;')
        
        # Добавляем скрипт виджета в body, который будет вставлен в контейнер footer
        ui.add_body_html(f'''
        <script>
            (function() {{
                function initTelegramWidget() {{
                    var container = document.getElementById('{widget_container_id}');
                    if (container && !container.querySelector('script[src*="telegram-widget"]')) {{
                        var script = document.createElement('script');
                        script.async = true;
                        script.src = 'https://telegram.org/js/telegram-widget.js?22';
                        script.setAttribute('data-telegram-post', 'tech_igor/327');
                        script.setAttribute('data-width', '100%');
                        script.setAttribute('data-userpic', 'true');
                        script.setAttribute('data-color', '#059669');
                        container.appendChild(script);
                    }}
                }}
                
                // Ждем загрузки DOM
                if (document.readyState === 'loading') {{
                    document.addEventListener('DOMContentLoaded', initTelegramWidget);
                }} else {{
                    // Если DOM уже загружен, ждем немного для гарантии, что контейнер создан
                    setTimeout(initTelegramWidget, 100);
                }}
            }})();
        </script>
        ''')

