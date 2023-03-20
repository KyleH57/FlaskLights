import math
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

    def set_color(self, index, color):
        self.leds[index].setColor(color)

    def get_color(self, index):
        return self.leds[index].color


    def print_XY_coords(self):
        # print the x_start and y_start of the segment rounded to 1 decimal place
        print("x_start: {:.1f}, y_start: {:.1f}".format(self.x_start, self.y_start))



    def __str__(self):
        return "LED segment starting at ({}, {}) with {} LEDs spaced {} units apart at an angle of {} degrees".format(
            self.x_start, self.y_start, self.num_leds, self.spacing, math.degrees(self.angle))


class constellation:
    def __init__(self, angles, num_leds_segment, spacing, edge_spacing, brightness):
        self.angles = [int(angle) for angle in angles.split(',')]
        self.num_segments = len(self.angles)
        self.segments = []
        x_start, y_start = 0, 0

        for angle in self.angles:
            segment = led_segment(x_start, y_start, angle, num_leds_segment, spacing, edge_spacing)
            self.segments.append(segment)
            x_start, y_start = segment.x_end, segment.y_end

        self.num_leds = self.num_segments * num_leds_segment
        self.color_data = [[0, 0, 0] for i in range(self.num_leds)]

        # combine color data from all segments into one array
        for i in range(self.num_segments):
            for j in range(num_leds_segment):
                index = i * num_leds_segment + j
                self.color_data[index] = self.segments[i].get_color(j)

        self.pixels2 = neopixel.NeoPixel(board.D18, self.num_leds, brightness=brightness, auto_write=False)

    def set_color(self, segment_index, led_index, color):
        self.segments[segment_index].set_color(led_index, color)
        index = segment_index * self.segments[0].num_leds + led_index
        self.color_data[index] = color

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
        color = colorsys.hsv_to_rgb(color[0], color[1], color[2])

        self.color_data[led_index] = color

    def get_color(self, segment_index, led_index):
        return self.segments[segment_index].get_color(led_index)

    def set_segment_color(self, segment_index, color):
        start_index = segment_index * self.segments[0].num_leds
        end_index = start_index + self.segments[0].num_leds
        for i in range(start_index, end_index):
            self.set_color(segment_index, i - start_index, color)

    def get_LED(self, led_index):
        # check if led_index is valid
        if led_index < 0 or led_index >= self.num_leds:
            return None

        return self.color_data[led_index]

    def rainbow_wave_x(constellation, wave_length, frequency, wave_progress):
        for led_index in range(constellation.num_leds):
            x_coord = constellation.segments[led_index // constellation.segments[0].num_leds].leds[
                led_index % constellation.segments[0].num_leds].xCoord
            hue = ((x_coord + wave_progress) % wave_length) / wave_length
            color_hsv = (hue, 1, 1)  # Full saturation and value for a bright rainbow

            constellation.set_color_HSV(led_index, color_hsv)

        # Update the colors of the LEDs
        for i, color in enumerate(constellation.color_data):
            constellation.pixels2[i] = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))

        # constellation.pixels2.show()

        wave_progress += wave_length / frequency
        wave_progress %= wave_length
        return wave_progress

    def __str__(self):
        return "Constellation with {} segments and {} LEDs".format(self.num_segments, self.num_leds)

    # print the x_start and y_start of each segment
    def print_XY_coords(self):
        for i in range(self.num_segments):
            self.segments[i].print_XY_coords()


    def show(self):
        for i, color in enumerate(self.color_data):
            self.pixels2[i] = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
        self.pixels2.show()
