import math
import board
import neopixel

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
    def __init__(self, x_start, y_start, angle, num_leds, spacing, edge_spacing=0):
        self.x_start = x_start
        self.y_start = y_start
        self.angle = angle
        self.num_leds = num_leds
        self.spacing = spacing
        self.edge_spacing = edge_spacing
        self.leds = []

        # calculate total length of segment
        total_length = (num_leds - 1) * spacing + 2 * edge_spacing

        # calculate end point of segment
        x_end = x_start + total_length * math.cos(angle)
        y_end = y_start + total_length * math.sin(angle)

        # create list of LED objects with calculated coordinates
        for i in range(num_leds):
            x = x_start + i * spacing * math.cos(angle) + edge_spacing * math.cos(angle)
            y = y_start + i * spacing * math.sin(angle) + edge_spacing * math.sin(angle)
            self.leds.append(WS2812LED(x, y))

        self.x_end = x_end
        self.y_end = y_end

    def set_color(self, index, color):
        self.leds[index].setColor(color)

    def get_color(self, index):
        return self.leds[index].color

    def __str__(self):
        return "LED segment starting at ({}, {}) with {} LEDs spaced {} units apart at an angle of {} degrees".format(
            self.x_start, self.y_start, self.num_leds, self.spacing, math.degrees(self.angle))


class constellation:
    def __init__(self, num_segments, num_leds_segment, spacing, edge_spacing):
        self.segments = [led_segment(0, 0, i * 2 * math.pi / num_segments, num_leds_segment, spacing, edge_spacing) for i in
                         range(num_segments)]
        self.num_segments = num_segments
        self.num_leds = num_segments * num_leds_segment


        self.pixels2 = neopixel.NeoPixel(board.D18, self.num_leds, brightness=0.2, auto_write=False)

    def set_led_color(self, index, color):
        self.pixels2[index] = color

    def get_color_data(self):
        return self.pixels2

    def show(self):
        self.pixels2.show()

    def set_segment_color(self, segment_index, color):
        start_index = segment_index * self.segments[0].num_leds
        end_index = start_index + self.segments[0].num_leds
        for i in range(start_index, end_index):
            self.pixels2[i] = color

    def clear(self):
        self.pixels2.fill((0, 0, 0))

    def __str__(self):
        return "Constellation with {} segments and {} LEDs".format(self.num_segments, self.num_leds)
