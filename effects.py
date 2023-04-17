from typing import List


class Effect:
    def run(self, current_song_data):
        raise NotImplementedError("Subclasses must implement this method")


class FillAllEffect(Effect):
    def __init__(self, constellation, start_time, duration, color):
        super().__init__()
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color

    def run(self, current_song_data):
        if not self.is_done(current_song_data):
            for led in range(self.constellation.num_leds):
                self.constellation.set_single_led(led, self.color)
            return True
        else:
            return False

    def is_done(self, current_song_data):
        if current_song_data[0] >= self.end_time:
            return True


class FillHexagonEffect(Effect):
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


# class Fill2HexagonEffect:
#     def __init__(self, constellation, start_time, duration, color, hexagon_index):
#         self.sub_effects = []
#         self.sub_effects.append(FillHexagonEffect(constellation, start_time, duration - 2, color, hexagon_index))
#         self.sub_effects.append(FillHexagonEffect(constellation, start_time, duration - 1, color, hexagon_index + 2))
#
#         self.end_time = start_time + duration
#
#     def run(self, current_song_data):
#         for effect in self.sub_effects:
#             if not effect.run(current_song_data):
#                 del effect
#
#         if not self.is_done(current_song_data):
#             return True
#         else:
#             return False
#
#     def is_done(self, current_song_data):
#         if current_song_data[0] >= self.end_time:
#             return True


class BeatMapEffect(Effect):
    def __init__(self, constellation, start_time, duration, bg_color, beat_color1, beat_color2):
        super().__init__()
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.bg_color = bg_color
        self.sub_effects: List[Effect] = []
        self.beat_color1 = beat_color1
        self.beat_color2 = beat_color2

        self.num_hexes = 10

        self.sub_effects.append(FillAllEffect(constellation, start_time, duration, bg_color))

    def run(self, current_song_data):

        if current_song_data[1] % self.num_hexes == 0:
            self.sub_effects = self.sub_effects[:1]
            self.sub_effects.append(
                FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color2, 0))
        elif current_song_data[1] % self.num_hexes == 1:
            self.sub_effects.append(
                FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color1, 9))
        elif current_song_data[1] % self.num_hexes == 2:
            self.sub_effects.append(
                FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color2, 4))
        elif current_song_data[1] % self.num_hexes == 3:
            self.sub_effects.append(
                FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color1, 8))
        elif current_song_data[1] % self.num_hexes == 4:
            self.sub_effects.append(
                FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color2, 2))
        elif current_song_data[1] % self.num_hexes == 5:
            self.sub_effects.append(
                FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color1, 10))
        elif current_song_data[1] % self.num_hexes == 6:
            self.sub_effects.append(
                FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color2, 5))
        elif current_song_data[1] % self.num_hexes == 7:
            self.sub_effects.append(
                FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color1, 11))
        elif current_song_data[1] % self.num_hexes == 8:
            self.sub_effects.append(
                FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color2, 1))
        elif current_song_data[1] % self.num_hexes == 9:
            self.sub_effects.append(
                FillHexagonEffect(self.constellation, current_song_data[0], 999, self.beat_color1, 12))





        for effect in self.sub_effects:
            if not effect.run(current_song_data):
                del effect

        if not self.is_done(current_song_data):
            return True
        else:
            return False

    def is_done(self, current_song_time):
        if current_song_time[0] >= self.end_time:
            return True
