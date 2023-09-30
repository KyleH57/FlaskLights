import colorsys
import math

import effects as ef

class RainbowWaveEffect2(ef.Effect):
    def __init__(self, constellation, start_time, duration, wave_length, speed, saturation, layer=0):
        super().__init__(start_time, duration)
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.wave_length = wave_length
        self.speed = speed
        self.saturation = saturation
        self.layer = layer

    def run(self, current_song_time):
        if not self.is_done(current_song_time):
            elapsed_time = current_song_time - self.start_time
            wave_progress = elapsed_time * self.speed  # How far along the wave is in mm
            self.rainbow_wave_x(self.constellation, self.wave_length, wave_progress)
            return True
        else:
            return False

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True

    def rainbow_wave_x(self, constellation, wave_length, wave_progress):
        for led in constellation.leds:
            x_coord = led.xCoord_centroid
            hue = ((x_coord + wave_progress) % wave_length) / wave_length
            color_hsv = (hue, self.saturation, 1)  # Full saturation and value for a bright rainbow
            color_rgb = tuple(math.floor(i * 255) for i in colorsys.hsv_to_rgb(*color_hsv))

            # convert HSV to RGB
            color_rgb = colorsys.hsv_to_rgb(color_hsv[0], color_hsv[1], color_hsv[2])

            # convert float RGB values to integers in the range 0 to 255
            color_int = [int(c * 255) for c in color_rgb]

            led.set_color(color_int)