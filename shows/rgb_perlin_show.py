import random

import effects as ef
from effects2 import loudness_perlin, ring_effect


def create_rgb_perlin_show(constellation, song, beat_parity='first'):
    BASE_PERLIN_SIZE = 65

    hue1 = 0
    hue2 = 1

    perlin_size = BASE_PERLIN_SIZE * abs(hue2 - hue1)
    perlin_speed = abs(hue2 - hue1) * 0.00375  # good for a diff of 1
    print("adding perlin noise effect")
    constellation.add_effect(
        loudness_perlin.LoudnessPerlin(constellation, song.current_song_time, song.time_until_song_end, 1.0, 1,
                                       perlin_size, perlin_speed, (64, 64), song.segments, 'both',
                                       ef.ColorMode.INTERPOLATE_HUES, {'hue1': hue1, 'hue2': hue2}))

    for index, beat in enumerate(song.beats):
        start = beat["start"]
        duration = beat["duration"]

        # Check the beat parity
        if (
            beat_parity == 'both' or
            (beat_parity == 'even' and index % 2 == 0) or
            (beat_parity == 'odd' and index % 2 == 1) or
            (beat_parity == 'first' and index % 4 == 0)  # assuming 4 beats in a measure
        ):
            constellation.add_effect(
                ring_effect.AnimatedRingEffect(constellation, start, duration, 200, 250, (255, 255, 255), 1200, 1200 * -1.618,
                                              0, 0, 2, False))

