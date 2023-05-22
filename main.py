from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.vector import Vector
from kivy.clock import Clock
from random import randint
from kivy.uix.relativelayout import RelativeLayout


class PongPaddle(Widget):
    score = NumericProperty(0)

    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            vx, vy = ball.velocity
            offset = (ball.center_y - self.center_y) / (self.height / 2)
            bounced = Vector(-1 * vx, vy)
            vel = bounced * 1.1

            ball.velocity = vel.x, vel.y + offset

class PongBall(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def move(self):
        self.pos = Vector(*self.velocity) + self.pos

class PongGame(Widget):
    ball = ObjectProperty(None)
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)
    is_running = False
    vs_ai = True

    def serve_ball(self, vel=(4, 0)):
        self.ball.center = self.center
        self.ball.velocity = Vector(vel[0], vel[1]).rotate(randint(0, 360))

    def update(self, dt):
        if not self.is_running:
            return

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

    def on_touch_move(self, touch):
        if touch.x < self.width / 3:
            self.player1.center_y = touch.y
        elif touch.x > self.width - self.width / 3:
            # Exclude AI paddle from touch input
            if not self.vs_ai:
                self.player2.center_y = touch.y

    def start_game(self, instance):
        self.is_running = True
        instance.disabled = True
        instance.opacity = 0
        self.mode_button.disabled = True
        self.mode_button.opacity = 0
        anchor_layout = instance.parent
        grid_layout = anchor_layout.parent
        grid_layout.remove_widget(instance)
        grid_layout.remove_widget(self.mode_button)

        if self.vs_ai:
            self.player2.center_y = self.center_y

    def switch_mode(self, instance):
        self.vs_ai = not self.vs_ai
        instance.text = "AI Mode" if self.vs_ai else "2 Players Mode"

    def move_ai_paddle(self):
        if self.ball.center_y > self.player2.center_y:
            self.player2.center_y += min(5, self.ball.center_y - self.player2.center_y)
        elif self.ball.center_y < self.player2.center_y:
            self.player2.center_y -= min(5, self.player2.center_y - self.ball.center_y)

from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout

class PongApp(App):
    def build(self):
        game = PongGame()
        game.serve_ball()
        Clock.schedule_interval(game.update, 1.0/60)

        anchor_layout = AnchorLayout()
        grid_layout = GridLayout(cols=1, spacing=10, size_hint=(None, None))
        grid_layout.bind(minimum_height=grid_layout.setter('height'))

        start_button = Button(
            text='Start',
            size_hint=(None, None),
            size=(100, 50)
        )
        start_button.bind(on_press=game.start_game)
        grid_layout.add_widget(start_button)

        mode_button = Button(
            text='AI Mode',
            size_hint=(None, None),
            size=(100, 50)
        )
        mode_button.bind(on_press=game.switch_mode)
        grid_layout.add_widget(mode_button)

        anchor_layout.add_widget(grid_layout)
        anchor_layout.anchor_x = 'center'
        anchor_layout.anchor_y = 'center'
        game.add_widget(anchor_layout)
        game.start_button = start_button
        game.mode_button = mode_button

        return game


if __name__ == '__main__':
    PongApp().run()
