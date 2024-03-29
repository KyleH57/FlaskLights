import socket
import time
import struct


# class for a WS2812 LED
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

    def initMathCoords(self, center):
        self.xMath = self.xCoord - center
        self.yMath = self.yCoord - center


class square_LED_panel:
    def __init__(self, num_leds_side, spacing):
        # spacing is the distance between the center of each LED in mm
        self.num_leds_side = num_leds_side
        self.spacing = spacing
        self.leds = []

        # find the center of the panel
        self.center = (num_leds_side - 1) * spacing / 2

        # 0,0 is the bottom left corner
        # the LED chain starts on the bottom row and goes left to right
        # The next row is above the first row and goes right to left
        # and so on
        for i in range(num_leds_side):
            for j in range(num_leds_side):
                if i % 2 == 0:
                    self.leds.append(WS2812LED(j * self.spacing, i * self.spacing))

                    # initialize the math coordinates
                    self.leds[-1].initMathCoords(self.center)
                else:
                    self.leds.append(WS2812LED((num_leds_side - j - 1) * self.spacing, i * self.spacing))

                    # initialize the math coordinates
                    self.leds[-1].initMathCoords(self.center)


class led_strip:
    def __init__(self, num_leds, spacing):
        # spacing is the distance between the center of each LED in mm
        self.num_leds = num_leds
        self.spacing = spacing
        self.leds = []

        # find the center of the panel
        self.center = (num_leds - 1) * spacing / 2

        # 0,0 is the bottom left corner
        # the LED chain starts on the bottom row and goes left to right
        # The next row is above the first row and goes right to left
        # and so on
        for i in range(num_leds):
            self.leds.append(WS2812LED(i * self.spacing, 0))

            # initialize the math coordinates
            self.leds[-1].initMathCoords(self.center)


# function that takes a panel object and a socket object and sends the data to the panel
def sendPanelData(led_panel, client_socket):
    binary_data = bytearray()
    for i in led_panel.leds:
        for j in i.color:
            binary_data.append(j)

    # Print sending data
    # print("Sending data...")
    # print(binary_data)
    client_socket.sendto(binary_data, (UDP_IP, UDP_PORT))


def sendPanelData2(socket_obj, value, led_panel):
    # print("Send data: " + str(value))
    socket_obj.settimeout(0.5)
    # Example uint64_t value
    # value = 1676857643023

    # Pack the value into a bytearray using the "Q" format code for unsigned long long (8 bytes)
    byte_array = struct.pack(">Q", value)  # big endian

    # create a bytearray 4336 bytes long (8 bytes for time, 8 bytes reserved, 4320 bytes for data) and fill it with 0s
    # big_byte_array = bytearray(4336)

    big_byte_array = bytearray(16)

    # copy the byte_array into the big_byte_array
    big_byte_array[0:len(byte_array)] = byte_array

    # # set the remaining bytes to 1
    # for i in range(len(byte_array), len(big_byte_array)):
    #     big_byte_array[i] = 20

    for i in led_panel.leds:
        for j in i.color:
            big_byte_array.append(j)

    # print the length of the bytearray should be 4336
    # print(len(big_byte_array))

    # Print the bytearray
    # print(big_byte_array)

    # send the message
    socket_obj.send(big_byte_array)

    return

def sendPanelData3(value, led_panel):
    # specify the server's IP address and port number
    server_address = ('192.168.0.123', 80)

    # create a TCP socket object
    socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect to the server
    socket_obj.connect(server_address)
    print("tcp_connect: Connected to server")

    # print("Send data: " + str(value))
    socket_obj.settimeout(0.5)
    # Example uint64_t value
    # value = 1676857643023

    # Pack the value into a bytearray using the "Q" format code for unsigned long long (8 bytes)
    byte_array = struct.pack(">Q", value)  # big endian

    # create a bytearray 4336 bytes long (8 bytes for time, 8 bytes reserved, 4320 bytes for data) and fill it with 0s
    # big_byte_array = bytearray(4336)

    big_byte_array = bytearray(16)

    # copy the byte_array into the big_byte_array
    big_byte_array[0:len(byte_array)] = byte_array

    # # set the remaining bytes to 1
    # for i in range(len(byte_array), len(big_byte_array)):
    #     big_byte_array[i] = 20

    for i in led_panel.leds:
        for j in i.color:
            big_byte_array.append(j)

    # print the length of the bytearray should be 4336
    # print(len(big_byte_array))

    # Print the bytearray
    # print(big_byte_array)

    # send the message
    print("Sending data...")
    socket_obj.send(big_byte_array)

    return

