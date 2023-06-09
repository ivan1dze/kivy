import os
from random import randint
from functools import partial
from datetime import datetime

from config.log_config import LogConfig
from config.pong_enum import PathEnum, ButtonNamesEnum

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.core.audio import SoundLoader

log_config = LogConfig()
logger = log_config.configurate_log()


class PongBall(Widget):
    balls_list = os.listdir(PathEnum.BALLS_PATH_ENUM)
    ball_image = StringProperty(PathEnum.BALLS_PATH_ENUM + '/' + balls_list[0])

    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def move(self):
        self.pos = Vector(*self.velocity) + self.pos


class PongPaddle(Widget):
    score = NumericProperty(0)

    def __init__(self, **kwargs):
        super(PongPaddle, self).__init__(**kwargs)
        self.bounce_sound = SoundLoader.load(PathEnum.BOUNCE_SOUND_PATH_ENUM)

    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            self.bounce_sound.play()
            vx, vy = ball.velocity
            offset = (ball.center_y - self.center_y) / (self.height / 2)
            bounced = Vector(-1 * vx, vy)
            vel = bounced * 1.15
            ball.velocity = vel.x, vel.y + offset
            logger.debug('Game: Ball bounced')


class PongGame(Widget):
    ball = ObjectProperty(None)
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)
    is_running = False
    vs_ai = True
    result = StringProperty('')
    start_time = NumericProperty(0)
    elapsed_time = NumericProperty(0)
    backgrounds_list = os.listdir(PathEnum.BACKGROUNDS_PATH_ENUM)
    background_image = StringProperty(PathEnum.BACKGROUNDS_PATH_ENUM + '/' + backgrounds_list[0])

    def __init__(self, **kwargs):
        super(PongGame, self).__init__(**kwargs)
        self.start_button = None
        self.mode_button = None
        self.background_image_button = None
        self.ball_button = None
        self.white_sound = SoundLoader.load(PathEnum.WHITE_SOUND_PATH_ENUM)
        self.move_paddle_event = None  # Event for moving paddles

    def change_background(self, instance):
        logger.debug('UI: Background changed')
        for i in range(len(self.backgrounds_list)):
            if PathEnum.BACKGROUNDS_PATH_ENUM + '/' + self.backgrounds_list[i] == self.background_image:
                if i + 1 == len(self.backgrounds_list):
                    self.background_image = PathEnum.BACKGROUNDS_PATH_ENUM + '/' + self.backgrounds_list[0]
                    break
                else:
                    self.background_image = PathEnum.BACKGROUNDS_PATH_ENUM + '/' + self.backgrounds_list[i + 1]
                    break

    def change_ball(self, instance):
        logger.debug('UI: Ball changed')
        for i in range(len(self.ball.balls_list)):
            if PathEnum.BALLS_PATH_ENUM + '/' + self.ball.balls_list[i] == self.ball.ball_image:
                if i + 1 == len(self.ball.balls_list):
                    self.ball.ball_image = PathEnum.BALLS_PATH_ENUM + '/' + self.ball.balls_list[0]
                    break
                else:
                    self.ball.ball_image = PathEnum.BALLS_PATH_ENUM + '/' + self.ball.balls_list[i + 1]
                    break

    def serve_ball(self, vel=(8, 2)):
        self.ball.center = self.center
        angle = randint(10, 60)  # угол 10 и 240 градусов
        self.ball.velocity = Vector(vel[0], vel[1]).rotate(angle)
        logger.debug('Game: Ball Start')

    def update(self, dt):
        if not self.is_running:
            return

        current_time = datetime.now().timestamp()
        self.elapsed_time = current_time - self.start_time
        self.ball.move()
        self.player1.bounce_ball(self.ball)
        self.player2.bounce_ball(self.ball)

        if (self.ball.y < 0) or (self.ball.top > self.height):
            self.ball.velocity_y *= -1

        if self.ball.x < self.x:
            self.player2.score += 1
            self.serve_ball(vel=(8, 0))

        if self.ball.x > self.width:
            self.player1.score += 1
            self.serve_ball(vel=(-8, 0))

        if self.vs_ai:
            self.move_ai_paddle()

        self.check_results()

    def check_results(self):
        if self.player1.score == 5 or self.player2.score == 5:
            self.is_running = False
            Clock.unschedule(self.update)
            self.show_results()

    def on_touch_move(self, touch):
        if self.vs_ai:
            if touch.x < self.width / 3:
                self.player1.center_y = touch.y
        else:
            if touch.x < self.width / 3:
                self.player1.center_y = touch.y
            elif touch.x > self.width - self.width / 3:
                self.player2.center_y = touch.y

    def show_results(self):
        logger.debug('UI: Pop up created')
        if self.player1.score > self.player2.score:
            winner = "Red Wins!"
        else:
            winner = "Blue Wins!"

        logger.debug(f'Game: {winner}')

        score_message = "Red Score: {}\nBlue Score: {}\nElapsed Time: {:.2f} seconds".format(
            self.player1.score, self.player2.score, self.elapsed_time)

        winner_label = Label(text=winner, font_size='40sp')
        score_label = Label(text=score_message)

        # Создаем BoxLayout для размещения виджетов Label
        layout = BoxLayout(orientation='vertical', padding=(0, 30))
        layout.add_widget(winner_label)
        layout.add_widget(score_label)

        # Создаем Popup с новым контентом
        message_box = Popup(title="Game Over", content=layout, size_hint=(None, None), size=(700, 700))
        message_box.open()

        self.return_to_main_menu()

    def return_to_main_menu(self):
        self.is_running = False
        self.enable_menu()
        self.reset_score()
        Clock.unschedule(self.update)
        self.ball.velocity = (0, 0)
        self.ball.center = self.center
        self.serve_ball()  # Serve the ball for the next match
        self.start_time = 0
        self.elapsed_time = 0
        logger.debug('Game: Returned to main menu')

    def start_game(self, instance):
        self.is_running = True
        self.disable_menu()
        self.reset_score()
        self.serve_ball()
        self.start_time = datetime.now().timestamp()
        logger.debug('Game: Match started')

        if self.vs_ai:
            self.player2.center_y = self.center_y

        Clock.unschedule(self.update)  # Unscheduling previous updates
        Clock.schedule_interval(self.update, 1.0 / 60)  # Schedule the update again

        # Start moving paddles
        self.move_paddle_event = Clock.schedule_interval(partial(self.move_paddles), 1.0 / 60)

    def reset_score(self):
        self.player1.score = 0
        self.player2.score = 0

    def switch_mode(self, instance):
        self.vs_ai = not self.vs_ai
        instance.text = "AI Mode" if self.vs_ai else "2 Players Mode"
        logger.debug('Game: Mode switched to AI Mode' if self.vs_ai else 'Game: Mode switched to 2 Players')

    def move_paddles(self, dt):
        if self.vs_ai:
            self.move_ai_paddle()

    def move_ai_paddle(self):
        if self.ball.center_y > self.player2.center_y:
            self.player2.center_y += min(4.5, self.ball.center_y - self.player2.center_y)
        elif self.ball.center_y < self.player2.center_y:
            self.player2.center_y -= min(4.5, self.player2.center_y - self.ball.center_y)

    def disable_menu(self):
        self.start_button.disabled = True
        self.start_button.opacity = 0
        self.mode_button.disabled = True
        self.mode_button.opacity = 0
        self.background_image_button.disabled = True
        self.background_image_button.opacity = 0
        self.ball_button.disabled = True
        self.ball_button.opacity = 0

    def enable_menu(self):
        self.start_button.disabled = False
        self.start_button.opacity = 1
        self.mode_button.disabled = False
        self.mode_button.opacity = 1
        self.background_image_button.disabled = False
        self.background_image_button.opacity = 1
        self.ball_button.disabled = False
        self.ball_button.opacity = 1


