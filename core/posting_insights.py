"""
Модуль для анализа лучшего времени публикаций
"""
import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from core.analytics import calculate_er


def analyze_posting_times(posts: List[Dict]) -> Dict:
    """
    Анализирует посты по времени публикации и возвращает рекомендации.
    
    Args:
        posts: Список постов с полями 'date', 'views', 'likes', 'comments', 'reposts'
    
    Returns:
        dict: Словарь с рекомендациями по времени публикации
    """
    if not posts:
        return {
            'has_data': False,
            'message': 'Нет данных для анализа'
        }
    
    # Проверка достаточности данных
    if len(posts) < 10:
        # Проверяем диапазон дат
        dates = []
        for p in posts:
            try:
                date_val = datetime.datetime.strptime(p['date'], "%Y-%m-%d").date()
                dates.append(date_val)
            except (ValueError, KeyError):
                continue
        
        if dates:
            date_range = (max(dates) - min(dates)).days
            if date_range < 14:
                return {
                    'has_data': False,
                    'insufficient_data': True,
                    'message': 'Недостаточно данных для точных рекомендаций. Рекомендуется период от 15 дней.',
                    'posts_count': len(posts),
                    'days_range': date_range
                }
    
    # Группируем по дням недели и часам
    # День недели: 0 = понедельник, 6 = воскресенье
    # Час: 0-23
    
    # Структура: day_hour -> список постов
    day_hour_posts = defaultdict(list)
    
    # Структура для агрегации метрик
    day_hour_metrics = defaultdict(lambda: {
        'views': [],
        'er': [],
        'posts_count': 0
    })
    
    for post in posts:
        try:
            # Получаем дату и время публикации
            if 'datetime' in post and isinstance(post['datetime'], datetime.datetime):
                post_date = post['datetime']
            elif 'date' in post:
                # Fallback: парсим дату, если datetime нет
                try:
                    post_date = datetime.datetime.strptime(post['date'], "%Y-%m-%d")
                except (ValueError, TypeError):
                    continue
            else:
                continue
            
            day_of_week = post_date.weekday()  # 0 = понедельник
            hour = post_date.hour
            
            views = post.get('views', 0)
            likes = post.get('likes', 0)
            comments = post.get('comments', 0)
            reposts = post.get('reposts', 0)
            
            # Рассчитываем ER
            er = calculate_er(likes, comments, reposts, views) if views > 0 else 0
            
            # Сохраняем метрики
            day_hour_metrics[(day_of_week, hour)]['views'].append(views)
            day_hour_metrics[(day_of_week, hour)]['er'].append(er)
            day_hour_metrics[(day_of_week, hour)]['posts_count'] += 1
            
            day_hour_posts[(day_of_week, hour)].append(post)
        except (ValueError, KeyError):
            continue
    
    if not day_hour_metrics:
        return {
            'has_data': False,
            'message': 'Не удалось проанализировать данные'
        }
    
    # Рассчитываем средние значения для каждого временного слота
    slot_stats = {}
    for (day, hour), metrics in day_hour_metrics.items():
        if metrics['posts_count'] > 0:
            avg_views = sum(metrics['views']) / len(metrics['views'])
            avg_er = sum(metrics['er']) / len(metrics['er']) if metrics['er'] else 0
            median_views = sorted(metrics['views'])[len(metrics['views']) // 2] if metrics['views'] else 0
            
            # Стабильность (стандартное отклонение)
            if len(metrics['views']) > 1:
                mean_views = avg_views
                variance = sum((x - mean_views) ** 2 for x in metrics['views']) / len(metrics['views'])
                std_views = variance ** 0.5
                stability = 'stable' if std_views < mean_views * 0.3 else 'unstable'
            else:
                stability = 'insufficient'
            
            slot_stats[(day, hour)] = {
                'avg_views': avg_views,
                'median_views': median_views,
                'avg_er': avg_er,
                'posts_count': metrics['posts_count'],
                'stability': stability
            }
    
    # Общие средние значения
    all_views = [v for metrics in day_hour_metrics.values() for v in metrics['views']]
    all_er = [er for metrics in day_hour_metrics.values() for er in metrics['er']]
    
    overall_avg_views = sum(all_views) / len(all_views) if all_views else 0
    overall_avg_er = sum(all_er) / len(all_er) if all_er else 0
    
    # Находим лучшие и худшие слоты для охвата
    best_views_slots = sorted(
        slot_stats.items(),
        key=lambda x: x[1]['avg_views'],
        reverse=True
    )[:3]  # Топ-3
    
    worst_views_slots = sorted(
        slot_stats.items(),
        key=lambda x: x[1]['avg_views']
    )[:3]  # Худшие 3
    
    # Находим лучшие и худшие слоты для ER
    best_er_slots = sorted(
        slot_stats.items(),
        key=lambda x: x[1]['avg_er'],
        reverse=True
    )[:3]  # Топ-3
    
    worst_er_slots = sorted(
        slot_stats.items(),
        key=lambda x: x[1]['avg_er']
    )[:3]  # Худшие 3
    
    # Форматируем результаты
    def format_slot(day: int, hour: int) -> Dict:
        """Форматирует временной слот для отображения"""
        day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        day_name = day_names[day]
        
        # Формируем временной диапазон (час ± 1)
        hour_start = max(0, hour - 1)
        hour_end = min(23, hour + 1)
        
        time_range = f"{hour_start:02d}:00–{hour_end + 1:02d}:00"
        
        return {
            'day': day_name,
            'day_num': day,
            'hour': hour,
            'time_range': time_range
        }
    
    def format_recommendations(slots: List[Tuple], metric_type: str) -> List[Dict]:
        """Форматирует рекомендации"""
        recommendations = []
        for (day, hour), stats in slots:
            slot_info = format_slot(day, hour)
            if metric_type == 'views':
                value = stats['avg_views']
                overall = overall_avg_views
                metric_name = 'просмотров'
            else:  # er
                value = stats['avg_er']
                overall = overall_avg_er
                metric_name = 'ER'
            
            if overall > 0:
                percent_diff = ((value - overall) / overall) * 100
            else:
                percent_diff = 0
            
            recommendations.append({
                **slot_info,
                'value': value,
                'overall': overall,
                'percent_diff': percent_diff,
                'posts_count': stats['posts_count'],
                'stability': stats['stability']
            })
        
        return recommendations
    
    # Проверяем конфликт целей
    best_views_day_hour = best_views_slots[0][0] if best_views_slots else None
    best_er_day_hour = best_er_slots[0][0] if best_er_slots else None
    
    has_conflict = best_views_day_hour != best_er_day_hour
    
    result = {
        'has_data': True,
        'overall_avg_views': overall_avg_views,
        'overall_avg_er': overall_avg_er,
        'best_views': format_recommendations(best_views_slots, 'views'),
        'worst_views': format_recommendations(worst_views_slots, 'views'),
        'best_er': format_recommendations(best_er_slots, 'er'),
        'worst_er': format_recommendations(worst_er_slots, 'er'),
        'has_conflict': has_conflict,
        'total_posts': len(posts),
        'total_slots': len(slot_stats)
    }
    
    if has_conflict and best_views_day_hour and best_er_day_hour:
        best_views_info = format_slot(*best_views_day_hour)
        best_er_info = format_slot(*best_er_day_hour)
        result['conflict_info'] = {
            'views': best_views_info,
            'er': best_er_info
        }
    
    return result

