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
        self.total_length = (num_leds - 1) * spacing + 2 * edge_spacing

        # calculate end point of segment
        x_end = x_start + self.total_length * math.cos(self.angle)
        y_end = y_start + self.total_length * math.sin(self.angle)

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

    def get_total_length(self):
        return self.total_length

    def print_XY_coords(self):
        # print the x_start and y_start of the segment rounded to 1 decimal place
        print("x_start: {:.1f}, y_start: {:.1f}".format(self.x_start, self.y_start))

    def __str__(self):
        return "LED segment starting at ({}, {}) with {} LEDs spaced {} units apart at an angle of {} degrees".format(
            self.x_start, self.y_start, self.num_leds, self.spacing, math.degrees(self.angle))


class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.segments = []
        self.neighbors = []
        self.is_hex_start = False
        self.hex_segments = []

    def __eq__(self, other, tolerance=1e-6):
        return abs(self.x - other.x) < tolerance and abs(self.y - other.y) < tolerance

    def add_segment(self, segment):
        self.segments.append(segment)

    def add_neighbor(self, neighbor):
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)

    def __str__(self):
        hex_start_str = " [Hex Start]" if self.is_hex_start else ""
        return f"Node at ({self.x}, {self.y}) with {len(self.segments)} segments and {len(self.neighbors)} neighbors{hex_start_str}"



class constellation:
    def __init__(self, angles, num_leds_segment, spacing, edge_spacing, brightness, debug=False):
        print("Initializing constellation...")
        self.angles = angles.split(',')
        self.num_segments = len(self.angles)
        self.segments = []  # list of led_segment objects

        # graph stuff
        self.nodes = []  # list of nodes
        self.special_nodes = []

        x_start, y_start = 0, 0

        # array of all currently playing effects
        self.effects = []

        prev_node = None
        for angle_str in self.angles:
            angle = int(angle_str[:-1]) if 'r' in angle_str else int(angle_str)
            segment = led_segment(x_start, y_start, angle, num_leds_segment, spacing, edge_spacing)
            self.segments.append(segment)
            if 'r' not in angle_str:
                start_node = self.add_node(Node(segment.x_start, segment.y_start))
                end_node = self.add_node(Node(segment.x_end, segment.y_end))
                start_node.add_segment(segment)
                end_node.add_segment(segment)

                if prev_node:
                    start_node.add_neighbor(prev_node)
                    prev_node.add_neighbor(start_node)

                prev_node = end_node
                x_start, y_start = segment.x_end, segment.y_end

        self.num_leds = self.num_segments * num_leds_segment
        self.color_data = [[0, 0, 0] for i in range(self.num_leds)]

        # # Debug: print node segment start and end points
        # if debug:
        #     for node in self.nodes:
        #         print("Node at ({:.1f}, {:.1f})".format(node.x, node.y))
        #         for segment in node.segments:
        #             print("  Segment from ({:.1f}, {:.1f}) to ({:.1f}, {:.1f})".format(
        #                 segment.x_start, segment.y_start, segment.x_end, segment.y_end))


        # calculate search distance for special nodes
        segment_total_len = self.segments[0].get_total_length()
        SEARCH_DISTANCE = segment_total_len * 2

        # Look for special nodes
        TOLERANCE = 1
        for node in self.nodes:
            neighbor_count = 0
            for neighbor in self.nodes:
                x_diff = neighbor.x - node.x
                y_diff = abs(neighbor.y - node.y)

                if (0 < -x_diff <= SEARCH_DISTANCE + TOLERANCE and
                        0 <= y_diff <= SEARCH_DISTANCE / 2 + TOLERANCE):
                    neighbor_count += 1

            if neighbor_count == 5:
                node.is_hex_start = True
                self.special_nodes.append(node)

        # Debug: print segment information while populating hex segments
        if debug:
            print("\nPopulating hex segments:")
        for node in self.special_nodes:
            for segment in self.segments:
                start_x_rel = segment.x_start - node.x
                end_x_rel = segment.x_end - node.x
                start_y_rel = segment.y_start - node.y
                end_y_rel = segment.y_end - node.y
                if (-SEARCH_DISTANCE - TOLERANCE <= start_x_rel <= 0 + TOLERANCE and
                        -SEARCH_DISTANCE - TOLERANCE <= end_x_rel <= 0 + TOLERANCE and
                        -SEARCH_DISTANCE / 2 - TOLERANCE <= start_y_rel <= SEARCH_DISTANCE / 2 + TOLERANCE and
                        -SEARCH_DISTANCE / 2 - TOLERANCE <= end_y_rel <= SEARCH_DISTANCE / 2 + TOLERANCE):

                    node.hex_segments.append(segment)
                    if debug:
                        print(
                            f"  Node at ({node.x}, {node.y}): added segment from ({segment.x_start}, {segment.y_start}) to ({segment.x_end}, {segment.y_end})")

            if len(node.hex_segments) != 6:
                raise ValueError(f"Special node at ({node.x}, {node.y}) does not have exactly 6 segments")



        # combine color data from all segments into one array
        for i in range(self.num_segments):
            for j in range(num_leds_segment):
                index = i * num_leds_segment + j
                self.color_data[index] = self.segments[i].get_color(j)

        self.pixels2 = neopixel.NeoPixel(board.D18, self.num_leds, brightness=brightness, auto_write=False)

        self.clear()

        print("Constellation initialized.")

        # print number of nodes
        print(f"Number of nodes: {len(self.nodes)}")

        # print special nodes
        print(f"Special nodes: {len(self.special_nodes)}")

    def set_hex_segments_color(self, index, color):
        if 0 <= index < len(self.special_nodes):
            special_node = self.special_nodes[index]
            for hex_segment in special_node.hex_segments:
                hex_segment.set_color_all(color)
                for i, segment in enumerate(self.segments):
                    if hex_segment == segment:
                        self.segments[i] = hex_segment

    def add_node(self, new_node):
        for existing_node in self.nodes:
            if existing_node == new_node:
                return existing_node
        self.nodes.append(new_node)
        return new_node

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

        for effect in self.effects:
            effect.write(current_song_time)


        # self.copy_segment_colors_to_data()


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
            self.pixels2[i] = (int(color[0]), int(color[1] * 1), int(color[2] * 1))
        self.pixels2.show()


class FillAllEffect:
    def __init__(self, constellation, start_time, duration, color):
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
