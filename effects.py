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
        if not self.is_done(current_song_time) and current_song_time >= self.start_time:
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
                    self.constellation.set_single_led(led_position,
                                                      self.color)  # Turn the LED on with the specified color
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


class FillHexagonEffectOld(Effect):
    def __init__(self, constellation, start_time, duration, color, hexagon_index):
        super().__init__()
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color
        # self.hexagon_index = hexagon_index
        self.hexagon = self.constellation.find_hexagons()[hexagon_index]
        self.hex_segments = self.constellation.find_hex_segments(self.hexagon)
        self.led_indices = []

        # print(self.hexagon)

        for i in range(len(self.hex_segments)):
            self.led_indices.append(self.hex_segments[i].start_index)

        # print(self.led_indices)

    def run(self, current_song_data):  # returns false if effect is done, true if it is playing

        if not self.is_done(current_song_data):
            for i in self.led_indices:
                for j in range(self.constellation.num_leds_segment):
                    self.constellation.set_single_led(i + j, self.color)
            return True
        else:
            return False

    def is_done(self, current_song_data):
        if current_song_data[0] >= self.end_time:
            return True


class HexagonProgressEffect(Effect):
    def __init__(self, constellation, start_time, duration, color, hexagon_index, layer=1, acceleration_fraction=0):
        super().__init__()
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color
        self.layer = layer
        self.acceleration_fraction = acceleration_fraction

        self.hexagon_obj = self.constellation.hexagons[hexagon_index]

        self.progress = 0


    def run(self, current_song_time):

        if self.acceleration_fraction == 0:
            self.progress = (current_song_time - self.start_time) / self.duration
        else:
            # special case where there is no coasting
            t1 = self.start_time + self.duration / 2
            accel = 4 / (self.duration ** 2)
            v1 = accel * self.duration / 2

            if current_song_time < t1:
                self.progress = 0.5 * accel * (current_song_time - self.start_time) ** 2
            else:
                self.progress = -0.5 * accel * (current_song_time - self.start_time - 0.5 * self.duration) ** 2 + v1 * \
                                (current_song_time - self.start_time - 0.5 * self.duration) + 0.5
                # don't confuse the \
                # for a fraction



        leds_to_set = round(90 * self.progress)
        if leds_to_set > 90:
            leds_to_set = 90
        for i in range(leds_to_set):
            self.constellation.set_single_led(self.hexagon_obj.led_angle_coords[i][1], self.color)

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True


class SCurve:  # dead code
    def __init__(self, start_time, duration, acceleration_time):
        if acceleration_time > duration / 2:
            raise ValueError("Acceleration time must be less than or equal to half of the total duration.")

        self.start_time = start_time
        self.duration = duration
        self.acceleration_time = acceleration_time
        self.acceleration = 1 / (2 * acceleration_time / duration)  # 1 represents the total change in position.
        self.final_time = start_time + duration

    def update(self, current_time):
        if current_time < self.start_time:
            return 0
        elif current_time > self.final_time:
            return 1
        else:
            t = (current_time - self.start_time) / self.duration
            if t < self.acceleration_time / self.duration:  # Acceleration phase
                return 0.5 * self.acceleration * t**2
            elif t < 1 - self.acceleration_time / self.duration:  # Uniform motion phase
                return t
            else:  # Deceleration phase
                dt = 1 - t
                return 1 - 0.5 * self.acceleration * dt**2


# old stuff, kept to not break things
class FillHexagonEffect(Effect):
    def __init__(self, constellation, start_time, duration, color, hexagon_index, layer=1, fade_in_time=0,
                 fade_out_time=0):
        super().__init__()
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color
        self.layer = layer
        self.fade_in_time = fade_in_time
        self.fade_out_time = fade_out_time
        self.hexagon = self.constellation.find_hexagons()[hexagon_index]
        self.hex_segments = self.constellation.find_hex_segments(self.hexagon)
        self.led_indices = []

        for i in range(len(self.hex_segments)):
            self.led_indices.append(self.hex_segments[i].start_index)

    def run(self, current_song_time):
        if current_song_time < self.start_time or self.is_done(current_song_time):
            return False

        elapsed_time = current_song_time - self.start_time
        remaining_time = self.end_time - current_song_time

        if elapsed_time < self.fade_in_time:
            progress = elapsed_time / self.fade_in_time
        elif remaining_time <= self.fade_out_time:
            progress = remaining_time / self.fade_out_time
        else:
            progress = 1

        current_color = tuple(int(progress * c) for c in self.color)

        for i in self.led_indices:
            for j in range(self.constellation.num_leds_segment):
                self.constellation.set_single_led(i + j, current_color)
        return True

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True


class LightItUp(Effect):
    def __init__(self, constellation, start_time, duration, color, pattern_number, stagger, fade_in_time, fade_out_time,
                 layer=1):
        super().__init__()
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color
        self.layer = layer
        self.fade_in_time = fade_in_time
        self.fade_out_time = fade_out_time
        self.pattern_number = pattern_number

        self.sub_effects = []

        end_time = start_time + duration

        hex_duration = 0.6

        hex_start_time = start_time

        self.stagger = stagger

        if pattern_number == 0:
            hex_indices = [0, 4, 2, 5, 1]
        elif pattern_number == 1:
            hex_indices = [9, 8, 10, 11, 12]

        for i, index in enumerate(hex_indices):
            start_time = hex_start_time + i * stagger
            self.sub_effects.append(
                FillHexagonEffect(constellation, start_time, hex_duration, color, index, layer, fade_in_time,
                                  fade_out_time))

    def run(self, current_song_time):
        if not self.is_done(current_song_time) and current_song_time >= self.start_time:
            for effect in self.sub_effects:
                effect.run(current_song_time)
            return True

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True


class BeachBall(Effect):
    def __init__(self, constellation, start_time, duration, color, pattern_number, stagger, fade_in_time, fade_out_time,
                 layer=1):
        super().__init__()
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color
        self.layer = layer
        self.fade_in_time = fade_in_time
        self.fade_out_time = fade_out_time
        self.pattern_number = pattern_number

        self.sub_effects = []

        hex_duration = 1.5

        hex_start_time = start_time

        self.stagger = stagger

        if color is None:
            ball_colors = [[255, 0, 0], [255, 255, 0], [0, 255, 0], [0, 255, 255], [0, 0, 255], [255, 0, 255]]

        if pattern_number == 0:
            hex_indices = [6, 11, 8, 3, 4, 5]
        elif pattern_number == 1:
            hex_indices = [6, 5, 4, 3, 8, 11]

        for i, index in enumerate(hex_indices):
            start_time = hex_start_time + i * stagger
            self.sub_effects.append(
                FillHexagonEffect(constellation, start_time, hex_duration, ball_colors[i], index, layer, fade_in_time,
                                  fade_out_time))

    def run(self, current_song_time):
        if not self.is_done(current_song_time) and current_song_time >= self.start_time:
            for effect in self.sub_effects:
                effect.run(current_song_time)
            return True

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True


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
class DrawRingEffect(Effect):
    def __init__(self, constellation, start_time, duration, outer_rad, thickness, color):
        super().__init__()
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
        self.is_transition = is_transition

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
