class FillAllEffect:
    def __init__(self, constellation, start_time, duration, color):
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color

    def write(self, current_song_time):
        for led in range(self.constellation.num_leds):
            self.constellation.set_single_led(led, self.color)

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True


class FillHexagonEffect:
    def __init__(self, constellation, start_time, duration, color, hexagon_index):
        print("Adding FillHexagonEffect")

        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color
        # self.hexagon_index = hexagon_index
        self.hexagon = self.constellation.find_hexagons()[hexagon_index]
        self.hex_segments = self.constellation.find_hex_segments(self.hexagon)
        self.led_indices = []

        #print(self.hexagon)

        for i in range(len(self.hex_segments)):
            self.led_indices.append(self.hex_segments[i].start_index)

        print(self.led_indices)

    def write(self, current_song_time):

        for i in self.led_indices:
            for j in range(self.constellation.num_leds_segment):
                self.constellation.set_single_led(i + j, self.color)

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True
