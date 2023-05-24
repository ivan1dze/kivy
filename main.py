from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from random import randint
from functools import partial
from datetime import datetime

class PongBall(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def move(self):
        self.pos = Vector(*self.velocity) + self.pos


class PongPaddle(Widget):
    score = NumericProperty(0)

    def __init__(self, **kwargs):
        super(PongPaddle, self).__init__(**kwargs)
        self.otskok_sound = SoundLoader.load('otskok.mp3')

    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            self.otskok_sound.play()
            vx, vy = ball.velocity
            offset = (ball.center_y - self.center_y) / (self.height / 2)
            bounced = Vector(-1 * vx, vy)
            vel = bounced * 1.4

            ball.velocity = vel.x, vel.y + offset


class PongGame(Widget):
    ball = ObjectProperty(None)
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)
    is_running = False
    vs_ai = True
    result = StringProperty('')
    start_time = NumericProperty(0)
    elapsed_time = NumericProperty(0)

    def __init__(self, **kwargs):
        super(PongGame, self).__init__(**kwargs)
        self.start_button = None
        self.mode_button = None
        self.white_sound = SoundLoader.load('chill.mp3')
        self.end_button = Button(text='Return to Main Menu', size_hint=(None, None), size=(250, 120))
        self.end_button.bind(on_press=self.return_to_main_menu)
        self.end_button.disabled = True
        self.end_button.opacity = 0

        self.move_paddle_event = None  # Event for moving paddles

    def serve_ball(self, vel=(6.5, 2)):
        self.ball.center = self.center
        self.ball.velocity = Vector(vel[0], vel[1]).rotate(randint(0, 360))

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
            self.serve_ball(vel=(4, 0))

        if self.ball.x > self.width:
            self.player1.score += 1
            self.serve_ball(vel=(-4, 0))

        if self.vs_ai:
            self.move_ai_paddle()

        if self.player1.score == 5:
            self.result = "Red Wins!"
            self.is_running = False
            self.end_button.disabled = False
            self.end_button.opacity = 1
            Clock.unschedule(self.update)
        elif self.player2.score == 5:
            self.result = "Blue Wins!"
            self.is_running = False
            self.end_button.disabled = False
            self.end_button.opacity = 1
            Clock.unschedule(self.update)

    def on_touch_move(self, touch):
        if self.vs_ai:
            if touch.x < self.width / 3:
                self.player1.center_y = touch.y
        else:
            if touch.x < self.width / 3:
                self.player1.center_y = touch.y
            elif touch.x > self.width - self.width / 3:
                self.player2.center_y = touch.y

    def return_to_main_menu(self, instance):
        self.is_running = False
        self.player1.score = 0
        self.player2.score = 0
        self.result = ''  # Clear the result
        self.remove_widget(self.end_button)
        self.start_button.disabled = False
        self.start_button.opacity = 1
        self.mode_button.disabled = False
        self.mode_button.opacity = 1
        Clock.unschedule(self.update)
        self.ball.velocity = (0, 0)
        self.ball.center = self.center
        self.serve_ball()  # Serve the ball for the next match
        self.start_time = 0
        self.elapsed_time = 0
    def start_game(self, instance):
        self.is_running = True
        instance.disabled = True
        instance.opacity = 0
        self.mode_button.disabled = True
        self.mode_button.opacity = 0
        self.add_widget(self.end_button)
        self.player1.score = 0
        self.player2.score = 0
        self.result = ''  # Clear the result
        self.end_button.disabled = True
        self.end_button.opacity = 0
        self.serve_ball()
        self.start_time = datetime.now().timestamp()

        if self.vs_ai:
            self.player2.center_y = self.center_y

        Clock.unschedule(self.update)  # Unscheduling previous updates
        Clock.schedule_interval(self.update, 1.0 / 60)  # Schedule the update again

        # Start moving paddles
        self.move_paddle_event = Clock.schedule_interval(partial(self.move_paddles), 1.0 / 60)

    def switch_mode(self, instance):
        self.vs_ai = not self.vs_ai
        instance.text = "AI Mode" if self.vs_ai else "2 Players Mode"

    def move_paddles(self, dt):
        if self.vs_ai:
            self.move_ai_paddle()

    def move_ai_paddle(self):
        if self.ball.center_y > self.player2.center_y:
            self.player2.center_y += min(5, self.ball.center_y - self.player2.center_y)
        elif self.ball.center_y < self.player2.center_y:
            self.player2.center_y -= min(5, self.player2.center_y - self.ball.center_y)


class PongApp(App):
    def build(self):
        game = PongGame()
        game.serve_ball()

        layout = BoxLayout(orientation='vertical', spacing=20, padding=(30, 0, 0, 0))

        game.start_button = Button(text='Start', size_hint=(None, None), size=(250, 120))
        game.start_button.bind(on_press=game.start_game)
        layout.add_widget(game.start_button)

        game.mode_button = Button(text='AI Mode', size_hint=(None, None), size=(250, 120))
        game.mode_button.bind(on_press=game.switch_mode)
        layout.add_widget(game.mode_button)

        layout.add_widget(Widget(size_hint=(1, 1)))
        game.add_widget(layout)

        # Play the chill.mp3 song
        game.white_sound.loop = True
        game.white_sound.volume = 0.08
        game.white_sound.play()

        return game


if __name__ == '__main__':
    PongApp().run()