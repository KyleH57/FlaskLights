import effects as ef

class GradientEffect(ef.Effect):
    def __init__(self, constellation, start_time, duration, color1, color2, layer):
        super().__init__()
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color1 = color1
        self.color2 = color2
        self.layer = layer

        self.min_x = constellation.min_x
        self.max_x = constellation.max_x



    def run(self, current_song_time):
        if not self.is_done(current_song_time) and current_song_time >= self.start_time:
            for led in self.constellation.leds:
                t = (led.xCoord_centroid - self.min_x) / (self.max_x - self.min_x) # t is between 0 and 1 and represents the
                # position of the LED along the x-axis

                new_color = [
                    int((1 - t) * self.color1[0] + t * self.color2[0]),
                    int((1 - t) * self.color1[1] + t * self.color2[1]),
                    int((1 - t) * self.color1[2] + t * self.color2[2])
                ]
                new_color = [
                    max(0, min(255, new_color[0])),
                    max(0, min(255, new_color[1])),
                    max(0, min(255, new_color[2]))
                ]

                led.set_color(new_color)

            return True
        else:
            return False

    def is_done(self, current_song_time):
        return current_song_time >= self.end_time
