import effects as ef

def create_alternating_perlin_show(constellation, song):
    BASE_PERLIN_SIZE = 65



    perlin_size = BASE_PERLIN_SIZE


    perlin_speed = 0.00375  # good for a diff of 1

    # Loop through each section
    for i, section in enumerate(song.sections):
        hue1 = 0
        if i % 2 == 0:  # For even sections use primary hue
            hue2 = song.primary_hue
        else:  # For odd sections use accent hue
            hue2 = song.accent_hue

        start_time = section['start']
        duration = section['duration']

        constellation.add_effect(
        ef.PerlinNoiseEffect(
            constellation, start_time, duration, 1.0, 1,
            perlin_size, perlin_speed * 6, (64, 64), None, 'odd',
            ef.ColorMode.HUE_TO_WHITE, {'hue1': hue2, 'hue2': 0}
        )
        )