def check_queue(socket_obj):
    # print("Checking queue...")
    socket_obj.settimeout(0.01)

    # try catch to receive data back
    try:
        data = socket_obj.recv(1)
        # convert from bytes to int
        data = int.from_bytes(data, byteorder='big')

        # print("Finished checking queue.")

        return data

    except TimeoutError:
        # print("No data received")

        return 0


def tcp_connect():
    # specify the server's IP address and port number
    server_address = ('192.168.0.123', 80)

    # create a TCP socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect to the server
    client_socket.connect(server_address)
    print("tcp_connect: Connected to server")

    return client_socket


def tcp_disconnect(client_socket):
    client_socket.close()


# set the color of all LEDs in the panel
def setPanelColor(color, led_panel):
    for i in led_panel.leds:
        i.setColor(color)


# draw a circle at the given x and y coordinates with the given radius
def drawCircle(x, y, radius, color, led_panel):
    for i in led_panel.leds:
        if (i.xMath - x) ** 2 + (i.yMath - y) ** 2 < radius ** 2:
            i.setColor(color)


# draw a ring at the given x and y coordinates with the given radius and width
def drawRing(x, y, radius, width, color, led_panel):
    for i in led_panel.leds:
        if radius ** 2 > (i.xMath - x) ** 2 + (i.yMath - y) ** 2 > (
                radius - width) ** 2:
            i.setColor(color)


# draw and send an animated ring given the center coordinates, radius, width, color, frame rate, and duration
def drawAnimatedRing(x, y, radius, width, color, frame_rate, duration, led_panel, client_socket):
    # radius starts at 0 and increases to radius
    # calculate the number of frames
    num_frames = int(frame_rate * duration)

    for i in range(num_frames):
        # clear the panel
        setPanelColor([0, 0, 0], led_panel)

        # draw the ring
        drawRing(x, y, i * radius / num_frames, width, color, led_panel)

        # send the data
        sendPanelData(led_panel, client_socket)

        # wait
        time.sleep(1 / frame_rate)

    # clear the panel
    setPanelColor([0, 0, 0], led_panel)
    sendPanelData(led_panel, client_socket)


# function that takes a list and turns on leds on each column based on the number in the list
# draw every other column in reverse
# draw the columns in reverse order
def drawColumns(columnList, led_panel, client_socket, color):
    # reverse the list
    columnList.reverse()

    for i in range(len(columnList)):
        if i % 2 == 0:
            for j in range(columnList[i]):
                led_panel.leds[i * led_panel.num_leds_side + j].setColor(color)
        else:
            for j in range(columnList[i]):
                led_panel.leds[i * led_panel.num_leds_side + led_panel.num_leds_side - j - 1].setColor(color)
    sendPanelData(led_panel, client_socket)


# function to clear the panel
def clearPanel(led_panel, client_socket):
    setPanelColor([0, 0, 0], led_panel)
    sendPanelData(led_panel, client_socket)


# DO NOT DELETE
UDP_IP = "192.168.0.140"
UDP_PORT = 4210
# END DO NOT DELETE


#
# #
# # # constant for frame rate
# # FRAME_RATE = 24
#
# p1 = square_LED_panel(8, 10)
# setPanelColor([0, 0, 0], p1)
#
# UDP_IP = "192.168.0.156"
# UDP_PORT = 4210
#
# # Create a socket object
# client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
# # #draw a circle
# # for i in p1.leds:
# #     if i.xMath**2 + i.yMath**2 < 200:
# #         i.setColor([0, 10, 0])
#
# # drawCircle(0, 20, 30, [0, 5, 0], p1)
#
# # drawRing(0, 20, 30, 10, [0, 5, 0], p1)
# # sendPanelData(p1, client_socket)
#
# #Time code to see how long it takes
# drawAnimatedRing(0, 20, 100, 20, [0, 0, 5], FRAME_RATE, .6, p1, client_socket)
#
# drawAnimatedRing(0, 10, 50, 15, [5, 0, 0], FRAME_RATE, .4, p1, client_socket)
#
# drawAnimatedRing(-50, -50, 200, 15, [0, 5, 0], FRAME_RATE, 1, p1, client_socket)
#
#
# #drawColumn(test51[1], p1, client_socket)
#
# # Close the socket
# client_socket.close()
