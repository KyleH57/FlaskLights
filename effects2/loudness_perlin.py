from enum import Enum

from noise import snoise3
import colorsys
import numpy as np

import effects as ef
import songState as ss

class ColorMode(Enum):
    INTERPOLATE_HUES = 1
    HUE_TO_WHITE = 2

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
                noise_value = snoise3(x / self.scale, y / self.scale, self.z, octaves=6, persistence=0.5, lacunarity=2.0)

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


# set hue2 to None for white mode
# Use an empty list if beats is None
class LoudnessPerlin(ef.Effect):
    def __init__(self, constellation, start_time, duration, saturation, layer, scale, speed, noise_dim, segments, boost_beat_parity, color_mode, color_params=None):
        super().__init__(start_time, duration)
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.saturation = saturation
        self.layer = layer
        self.noise_gen = PerlinNoiseGenerator(*noise_dim, scale)
        self.speed = speed  # Store the initial speed
        self.segments = segments


        self.noise_dim = noise_dim
        self.segments = segments

        self.boost_beat_parity = boost_beat_parity  # Use 'even', 'odd' or 'both'
        self.BEAT_SPEED_FRACTION = 0.5  # speed boost will last for this fraction of the beat
        self.BEAT_SPEED_BOOST = 2.75 # speed boost multiplier
        self.color_mode = color_mode
        self.color_params = color_params or {}

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
        return int((coord + max_coord) / (2 * max_coord) * self.noise_dim[0])  # assuming x and y dimensions are the same

    def perlin_noise_effect(self, constellation, current_song_time):
        current_speed = self.get_current_speed(current_song_time)
        noise_array = self.noise_gen.generate_perlin_noise(current_speed)

        for led in constellation.leds:
            x = self.map_coord_to_noise(led.xCoord_centroid, 950)
            y = self.map_coord_to_noise(led.yCoord_centroid, 615)

            hue = noise_array[y, x]
            color_int = self.get_color(hue)
            led.set_color(color_int)

    def get_current_speed(self, current_time):
        curr_seg = ss.get_current_segment(self.segments, current_time)
        timbre_loudness_list = []
        for segment in self.segments:
            timbre_loudness_list.append(segment['timbre'][0])

        timbre_loudness_percentiles = calculate_percentiles(timbre_loudness_list) #TODO optimize this

        current_segment_index = self.segments.index(curr_seg)

        # print(timbre_loudness_percentiles[current_segment_index])

        self.speed = 0.003 + 0.02 * timbre_loudness_percentiles[current_segment_index] #TODO optimize this

        # print(self.speed)


        return self.speed

    def get_color(self, hue): # the hue arg is just a number between 0 and 1 and is from the noise array.
        # It has nothing to do with color
        if self.color_mode == ColorMode.INTERPOLATE_HUES:
            hue1, hue2 = self.color_params['hue1'], self.color_params['hue2']

            #print('hue old: ', hue)
            # interpolate between hue1 and hue2
            hue = hue1 + (hue2 - hue1) * hue

        elif self.color_mode == ColorMode.HUE_TO_WHITE:
            hue1 = self.color_params['hue1']
            # interpolate between hue1 and white (hue 0, saturation 0)
            hue = hue1 + (0 - hue1) * hue
            self.saturation = (1 - hue) * self.saturation

        # convert HSV to RGB and then to 0-255 range
        color_rgb = colorsys.hsv_to_rgb(hue, self.saturation, 1)
        color_int = [int(c * 255) for c in color_rgb]

        return color_int


def calculate_percentiles(unordered_list):
    # Sort the list
    ordered_list = sorted(unordered_list)

    # Get the total number of elements in the list
    n = len(ordered_list)

    # If the list is empty or has only one element, return an empty list or [1.0] respectively
    if n == 0:
        return []
    if n == 1:
        return [1.0]

    # Calculate and store percentiles for ordered list
    ordered_percentiles = []
    for i in range(n):
        percentile = (i) / (n - 1)
        ordered_percentiles.append(percentile)

    # Map the percentiles back to the original unordered list
    percentile_map = {val: percentile for val, percentile in zip(ordered_list, ordered_percentiles)}
    original_percentiles = [percentile_map[val] for val in unordered_list]

    return original_percentiles


