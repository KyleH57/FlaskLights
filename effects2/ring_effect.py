import math

import effects as ef

class DrawRingEffect(ef.Effect):
    def __init__(self, constellation, start_time, duration, outer_rad, thickness, color):
        super().__init__(start_time, duration)
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.outer_rad = outer_rad
        self.thickness = thickness
        self.color = color

    def run(self, current_song_time):
        if not self.is_done(current_song_time) and current_song_time >= self.start_time:
            inner_rad = self.outer_rad - self.thickness
            for led in self.constellation.leds:
                led_x, led_y = led.xCoord_centroid, led.yCoord_centroid
                distance = math.sqrt(led_x ** 2 + led_y ** 2)

                if inner_rad <= distance <= self.outer_rad:
                    led.set_color(self.color)
            return True
        else:
            return False

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True


class AnimatedRingEffect(DrawRingEffect):
    def __init__(self, constellation, start_time, duration, outer_rad, thickness, color, velocity, acceleration,
                 x_coord, y_coord, layer=1, is_transition=False):
        super().__init__(constellation, start_time, duration, outer_rad, thickness, color)
        self.velocity = velocity
        self.acceleration = acceleration
        self.x_coord = x_coord
        self.y_coord = y_coord
        self.layer = layer
        self.is_transition = is_transition  # This is to fill the whole board

    def run(self, current_song_time):
        if not self.is_done(current_song_time) and current_song_time >= self.start_time:
            elapsed_time = current_song_time - self.start_time
            current_velocity = self.velocity + self.acceleration * elapsed_time
            self.outer_rad += current_velocity * elapsed_time

            if self.is_transition and current_velocity <= 0:
                for led in self.constellation.leds:
                    led.set_color(self.color)
                return True

            if current_velocity < 0:
                return False

            inner_rad = self.outer_rad - self.thickness
            for led in self.constellation.leds:
                led_x, led_y = led.xCoord_centroid - self.x_coord, led.yCoord_centroid - self.y_coord
                distance = math.sqrt(led_x ** 2 + led_y ** 2)

                if inner_rad <= distance <= self.outer_rad:
                    led.set_color(self.color)

            return True
        else:
            return False

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time or self.velocity < 0:
            return True