class PongApp(App):

    def build(self):
        game = PongGame()
        layout = BoxLayout(orientation='vertical', spacing=20, padding=(30, 0, 0, 0))

        game.start_button = Button(text=ButtonNamesEnum.START_BTN_ENUM, size_hint=(None, None), size=(290, 100))
        game.start_button.bind(on_press=game.start_game)
        layout.add_widget(game.start_button)

        game.mode_button = Button(text=ButtonNamesEnum.GAME_MODE_BTN_ENUM, size_hint=(None, None),
                                  size=(290, 100))
        game.mode_button.bind(on_press=game.switch_mode)
        layout.add_widget(game.mode_button)

        game.background_image_button = Button(text=ButtonNamesEnum.CHANGE_TABLE_BTN_ENUM, size_hint=(None, None),
                                              size=(290, 100))
        game.background_image_button.bind(on_press=game.change_background)
        layout.add_widget(game.background_image_button)

        game.ball_button = Button(text=ButtonNamesEnum.CHANGE_BALL_BTN_ENUM, size_hint=(None, None),
                                  size=(290, 100))
        game.ball_button.bind(on_press=game.change_ball)
        layout.add_widget(game.ball_button)

        layout.add_widget(Widget(size_hint=(1, 1)))
        game.add_widget(layout)

        # Play the chill.mp3 song
        game.white_sound.loop = True
        game.white_sound.volume = 0.08
        game.white_sound.play()

        logger.debug('Game: Game started')
        return game


if __name__ == '__main__':
    PongApp().run()
