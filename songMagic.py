import colorsys
import random
import time

import numpy as np

import effects as ef


def next_color(max_brightness, last_color, min_advance=13, max_advance=43):
    # convert last color to hsv
    last_color = colorsys.rgb_to_hsv(last_color[0] / 255, last_color[1] / 255, last_color[2] / 255)
    h_old = last_color[0]
    h = h_old + random.randrange(min_advance, max_advance) / 100
    if h > 1:
        h -= 1
    r, g, b = colorsys.hsv_to_rgb(h, 1, max_brightness)
    return [int(r * 255), int(g * 255), int(b * 255)]


class Song:
    def __init__(self, constellation, local_timestamp, current_song_timeAPI, song_title, song_id, total_duration,
                 sections, bars, beats, segments, tatums, time_signature=4):
        self.constellation = constellation
        self.local_timestamp = local_timestamp
        self.current_song_timeAPI = current_song_timeAPI
        self.song_title = song_title
        self.song_id = song_id
        self.total_duration = total_duration

        self.sections = sections
        self.bars = bars
        self.beats = beats
        self.segments = segments
        self.tatums = tatums

        self.time_signature = time_signature

        self.mapped_song = False

        self.current_song_time = 0  # used when playing song

        self.current_section = 0
        self.last_section = None

        self.current_beat = None
        self.current_beat_index = 0
        self.last_beat = None

        self.current_segment = None
        self.current_segment_index = 0
        self.last_segment = None




        # Calculate the 2.5th and 97.5th percentiles
        timbre_data = np.array([segment["timbre"][0] for segment in self.segments])
        self.lower_bound = np.percentile(timbre_data, 2.5)
        self.upper_bound = np.percentile(timbre_data, 97.5)  #TODO: need to update for x2-12
        self.range = self.upper_bound - self.lower_bound


        self.section_color = [255, 0, 0]
        self.color2 = None
        self.color3 = None

        print(self.song_id)

        self.is_special(song_id)

    def is_special(self, song_id):
        if song_id == "1sK28tbNrhhKWRKl920sDa":  # "Check This Out" by Oh The Larceny, broken bc these
            # methods were updated since the code was written
            print("special song detected")
            check_it_out_time = 33
            self.mapped_song = True
            self.section_color = next_color(1, self.section_color)
            self.constellation.add_effect(
                ef.FillAllEffect(self.constellation, self.get_beat_time(117), .75, self.section_color, 1))  # Let
            self.section_color = next_color(1, self.section_color, 25, 35)
            self.constellation.add_effect(
                ef.FillAllEffect(self.constellation, self.get_beat_time(119), .5, self.section_color, 1))  # Me
            self.section_color = next_color(1, self.section_color, 25, 35)

            self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.get_beat_time(122), 0.35, (255, 255, 255), 1, 1, 0.1, 0.2))
            self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.get_beat_time(122), 0.35, (255, 255, 255), 2, 1, 0.1, 0.2))
            self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.get_beat_time(122), 0.35, (255, 255, 255), 0, 1, 0.1, 0.2))

            self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.get_beat_time(122)+0.25, 0.35, (255, 255, 255), 12, 1, 0.1, 0.2))
            self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.get_beat_time(122)+0.25, 0.35, (255, 255, 255), 10, 1, 0.1, 0.2))
            self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.get_beat_time(122)+0.25, 0.35, (255, 255, 255), 9, 1, 0.1, 0.2))

            self.constellation.add_effect(ef.BeachBall(self.constellation, self.get_beat_time(122)+0.75, 1.0, None, 0, 0.1, 0.3, 1))



            self.section_color = next_color(1, self.section_color)

            # self.constellation.add_effect(
            #     ef.FillAllEffect(self.constellation, check_it_out_time, .75, self.section_color, 1))  # Check it out
            #
            self.constellation.add_effect(
                ef.AnimatedRingEffect(self.constellation, check_it_out_time, 0.75,
                                      200, 400, self.section_color, 1200, 1200 * -1.618, 0,
                                      0, 1, False))  # Check it out

            self.section_color = next_color(1, self.section_color)

            stagger = 0.09

            # self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, 35, 1, self.section_color, 7, 1, 0.25, 0.25))
            self.constellation.add_effect(
                ef.LightItUp(self.constellation, 34.0, 1.2, (255, 255, 255), 0, stagger, 0.05, 0.2, 1))
            self.constellation.add_effect(
                ef.LightItUp(self.constellation, 35.65, 1.2, (255, 255, 255), 1, stagger, 0.05, 0.2, 1))

            self.constellation.add_effect(
                ef.AnimatedRingEffect(self.constellation, 37, 3.2, 200, 400, self.section_color, 1200, 1200 * -1.618, 0,
                                      0, 2, False))
            self.section_color = next_color(1, self.section_color)
            self.constellation.add_effect(
                ef.LightItUp(self.constellation, 38.2, 1.2, (255, 255, 255), 0, stagger, 0.05, 0.2, 1))
            self.constellation.add_effect(
                ef.LightItUp(self.constellation, 39.35, 1.2, (255, 255, 255), 1, stagger, 0.05, 0.2, 1))

            self.constellation.add_effect(
                ef.AnimatedRingEffect(self.constellation, 41.0, 3.2, 200, 400, self.section_color, 1200, 1200 * -1.618,
                                      0, 0, 2, False))

            self.constellation.add_effect(
                ef.LightItUp(self.constellation, 41.55, 1.2, (255, 255, 255), 0, stagger, 0.05, 0.2, 1))
            self.constellation.add_effect(
                ef.LightItUp(self.constellation, 43.5, 1.2, (255, 255, 255), 1, stagger, 0.05, 0.2, 1))

            self.constellation.add_effect(ef.BeachBall(self.constellation, 45, 3, None, 0, 0.1, 0.2, 1))

    def get_beat_time(self, beat_num):
        return self.beats[beat_num]["start"]

    def get_beat_duration(self, beat_num):  # beat_num may be 0-based or 1-based. Need to check and make sure code is consistent
        # ("Beat num: " + str(beat_num))
        return self.beats[beat_num]["duration"]

    def get_segment_duration(self, segment_index):  # segment_index is 0-based
        return self.segments[segment_index]["duration"]

    def add_effects_while_running(self):

        self.update_time()

        # if section changed, do something
        if self.update_sections() and not self.mapped_song:
            self.section_color = next_color(1, self.section_color)
            self.color2 = next_color(1, self.section_color)
            self.color3 = next_color(1, self.color2)

            # get time until next section
            time_until_next_section = self.sections[self.current_section]["start"] + \
                                      self.sections[self.current_section]["duration"] - self.current_song_time

            # self.constellation.add_effect(
            #     ef.FillAllEffect(self.constellation, self.current_song_time, time_until_next_section,
            #                      self.section_color, 0))
            self.constellation.add_effect(ef.HexagonProgressEffect(self.constellation, self.current_song_time, time_until_next_section, self.section_color, (111, 111, 111), 7, 2, 0))
            self.constellation.add_effect(ef.AnimatedRingEffect(self.constellation, self.current_song_time, 1, 200, 400, self.section_color, 1200, 1200 * -1.618, 0, 0, 1, False))

        # if beat changed, do something
        if self.update_beats():
            if self.time_signature == 4:
                # print("Beat index: " + str(self.current_beat_index), "Length of beats: " + str(len(self.beats)))
                if self.current_beat_index + 2 < len(self.beats):
                    if self.current_beat_index % 2 == 0:  # do something on a 1,3 or 2,4 beat when time signature is 4/4
                        # self.constellation.add_effect(ef.HexagonProgressEffect(self.constellation, self.current_song_time, self.get_beat_duration(self.current_beat_index) + self.get_beat_duration(self.current_beat_index + 2), (100, 100, 100), self.color3, 2, 2, 0.5))
                        # self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.current_song_time, self.get_beat_duration(self.current_beat_index), self.color3, 1, 1, 0.2, 0.4))
                        # self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.current_song_time, self.get_beat_duration(self.current_beat_index), self.color3, 0, 1, 0.2, 0.4))
                        pass
                    else:
                        # self.constellation.add_effect(ef.HexagonProgressEffect(self.constellation, self.current_song_time, self.get_beat_duration(self.current_beat_index) + self.get_beat_duration(self.current_beat_index + 2), (100, 100, 100), self.color2,  10, 2, 0.5))
                        # self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.current_song_time,
                        #                                                    self.get_beat_duration(
                        #                                                        self.current_beat_index), self.color2, 12,
                        #                                                    1, 0.2, 0.4))
                        # self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.current_song_time,
                        #                                                    self.get_beat_duration(
                        #                                                        self.current_beat_index), self.color2, 9,
                        #                                                    1, 0.2, 0.4))
                        pass

            else:
                print("Time signature not supported")
                print(self.time_signature)

        # if segment changed, do something
        if self.update_segments():
            # print("Segment changed")
            # print(self.current_segment)
            # get timbre data

            x1 = abs((self.current_segment["timbre"][0] - self.lower_bound) / self.range)
            if x1 > 1:
                x1 = 1
            if x1 < 0:
                x1 = 0

            print("x1 = " + str(x1))

            # print("x1 = " + str(self.current_segment["timbre"][0]) + "x2 = " + str(
            #     self.current_segment["timbre"][1]) + "x3 = " + str(self.current_segment["timbre"][2]) + "x4 = " + str(
            #     self.current_segment["timbre"][3]) + "x5 = " + str(self.current_segment["timbre"][4]) + "x6 = " + str(
            #     self.current_segment["timbre"][5]))

            self.constellation.add_effect(ef.VolumeBarEffect(self.constellation, 0, self.current_song_time,
                                                             self.get_segment_duration(self.current_segment_index) / 1.5, x1,
                                                             self.section_color, 4))

    def update_sections(self):
        for section in self.sections:
            if section["start"] <= self.current_song_time < section["start"] + section["duration"]:  # section has changed

                self.current_section = self.sections.index(section)

                if self.current_section != self.last_section:
                    self.last_section = self.current_section
                    return True
                break

    def update_beats(self):
        for beat in self.beats:
            if beat["start"] <= self.current_song_time < beat["start"] + beat["duration"]:  # beat has changed

                self.current_beat_index = self.beats.index(beat)

                if self.current_beat_index != self.last_beat:

                    self.last_beat = self.current_beat_index
                    return True  # beat has changed
                return False  # beat has not changed

    def update_segments(self):
        for segment in self.segments:
            if segment["start"] <= self.current_song_time < segment["start"] + segment["duration"]:

                self.current_segment_index = self.segments.index(segment)
                self.current_segment = segment

                if self.current_segment != self.last_segment:
                    self.last_segment = self.current_segment
                    return True
                return False

    def update_time(self):
        # this can be optimized
        current_time = int(round(time.time() * 1000))
        self.current_song_time = (current_time - self.local_timestamp) / 1000 + self.current_song_timeAPI

    def get_current_section(sections, last_section, current_song_time):
        section_changed = False
        for section in sections:
            if section["start"] <= current_song_time < section["start"] + section["duration"]:
                current_section = sections.index(section)
                if current_section != last_section:
                    section_changed = True
                break
        else:
            # If we didn't find a section, return the last section
            current_section = last_section
        return current_section, section_changed


# class SongLookup:
#     __instance = None
#
#     @staticmethod
#     def get_instance():
#         if SongLookup.__instance is None:
#             SongLookup()
#         return SongLookup.__instance
#
#     def __init__(self):
#         if SongLookup.__instance is not None:
#             raise Exception("This class is a singleton!")
#         else:
#             SongLookup.__instance = self
#             self.song_list = []
#
#         # self.song_list.append(Song("63mL1DdcSFfxVJ9XGnSRQz", 176.97333, [0.0, 7.9221, 21.40309, 34.00896, 48.79903, 64.01683, 70.5222, 91.83413, 116.60762, 132.47868, 145.744, 163.1296]))
#
#         self.song_list.append(Song("Run Wild", "2QQ5BiHTf2UnZ6LHYKLcx5",
#                                    159.4737, [0.0, 8.31746, 20.16123, 43.84421, 73.05014, 95.93646, 108.5845, 120.42278,
#                                               133.84496]))
#
#     def get_song_by_id(self, id):
#         for song in self.song_list:
#             if song.get_song_id() == id:
#                 return song
#
#         return None
