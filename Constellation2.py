import math
import platform
import matplotlib.pyplot as plt
import board
import neopixel
import colorsys


def is_near(point1, point2, tolerance=1):
    """
    Check if two points are within a certain distance of each other on the real number line or in the 2D coordinate plane.

    Args:
        point1 (tuple or float): The coordinates of the first point. If R1, point1 is a float.
        If R2, point1 is a tuple of two floats (x, y).
        point2 (tuple or float): The coordinates of the second point. If R1, point2 is a float.
        If R2, point2 is a tuple of two floats (x, y).
        tolerance (float): The maximum distance between the two points to be considered "near".
            Default value is 1.

    Returns:
        bool: True if the two points are within the tolerance distance of each other, False otherwise.
    """
    if isinstance(point1, tuple) and isinstance(point2, tuple):
        # R2 case - calculate Euclidean distance
        x1, y1 = point1
        x2, y2 = point2
        distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    else:
        # R1 case - calculate absolute distance
        distance = abs(point1 - point2)
    return distance <= tolerance


class WS2812LED:
    def __init__(self, xCoord, yCoord):
        self.xCoord = xCoord
        self.yCoord = yCoord

        self.xCoord_centroid = None
        self.yCoord_centroid = None

        self.color = [0, 0, 0]

    def __str__(self):
        return ("LED at " + str(self.xCoord) + ", " + str(self.yCoord) +
                " centroid at " + str(self.xCoord_centroid) + ", " +
                str(self.yCoord_centroid) + " with color " + str(self.color))

    def set_color(self, color):
        # Check if each color value is within [0, 255]
        if not (0 <= color[0] <= 255 and 0 <= color[1] <= 255 and 0 <= color[2] <= 255):
            print(color)
            raise ValueError("Color values must be in the range [0, 255]")
        self.color = color

    def get_color(self):
        return self.color

    def set_centroid(self, x, y):
        self.xCoord_centroid = x
        self.yCoord_centroid = y



class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.x_centroid = None
        self.y_centroid = None

        self.segment_neighbors = []
        self.neighbor_nodes = []
        self.is_hex_start = False
        self.hex_segments = []

        self.node_index = None

        self.hex_segments = []

    def __repr__(self):
        return f"Node({self.x}, {self.y})"


class Segment:
    def __init__(self, x_start, y_start, angle_degrees, num_leds, spacing, edge_spacing, start_index, panel):
        self.x_start = x_start
        self.y_start = y_start

        self.angle = math.radians(angle_degrees)  # pay attention to units
        self.num_leds = num_leds
        self.spacing = spacing
        self.edge_spacing = edge_spacing
        self.start_index = start_index

        self.panel = panel  # reserved for future use

        # calculate total length of segment
        self.total_length = (num_leds - 1) * spacing + 2 * edge_spacing

        # calculate end point of segment
        self.x_end = x_start + self.total_length * math.cos(self.angle)
        self.y_end = y_start + self.total_length * math.sin(self.angle)

        self.start_node = None
        self.end_node = None

    def __repr__(self):
        return f"Segment({self.x_start}, {self.y_start}, {math.degrees(self.angle)}, {self.num_leds}, {self.spacing}, {self.edge_spacing}, {self.start_index}, {self.panel})"


class VolumeBar:
    def __init__(self, constellation, segment_indices, num_leds_segment):
        self.led_indices = []
        self.sorted_led_indices = []
        for i in range(len(segment_indices)):
            for j in range(num_leds_segment):
                self.led_indices.append((segment_indices[i] + 0) * num_leds_segment + j)

        # create a list of led indices sorted by led.yCoord
        self.sorted_led_indices = sorted(self.led_indices, key=lambda x: constellation.leds[x].yCoord)


