import os
import logging

from kivy.utils import platform


class LogConfig:
    def __init__(self):
        self.filename = 'game.log'
        self.log_folder = os.path.join(os.getenv('EXTERNAL_STORAGE'),
                                       'kivy') if platform == 'android' else os.path.join(
            os.path.expanduser('~'), '.kivy')
        self.log_file = os.path.join(self.log_folder, self.filename)

    def configurate_log(self):
        # создаем папку если не создана
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)

        logger = logging.getLogger('game')
        logger.setLevel(logging.DEBUG)

        # создаем хендлер и ставим для его уровень
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)

        # формат для логгинга
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # добавляем хендлер в логгер
        logger.addHandler(file_handler)
        return logger
