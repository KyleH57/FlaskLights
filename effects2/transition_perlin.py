import numpy as np
from noise import snoise3

import effects as ef

import colorsys


# set hue2 to None for white mode
# Use an empty list if beats is None
class TransitionPerlinNoiseEffect(ef.Effect):
    def __init__(self, constellation, start_time, duration, saturation, layer, scale, speed, noise_dim, hue_list,
                 hue_times):
        super().__init__(start_time, duration)
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.saturation = saturation
        self.layer = layer
        self.noise_gen = PerlinNoiseGenerator(*noise_dim, scale)
        self.speed = speed  # Store the initial speed
        self.noise_dim = noise_dim  # (width, height)
        self.hue_list = hue_list  # list of hues to use (e.g. [0, 0.5, 1])
        self.hue_times = hue_times  # start transition times between hues (e.g. [0, 20.23, 50.5])
        self.hue_transition_time = 3  # time to transition between hues in seconds

    def run(self, current_song_time):
        if not self.is_done(current_song_time):
            self.perlin_noise_effect(self.constellation, current_song_time)
            return True
        else:
            return False

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time:
            return True

    def map_coord_to_noise(self, coord, max_coord):
        # Map LED's centroid coordinates to noise array coordinates
        return int(
            (coord + max_coord) / (2 * max_coord) * self.noise_dim[0])  # assuming x and y dimensions are the same

    def perlin_noise_effect(self, constellation, current_song_time):
        current_speed = self.speed
        noise_array = self.noise_gen.generate_perlin_noise(current_speed)

        for led in constellation.leds:
            x = self.map_coord_to_noise(led.xCoord_centroid, 950)
            y = self.map_coord_to_noise(led.yCoord_centroid, 615)

            hue = noise_array[y, x]
            color_int = self.get_color(hue, current_song_time)
            led.set_color(color_int)

    def get_color(self, hue, current_song_time):
        # Determine the interpolated hue based on the current song time and the transition time
        interpolated_hue = self.get_interpolated_hue(current_song_time)

        remapped_value = color_remap(hue, a=10, b=0.4)  # remap to make it more or less white
        saturation_value = remapped_value * self.saturation

        # Interpolate between white and the current hue based on the remapped value
        hsv_color = (interpolated_hue, saturation_value, 1)
        color_rgb = colorsys.hsv_to_rgb(*hsv_color)
        color_int = [int(c * 255) for c in color_rgb]

        return color_int

    def get_interpolated_hue(self, current_song_time):

        for idx, hue_time in enumerate(self.hue_times):
            # If we are before the first hue_time
            if current_song_time < self.hue_times[0]:
                return self.hue_list[0]

            # Check if we are between two hue_times
            if idx < len(self.hue_times) - 1 and hue_time <= current_song_time < hue_time + self.hue_transition_time:
                hue1 = self.hue_list[idx]
                hue2 = self.hue_list[idx + 1]

                # Calculate how far we are into the transition
                ratio = (current_song_time - hue_time) / self.hue_transition_time

                # Interpolate between the two hues
                return (1 - ratio) * hue1 + ratio * hue2

            # If we are between two transition periods
            elif idx < len(self.hue_times) - 1 and hue_time + self.hue_transition_time <= current_song_time < \
                    self.hue_times[idx + 1]:
                return self.hue_list[idx + 1]

        return self.hue_list[-1]  # return the last hue if current_song_time is beyond all hue_times


class PerlinNoiseGenerator:
    def __init__(self, width, height, scale):
        self.width = width
        self.height = height
        self.scale = scale
        self.z = 0

        self.CLIPPING_THRESHOLD = 0.50

    def generate_perlin_noise(self, speed):
        noise_array = np.zeros((self.height, self.width))

        for y in range(self.height):
            for x in range(self.width):
                noise_value = snoise3(x / self.scale, y / self.scale, self.z, octaves=6, persistence=0.5,
                                      lacunarity=2.0)

                if noise_value > self.CLIPPING_THRESHOLD:
                    noise_value = self.CLIPPING_THRESHOLD
                elif noise_value < -self.CLIPPING_THRESHOLD:
                    noise_value = -self.CLIPPING_THRESHOLD

                # now scale to the range of 0 to 1
                noise_value = (noise_value + self.CLIPPING_THRESHOLD) / (2 * self.CLIPPING_THRESHOLD)
                # snosie3 returns a value between -1 and 1, but the vast majority of values are between -0.6 and 0.6
                noise_array[y][x] = noise_value

        self.z += speed
        return noise_array


def color_remap(x, a=10, b=0.4):
    """A custom sigmoid function with adjustable center.

    :param x: The input value.
    :param a: The parameter that adjusts the steepness of the sigmoid.
    :param b: The parameter that adjusts the center of the sigmoid.
    :return: The output value between 0 and 1.
    """
    return 1 / (1 + np.exp(-a * (x - b)))