class Hexagon:
    def __init__(self, hex_node, constellation):
        self.constellation = constellation
        self.hex_segments = self.constellation.find_hex_segments(hex_node)
        self.led_indices = []  # only contains the start index of each segment
        self.led_angle_coords = []  # 2d list that contains angle in radians relative to the hex centroid and led index
        self.centroid_x = hex_node.x - self.constellation.segments[0].total_length - self.constellation.centroid_x
        self.centroid_y = hex_node.y - self.constellation.centroid_y
        self.num_leds = 6 * self.constellation.num_leds_segment

        for i in range(len(self.hex_segments)):
            self.led_indices.append(self.hex_segments[i].start_index)

        # set all led angle coordinates
        for i in self.led_indices:
            for j in range(self.constellation.num_leds_segment):
                led = self.constellation.leds[i + j]
                led_x = led.xCoord_centroid - self.centroid_x
                led_y = led.yCoord_centroid - self.centroid_y
                angle = math.atan2(led_y, led_x)

                if angle < 0:
                    angle += 2 * math.pi

                self.led_angle_coords.append([angle, i + j, led_x, led_y])

        # sort led angle coordinates by ascending angle
        self.led_angle_coords.sort(key=lambda x: x[0])

    def debug(self):
        print("Hexagon centroid: " + str(self.centroid_x) + ", " + str(self.centroid_y))
        print("Hexagon led indices: " + str(self.led_indices))
        print("Hexagon led angle coordinates: " + str(self.led_angle_coords))


