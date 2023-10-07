from random import randint

from shows import rgb_perlin_show, alternating_perlin_show

def generate_show(constellation, song, debug=True):
    # generate a number between 1 and n
    n = 1
    random_number = randint(1, n)
    random_number = 1

    if debug:
        print("Generating show...")

    if song.lyrics_mapped:
        if random_number == 1:
            alternating_perlin_show.create_alternating_perlin_show(constellation, song)
        else:
            rgb_perlin_show.create_rgb_perlin_show(constellation, song)



    else:
        print("Default show...")
        rgb_perlin_show.create_rgb_perlin_show(constellation, song)


