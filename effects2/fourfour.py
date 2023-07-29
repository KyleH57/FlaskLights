import effects as ef
from effects2 import hexagonprogress as hp

class FourFour(ef.Effect):
    def __init__(self, constellation, start_time, duration, beats, color1, color2, layer=1):
        super().__init__()
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.beats = beats
        self.color1 = color1
        self.color2 = color2
        self.layer = layer
        self.current_beat_index = 0
        self.last_beat = None

        self.beat_to_hexagons = {
            0: [0, 1, 2],  # On the first beat, hexagons 0,1,2 are addressed
            1: [4, 5],  # On the 2nd beat, hexagons 4,5 are addressed
            2: [3, 6, 7],  # On the 3rd beat, hexagons 3,6,7 are addressed
            3: [8, 11],  # On the 4th beat, hexagons 8,11 are addressed
        }

        self.constellation.add_effect(hp.HexagonProgressEffect(self.constellation, self.start_time, self.duration, (0, 255, 0), (255, 0, 0), 10, self.layer + 1))

    def run(self, current_song_time):
        FADE_IN_TIME = 0.07
        FADE_OUT_TIME = 2
        if not self.is_done(current_song_time) and current_song_time >= self.start_time:
            # If beat has changed
            if self.update_beats(current_song_time):
                if self.current_beat_index + 2 < len(self.beats):
                    beat_modulo = self.current_beat_index % 4  # Now we're considering 4 beats
                    hexagons_for_this_beat = self.beat_to_hexagons[beat_modulo]
                    color = self.color1 if beat_modulo % 2 == 0 else self.color2  # Even indices use color1, odd ones use color2

                    for hexagon in hexagons_for_this_beat:
                        self.constellation.add_effect(
                            ef.FillHexagonEffect(
                                self.constellation,
                                current_song_time,
                                self.get_beat_duration(self.current_beat_index) * 2.2,
                                color,  # use the chosen color
                                hexagon,  # The hexagon index from the beat_to_hexagons mapping
                                1,
                                FADE_IN_TIME,
                                FADE_OUT_TIME
                            )
                        )
            return True
        else:
            return False

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True

    def update_beats(self, current_song_time):
        for beat in self.beats:
            if beat["start"] <= current_song_time < beat["start"] + beat["duration"]:
                self.current_beat_index = self.beats.index(beat)
                if self.current_beat_index != self.last_beat:
                    self.last_beat = self.current_beat_index
                    return True  # beat has changed
        return False  # beat has not changed

    def get_beat_duration(self, beat_index):
        return self.beats[beat_index]["duration"]
