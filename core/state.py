from dataclasses import dataclass, field


@dataclass
class AppState:
    """Состояние приложения"""
    channel: str = ''
    start_date: str = ''
    end_date: str = ''
    compare_enabled: bool = False

    posts: list = field(default_factory=list)
    previous_posts: list = field(default_factory=list)
    
    last_fetch_params: dict = field(default_factory=dict)
    last_channel: str = ''

    def reset(self):
        """Сброс данных"""
        self.posts.clear()
        self.previous_posts.clear()
        self.last_fetch_params.clear()
        self.last_channel = ''


# Глобальный экземпляр состояния
STATE = AppState()