class Constellation:
    def __init__(self, angles, num_leds_segment, spacing, edge_spacing, brightness):
        self.angles = angles.split(',')
        self.repeat_flags = ['r' in angle for angle in angles.split(',')]
        self.num_leds_segment = num_leds_segment
        self.spacing = spacing
        self.edge_spacing = edge_spacing
        self.brightness = brightness
        self.centroid_x = None
        self.centroid_y = None

        # initialize min and max values
        self.min_x = float('inf') # rightmost led in the centroid coordinate system
        self.max_x = float('-inf')
        self.min_y = float('inf')
        self.max_y = float('-inf')


        self.segments = []
        self.nodes = []
        self.leds = []  # WS2812LED objects
        self.hexagons = []
        self.volume_bars = []
        self.num_leds = 0

        self.effects = []  # list of currently running effects
        self.overlays = []  # list of currently running overlays

        self._create_constellation()

        for segment in self.segments:
            for i in range(segment.num_leds):
                x = segment.x_start + (i * segment.spacing + segment.edge_spacing) * math.cos(segment.angle)
                y = segment.y_start + (i * segment.spacing + segment.edge_spacing) * math.sin(segment.angle)
                led = WS2812LED(x, y)
                self.leds.append(led)

        # now that leds are created, calculate centroids
        for led in self.leds:
            led.xCoord_centroid = led.xCoord - self.centroid_x
            led.yCoord_centroid = led.yCoord - self.centroid_y

            # update min and max x and y values
            if led.xCoord_centroid < self.min_x:
                self.min_x = led.xCoord_centroid
            if led.xCoord_centroid > self.max_x:
                self.max_x = led.xCoord_centroid
            if led.yCoord_centroid < self.min_y:
                self.min_y = led.yCoord_centroid
            if led.yCoord_centroid > self.max_y:
                self.max_y = led.yCoord_centroid

        # populate the hexagons list
        stuff5623 = self.find_hexagons()

        # populate the volume bars list
        # hard coded for now
        self.volume_bars.append(VolumeBar(self, [2, 3, 5, 6, 8, 9], self.num_leds_segment))

        for hex_node in stuff5623:
            self.hexagons.append(Hexagon(hex_node, self))

    def _create_constellation(self):
        print("Creating constellation...")
        print("Segment length: " + str(self.edge_spacing * 2 + (self.num_leds_segment - 1) * self.spacing))
        x, y = 0, 0
        prev_node = None
        counter = 0
        for angle_str in self.angles:
            angle = float(angle_str.strip('r'))
            segment = Segment(x, y, angle, self.num_leds_segment, self.spacing, self.edge_spacing,
                              self.num_leds_segment * counter, None)
            self.segments.append(segment)
            self.num_leds += segment.num_leds

            counter += 1
            # node at the beginning of the segment
            start_node = self._find_or_create_node(segment.x_start, segment.y_start)
            # node at the end of the segment
            end_node = self._find_or_create_node(segment.x_end, segment.y_end)

            segment.start_node = start_node
            segment.end_node = end_node

            if 'r' not in angle_str:  # if not a reversed segment

                # add segments to nodes
                start_node.segment_neighbors.append(segment)
                end_node.segment_neighbors.append(segment)

                # if not first node?
                # if prev_node:
                # set the neighbor of the node at the beginning of the current
                # segment to the node at the end of the current segment
                start_node.neighbor_nodes.append(end_node)

                # set the neighbor of the node at the end of the current segment
                # to the node at the beginning of the current segment
                end_node.neighbor_nodes.append(start_node)

                # prev_node.neighbor_nodes.append(end_node)

                prev_node = end_node
                x, y = segment.x_end, segment.y_end
            else:  # if a reversed segment
                # start_node = prev_node
                # end_node = prev_node

                start_node.neighbor_nodes.append(end_node)
                end_node.neighbor_nodes.append(start_node)

                start_node.segment_neighbors.append(segment)
                end_node.segment_neighbors.append(segment)

                end_node = start_node
        # end of segment initialization

        self.pixels = neopixel.NeoPixel(board.D18, self.num_leds, brightness=self.brightness, auto_write=False)

        self.centroid_x, self.centroid_y = self.find_centroid()

        for node in self.nodes:
            node.x_centroid = node.x - self.centroid_x
            node.y_centroid = node.y - self.centroid_y

            # set node indices
            node.node_index = self.nodes.index(node)

        # self.update_neighbor_lists()  # this adds nodes to the start and endpoints of each segment

        for segment in self.segments:
            segment.x_start_centroid = segment.x_start - self.centroid_x
            segment.y_start_centroid = segment.y_start - self.centroid_y
            segment.x_end_centroid = segment.x_end - self.centroid_x
            segment.y_end_centroid = segment.y_end - self.centroid_y

    def _find_or_create_node(self, x, y):
        for node in self.nodes:
            if is_near((node.x, node.y), (x, y)):
                return node
        new_node = Node(x, y)

        # get number of nodes
        new_node.node_index = len(self.nodes)
        self.nodes.append(new_node)
        return new_node

    def print_node_neighbors(self):
        for i, node in enumerate(self.nodes):
            print(f"Node {node.node_index}: ({node.x:.0f}, {node.y:.0f})")

            neighbor_nodes = []
            for neighbor_node in node.neighbor_nodes:
                neighbor_nodes.append(f"{neighbor_node.node_index}| ({neighbor_node.x:.0f}, {neighbor_node.y:.0f})")
            print(f"  Neighbor Nodes: {', '.join(neighbor_nodes)}")

            neighbor_segments = []
            for neighbor_segment in node.segment_neighbors:
                start_x, start_y = neighbor_segment.x_start, neighbor_segment.y_start
                end_x, end_y = neighbor_segment.x_end, neighbor_segment.y_end
                neighbor_segments.append(f"({start_x:.0f}, {start_y:.0f}) -> ({end_x:.0f}, {end_y:.0f})")
            print(f"  Neighbor Segments: {', '.join(neighbor_segments)}")
            print()

    def print_segment_debug_data(self):
        print("Printing segment debug data...")
        for i, segment in enumerate(self.segments):
            print(f"Segment {i}:")
            print(f"  Start coordinates: ({segment.x_start:.2f}, {segment.y_start:.2f})")
            print(f"  End coordinates: ({segment.x_end:.2f}, {segment.y_end:.2f})")
            # print(f"  Angle: {segment.angle:.2f} rad?")
            print(f"  Length: {segment.total_length:.2f}")
            print(f"  Start node index: {segment.start_node.node_index}")
            print(f"  End node index: {segment.end_node.node_index}")
            print("")

    # generates a list of all the special hexagon nodes
    def find_hexagons(self):
        segment_length = self.segments[0].total_length
        hexagon_list = []

        for node in self.nodes:
            x, y = node.x, node.y
            nearby_node = self.get_nearby_node(x - segment_length * 2, y)
            if nearby_node is not None:
                lower_y_node = self.get_nearby_node(x - segment_length / 2, y - segment_length * math.sqrt(3) / 2)
                higher_y_node = self.get_nearby_node(x - segment_length / 2, y + segment_length * math.sqrt(3) / 2)
                if lower_y_node is not None and higher_y_node is not None:
                    hexagon_list.append(node)

        return hexagon_list

    # generates a list of all the centroids of the hexagons in the list that is passed in
    def find_orange_dots(self, hexagon_list):
        segment_length = self.segments[0].total_length
        orange_dots = []

        for node in hexagon_list:
            x, y = node.x, node.y
            orange_dots.append((x - segment_length, y))

        return orange_dots

    # a
    def find_hex_segments(self, node):
        hex_segments = []
        current_node = node

        for i in range(6):
            # Find the next node depending on the iteration

            if i == 0:
                # Find node with largest Y
                next_node = max(current_node.neighbor_nodes, key=lambda n: n.y)
            elif i == 1:
                # Find node with smallest X
                next_node = min(current_node.neighbor_nodes, key=lambda n: n.x)
            elif i == 2 or i == 3:
                # Find node with smallest Y
                next_node = min(current_node.neighbor_nodes, key=lambda n: n.y)
            elif i == 4:
                # Find node with largest X
                next_node = max(current_node.neighbor_nodes, key=lambda n: n.x)
            elif i == 5:
                # Find node with largest Y
                next_node = max(current_node.neighbor_nodes, key=lambda n: n.y)

            # Find the segment connecting current_node and next_node
            for segment in current_node.segment_neighbors:
                if (is_near((segment.start_node.x, segment.start_node.y), (next_node.x, next_node.y)) and
                    is_near((segment.end_node.x, segment.end_node.y), (current_node.x, current_node.y))) or \
                        (is_near((segment.start_node.x, segment.start_node.y), (current_node.x, current_node.y)) and
                         is_near((segment.end_node.x, segment.end_node.y), (next_node.x, next_node.y))):
                    hex_segments.append(segment)
                    break

            current_node = next_node

        return hex_segments

    def get_hexagon_led_indices(constellation, hexagon_number):
        hexagons = constellation.find_hexagons()
        if hexagon_number in hexagons:
            return hexagons[hexagon_number]
        else:
            return []

    def get_nearby_node(self, x, y):
        for node in self.nodes:
            if is_near((x, y), (node.x, node.y)):
                return node
        return None

    def update_neighbor_lists(self):
        print("Updating neighbor lists...")
        for segment in self.segments:
            start_node = segment.start_node
            end_node = segment.end_node

            # problem?
            if start_node not in end_node.neighbor_nodes:
                end_node.neighbor_nodes.append(start_node)

                # print debug info
                print("Adding node" + str(start_node.node_index) + " to node" + str(
                    end_node.node_index) + "'s neighbor list")

            if end_node not in start_node.neighbor_nodes:
                start_node.neighbor_nodes.append(end_node)

    def find_centroid(self):
        x_sum, y_sum = 0, 0
        num_nodes = len(self.nodes)

        for node in self.nodes:
            x_sum += node.x
            y_sum += node.y

        centroid_x = x_sum / num_nodes
        centroid_y = y_sum / num_nodes

        return centroid_x, centroid_y

    def plot_constellation(self):
        fig, ax = plt.subplots()

        orange_dots = self.find_orange_dots(self.find_hexagons())
        i = 0
        for x, y in orange_dots:
            plt.scatter(x, y, c='orange', s=10, zorder=4)
            plt.text(x, y, i, fontsize=8, color='orange')
            i += 1

        centroid_x, centroid_y = self.find_centroid()
        plt.plot(centroid_x, centroid_y, 'mo', markersize=10, label='Centroid')
        plt.legend()

        for i, segment in enumerate(self.segments):
            plt.plot([segment.x_start, segment.x_end], [segment.y_start, segment.y_end], 'k-')
            plt.plot((segment.x_start + segment.x_end) / 2, (segment.y_start + segment.y_end) / 2, 'ro')
            plt.text((segment.x_start + segment.x_end) / 2, (segment.y_start + segment.y_end) / 2, f'{i}', fontsize=8,
                     color='r')

        for i, node in enumerate(self.nodes):
            plt.plot(node.x, node.y, 'go')
            plt.text(node.x, node.y, f'{i}', fontsize=8, color='g')

        plt.axis('equal')

        if platform.system() == 'Linux':
            plt.savefig('constellation_plot.png', dpi=300)
            print('Plot saved as constellation_plot.png')
        else:
            plt.show()

    def plot_constellation_centroid(self):
        fig, ax = plt.subplots()

        for segment in self.segments:
            plt.plot([segment.x_start_centroid, segment.x_end_centroid],
                     [segment.y_start_centroid, segment.y_end_centroid], 'r-')
            plt.plot(segment.x_start_centroid, segment.y_start_centroid, 'ro')

        for node in self.nodes:
            plt.plot(node.x_centroid, node.y_centroid, 'bo')
            plt.annotate(f"({int(node.x_centroid)}, {int(node.y_centroid)})", (node.x_centroid, node.y_centroid),
                         textcoords="offset points", xytext=(-15, 7), fontsize=8, color='blue')

        plt.axhline(0, color='grey', linewidth=0.5)
        plt.axvline(0, color='grey', linewidth=0.5)
        plt.xlabel('X Coordinate (Centroid System)')
        plt.ylabel('Y Coordinate (Centroid System)')
        plt.title('Constellation Plot (Centroid Coordinate System)')

        if platform.system() == 'Linux':
            plt.savefig('constellation_plot_centroid.png', dpi=300)
            print('Plot saved as constellation_plot_centroid.png')
        else:
            plt.show()

    def set_single_led(self, led_index, color):
        self.leds[led_index].set_color(color)

    def clear(self):
        # set all leds to black
        for i in range(self.num_leds):
            self.leds[i].set_color([0, 0, 0])

    def add_effect(self, effect):
        self.effects.append(effect)

    def remove_all_effects(self):
        self.effects = []

    def run_effects(self, current_song_data):  # do not delete, needed for backwards compatibility with idle rainbow

        self.clear()

        # check if any effects are done and remove them
        for effect in self.effects:
            if effect.is_done(current_song_data):
                self.effects.remove(effect)

        # run all remaining effects
        for effect in self.effects:
            effect.run(current_song_data)

        # copy data from leds to pixels
        for i in range(self.num_leds):
            self.pixels[i] = self.leds[i].get_color()

        # write data to pixels
        self.pixels.show()

    def run_effects2(self, song_object, debug=False):

        self.clear()

        count = 0  # initialize a counter variable

        # check if any effects are done and remove them
        for effect in self.effects:
            if effect.is_done(song_object.current_song_time):
                self.effects.remove(effect)

        effect_layers = {}
        max_layer = -1  # initialize max layer number to -1

        # group effects by layer number and find max layer number
        for effect in self.effects:
            if effect.layer not in effect_layers:
                effect_layers[effect.layer] = []
            effect_layers[effect.layer].append(effect)
            max_layer = max(max_layer, effect.layer)

        # loop through all layers from 0 to max_layer
        for layer in range(max_layer + 1):
            if layer in effect_layers:
                for effect in effect_layers[layer]:
                    if effect.start_time <= song_object.current_song_time <= effect.end_time:
                        effect.run(song_object.current_song_time)
                        count += 1  # increment the counter each time an effect is run

                        if debug:
                            print(effect.color_params, effect.start_time, effect.end_time, count, song_object.current_song_time)

        # copy data from leds to pixels
        for i in range(self.num_leds):
            self.pixels[i] = self.leds[i].get_color()

        # write data to pixels
        self.pixels.show()

