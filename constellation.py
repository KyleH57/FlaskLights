import math
import random
import time

import board
import neopixel
import colorsys

class WS2812LED:
    def __init__(self, xCoord, yCoord):
        self.xCoord = xCoord
        self.yCoord = yCoord
        self.color = [0, 0, 0]
        # self.brightness = 0

    # string representation of the LED
    def __str__(self):
        return "LED at " + str(self.xCoord) + ", " + str(self.yCoord)

    def setColor(self, color):
        self.color = color


class led_segment:
    def __init__(self, x_start, y_start, angle_degrees, num_leds, spacing, edge_spacing=0):
        self.x_start = x_start
        self.y_start = y_start
        self.angle = math.radians(angle_degrees)  # pay attention to units
        self.num_leds = num_leds
        self.spacing = spacing
        self.edge_spacing = edge_spacing
        self.leds = []

        # calculate total length of segment
        total_length = (num_leds - 1) * spacing + 2 * edge_spacing

        # calculate end point of segment
        x_end = x_start + total_length * math.cos(self.angle)
        y_end = y_start + total_length * math.sin(self.angle)

        # create list of LED objects with calculated coordinates
        for i in range(num_leds):
            x = x_start + i * spacing * math.cos(self.angle) + edge_spacing * math.cos(self.angle)
            y = y_start + i * spacing * math.sin(self.angle) + edge_spacing * math.sin(self.angle)
            self.leds.append(WS2812LED(x, y))

        self.x_end = x_end
        self.y_end = y_end

    def set_led_color(self, index, color):
        self.leds[index].setColor(color)

    def set_color_all(self, color):
        for i in range(self.num_leds):
            self.leds[i].setColor(color)

    def get_color(self, index):
        return self.leds[index].color

    def print_XY_coords(self):
        # print the x_start and y_start of the segment rounded to 1 decimal place
        print("x_start: {:.1f}, y_start: {:.1f}".format(self.x_start, self.y_start))

    def __str__(self):
        return "LED segment starting at ({}, {}) with {} LEDs spaced {} units apart at an angle of {} degrees".format(
            self.x_start, self.y_start, self.num_leds, self.spacing, math.degrees(self.angle))


class constellation:
    def __init__(self, angles, num_leds_segment, spacing, edge_spacing, brightness, debug=False):
        self.angles = angles.split(',')
        self.num_segments = len(self.angles)
        self.segments = []
        x_start, y_start = 0, 0

        # array of all currently playing effects
        self.effects = []

        for angle_str in self.angles:
            angle = int(angle_str[:-1]) if 'r' in angle_str else int(angle_str)
            segment = led_segment(x_start, y_start, angle, num_leds_segment, spacing, edge_spacing)
            self.segments.append(segment)
            if 'r' not in angle_str:
                x_start, y_start = segment.x_end, segment.y_end

        self.num_leds = self.num_segments * num_leds_segment
        self.color_data = [[0, 0, 0] for i in range(self.num_leds)]

        # combine color data from all segments into one array
        for i in range(self.num_segments):
            for j in range(num_leds_segment):
                index = i * num_leds_segment + j
                self.color_data[index] = self.segments[i].get_color(j)

        self.pixels2 = neopixel.NeoPixel(board.D18, self.num_leds, brightness=brightness, auto_write=False)

        self.clear()

        if debug:
            # print number of leds
            print("Number of LEDs: {}".format(self.num_leds))


    def set_color_rgb(self, led_index, color):
        # check if led_index is valid
        if led_index < 0 or led_index >= self.num_leds:
            return None

        self.color_data[led_index] = color

    def set_color_HSV(self, led_index, color):
        # check if led_index is valid
        if led_index < 0 or led_index >= self.num_leds:
            return None

        # convert HSV to RGB
        color_rgb = colorsys.hsv_to_rgb(color[0], color[1], color[2])

        # convert float RGB values to integers in the range 0 to 255
        color_int = [int(c * 255) for c in color_rgb]

        self.color_data[led_index] = color_int

    def get_color(self, segment_index, led_index):
        return self.segments[segment_index].get_color(led_index)

    def set_segment_color(self, segment_index, color):
        self.segments[segment_index].set_color_all(color)

    def copy_segment_colors_to_data(self):
        for i in range(self.num_segments):
            for j in range(self.segments[i].num_leds):
                index = i * self.segments[i].num_leds + j
                self.color_data[index] = self.segments[i].get_color(j)

    def get_LED(self, led_index):
        # check if led_index is valid
        if led_index < 0 or led_index >= self.num_leds:
            return None

        return self.color_data[led_index]

    def rainbow_wave_x(constellation, wave_length, speed, frequency, wave_progress):
        for led_index in range(constellation.num_leds):
            x_coord = constellation.segments[led_index // constellation.segments[0].num_leds].leds[
                led_index % constellation.segments[0].num_leds].xCoord
            hue = ((x_coord + wave_progress) % wave_length) / wave_length
            color_hsv = (hue, 1, 1)  # Full saturation and value for a bright rainbow

            constellation.set_color_HSV(led_index, color_hsv)

        wave_progress += (speed / frequency)
        wave_progress %= wave_length
        return wave_progress

    def set_random_segments_color(self, color, fraction):
        if not 0 <= fraction <= 1:
            raise ValueError("Fraction should be a number between 0 and 1.")

        n = int(self.num_segments * fraction)
        selected_segments = random.sample(self.segments, n)

        for segment in selected_segments:
            segment.set_color_all(color)

        self.copy_segment_colors_to_data()



    def add_effect(self, effect):
        self.effects.append(effect)

    def run_effects(self, current_song_time):

        self.clear()

        for effect in self.effects:
            if effect.is_done(current_song_time):
                self.effects.remove(effect)
            else:
                effect.write(current_song_time)

        self.show()

    def clear(self):
        # for i in range(self.num_leds):
        #     self.color_data[i] = [0, 0, 0]


        for segment in self.segments:
            segment.set_color_all([0, 0, 0])

        self.copy_segment_colors_to_data()

    def __str__(self):
        return "Constellation with {} segments and {} LEDs".format(self.num_segments, self.num_leds)

    # print the x_start and y_start of each segment
    def print_XY_coords(self):
        for i in range(self.num_segments):
            self.segments[i].print_XY_coords()


    def show(self):
        for i, color in enumerate(self.color_data):
            # self.pixels2[i] = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
            self.pixels2[i] = (int(color[0]), int(color[1] * 1), int(color[2] * 1))
        self.pixels2.show()


class FillAllEffect:
    def __init__(self, constellation,start_time, duration, color):
        self.constellation = constellation
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.color = color

    def write(self, current_song_time):
        for led in range(self.constellation.num_leds):
            self.constellation.set_color_rgb(led, self.color)

    def is_done(self, current_song_time):
        if current_song_time >= self.end_time + 0.2:
            return True