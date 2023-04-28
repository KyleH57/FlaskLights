import colorsys
import math
from typing import List


class Effect:
    def run(self, current_song_data):
        raise NotImplementedError("Subclasses must implement this method")

    def is_done(self, current_song_data):
        raise NotImplementedError("Subclasses must implement this method")


class FillAllEffect(Effect):
    def __init__(self, constellation, start_time, duration, color, layer):
        super().__init__()
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color
        self.layer = layer

    def run(self, current_song_time):
        if not self.is_done(current_song_time):
            for led in range(self.constellation.num_leds):
                self.constellation.set_single_led(led, self.color)
            return True
        else:
            return False

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True


class DebugCounterEffect:
    def __init__(self, constellation, number, start_index, start_time, duration, color, layer):
        super().__init__()
        self.constellation = constellation
        self.number = number
        self.start_index = start_index
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color
        self.layer = layer

    def run(self, current_time):
        if not self.is_done(current_time):
            binary_representation = bin(self.number)[2:]  # Remove the '0b' prefix
            binary_length = len(binary_representation)

            for i, bit in enumerate(reversed(binary_representation)):
                led_position = self.start_index + i
                if bit == '1':
                    self.constellation.set_single_led(led_position, self.color)  # Turn the LED on with the specified color
                else:
                    self.constellation.set_single_led(led_position, (0, 0, 0))  # Turn the LED off

            return True
        else:
            return False

    def is_done(self, current_time):
        if current_time >= self.end_time:
            return True
        else:
            return False


# class FillHexagonEffect(Effect):
#     def __init__(self, constellation, start_time, duration, color, hexagon_index):
#         super().__init__()
#         self.constellation = constellation
#         self.start_time = start_time
#         self.duration = duration
#         self.end_time = start_time + duration
#         self.color = color
#         # self.hexagon_index = hexagon_index
#         self.hexagon = self.constellation.find_hexagons()[hexagon_index]
#         self.hex_segments = self.constellation.find_hex_segments(self.hexagon)
#         self.led_indices = []
#
#         # print(self.hexagon)
#
#         for i in range(len(self.hex_segments)):
#             self.led_indices.append(self.hex_segments[i].start_index)
#
#         # print(self.led_indices)
#
#     def run(self, current_song_data):  # returns false if effect is done, true if it is playing
#
#         if not self.is_done(current_song_data):
#             for i in self.led_indices:
#                 for j in range(self.constellation.num_leds_segment):
#                     self.constellation.set_single_led(i + j, self.color)
#             return True
#         else:
#             return False
#
#     def is_done(self, current_song_data):
#         if current_song_data[0] >= self.end_time:
#             return True
#
#
# class BeatMapEffect(Effect):
#     def __init__(self, constellation, start_time, duration, bg_color, beat_color1, beat_color2):
#         super().__init__()
#         self.constellation = constellation
#         self.start_time = start_time
#         self.duration = duration
#         self.end_time = start_time + duration
#         self.bg_color = bg_color
#         self.sub_effects: List[Effect] = []
#         self.beat_color1 = beat_color1
#         self.beat_color2 = beat_color2
#
#         self.num_hexes = 10
#
#         self.sub_effects.append(FillAllEffect(constellation, start_time, duration, bg_color))
#
#     def run(self, current_song_data):
#
#         if current_song_data[1] % self.num_hexes == 0:
#             self.sub_effects = self.sub_effects[:1]
#             self.sub_effects.append(
#                 FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color2, 0))
#         elif current_song_data[1] % self.num_hexes == 1:
#             self.sub_effects.append(
#                 FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color1, 9))
#         elif current_song_data[1] % self.num_hexes == 2:
#             self.sub_effects.append(
#                 FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color2, 4))
#         elif current_song_data[1] % self.num_hexes == 3:
#             self.sub_effects.append(
#                 FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color1, 8))
#         elif current_song_data[1] % self.num_hexes == 4:
#             self.sub_effects.append(
#                 FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color2, 2))
#         elif current_song_data[1] % self.num_hexes == 5:
#             self.sub_effects.append(
#                 FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color1, 10))
#         elif current_song_data[1] % self.num_hexes == 6:
#             self.sub_effects.append(
#                 FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color2, 5))
#         elif current_song_data[1] % self.num_hexes == 7:
#             self.sub_effects.append(
#                 FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color1, 11))
#         elif current_song_data[1] % self.num_hexes == 8:
#             self.sub_effects.append(
#                 FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color2, 1))
#         elif current_song_data[1] % self.num_hexes == 9:
#             self.sub_effects.append(
#                 FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color1, 12))
#
#
#
#
#
#         for effect in self.sub_effects:
#             if not effect.run(current_song_data):
#                 del effect
#
#         if not self.is_done(current_song_data):
#             return True
#         else:
#             return False
#
#     def is_done(self, current_song_time):
#         if current_song_time[0] >= self.end_time:
#             return True
#
#
class RainbowWaveEffect(Effect):
    def __init__(self, constellation, start_time, duration, wave_length, speed, saturation, layer=0):
        super().__init__()
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

#
#
# class DrawRingEffect(Effect):
#     def __init__(self, constellation, start_time, duration, outer_rad, thickness, color):
#         super().__init__()
#         self.constellation = constellation
#         self.start_time = start_time
#         self.duration = duration
#         self.end_time = start_time + duration
#         self.outer_rad = outer_rad
#         self.thickness = thickness
#         self.color = color
#
#     def run(self, current_song_data):
#         if not self.is_done(current_song_data):
#             inner_rad = self.outer_rad - self.thickness
#             for led in self.constellation.leds:
#                 led_x, led_y = led.xCoord_centroid, led.yCoord_centroid
#                 distance = math.sqrt(led_x ** 2 + led_y ** 2)
#
#                 if inner_rad <= distance <= self.outer_rad:
#                     led.set_color(self.color)
#             return True
#         else:
#             return False
#
#     def is_done(self, current_song_data):
#         if current_song_data[0] >= self.end_time:
#             return True
#
#
# class AnimatedRingEffect(DrawRingEffect):
#     def __init__(self, constellation, start_time, duration, outer_rad, thickness, color, velocity, acceleration,
#                  x_coord, y_coord):
#         super().__init__(constellation, start_time, duration, outer_rad, thickness, color)
#         self.velocity = velocity
#         self.acceleration = acceleration
#         self.x_coord = x_coord
#         self.y_coord = y_coord
#
#     def run(self, current_song_data):
#         if self.velocity < 0:
#             return False
#
#         if not self.is_done(current_song_data):
#             elapsed_time = current_song_data[0] - self.start_time
#             current_velocity = self.velocity + self.acceleration * elapsed_time
#             # print(current_velocity)
#             self.outer_rad += current_velocity * elapsed_time
#
#             if current_velocity < 0:
#                 return False
#
#             inner_rad = self.outer_rad - self.thickness
#             for led in self.constellation.leds:
#                 led_x, led_y = led.xCoord_centroid - self.x_coord, led.yCoord_centroid - self.y_coord
#                 distance = math.sqrt(led_x ** 2 + led_y ** 2)
#
#                 if inner_rad <= distance <= self.outer_rad:
#                     led.set_color(self.color)
#
#             return True
#         else:
#             return False
#
#     def is_done(self, current_song_data):
#         if current_song_data[0] >= self.end_time or self.velocity < 0:
#             return True
