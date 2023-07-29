import effects as ef

class HexagonProgressEffect(ef.Effect):
    def __init__(self, constellation, start_time, duration, color, bg_color, hexagon_index, layer=1,
                 acceleration_fraction=0):
        super().__init__()
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color
        self.bg_color = bg_color
        self.layer = layer
        self.acceleration_fraction = acceleration_fraction

        self.hexagon_obj = self.constellation.hexagons[hexagon_index]

        self.progress = 0

    def run(self, current_song_time):
        if current_song_time < self.start_time:
            return True

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

        for i in range(90):
            if i < leds_to_set:
                self.constellation.set_single_led(self.hexagon_obj.led_angle_coords[i][1], self.color)
            else:
                self.constellation.set_single_led(self.hexagon_obj.led_angle_coords[i][1], self.bg_color)

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True