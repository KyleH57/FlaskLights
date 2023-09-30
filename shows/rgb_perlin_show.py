import effects as ef
from effects2 import loudness_perlin

def create_rgb_perlin_show(constellation, song):
    BASE_PERLIN_SIZE = 65

    hue1 = 0
    hue2 = 1

    perlin_size = BASE_PERLIN_SIZE * abs(hue2 - hue1)

    # perlin_speed = abs(hue2 - hue1) * 0.1  # good for a diff of 1/6
    # perlin_speed = abs(hue2 - hue1) * 0.0375 # good for a diff of 2/6
    # perlin_speed = abs(hue2 - hue1) * 0.01  # good for a diff of 4/6
    perlin_speed = abs(hue2 - hue1) * 0.00375  # good for a diff of 1
    print("adding perlin noise effect")
    constellation.add_effect(
        loudness_perlin.LoudnessPerlin(constellation, song.current_song_time, song.time_until_song_end, 1.0, 1,
                                       perlin_size, perlin_speed, (64, 64), song.segments, 'both',
                                       ef.ColorMode.INTERPOLATE_HUES, {'hue1': hue1, 'hue2': hue2}))