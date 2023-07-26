import colorsys
import random
import time

import effects as ef

import numpy as np
from scipy.spatial.distance import cdist
from collections import defaultdict


def calculate_avg_distance(set1, set2):
    # calculate pairwise distance matrix
    dist_matrix = cdist(set1, set2)
    # return mean of pairwise distances
    return dist_matrix.mean()


# Assuming data is a dictionary where keys are set names and values are np arrays of vectors
# Example: data = {"A": np.array([[1,2,3], [2,3,4], [3,4,5]]), "B": np.array([[2,3,4], [3,4,5], [4,5,6]])}
def find_similar_sets(data, threshold):
    # dictionary to store similarities
    similar_sets = defaultdict(list)

    # iterate over all pairs of sets
    for set_name1, set_vectors1 in data.items():
        for set_name2, set_vectors2 in data.items():
            # skip comparison with self
            if set_name1 == set_name2:
                continue

            # calculate average distance
            avg_distance = calculate_avg_distance(set_vectors1, set_vectors2)

            # if average distance is below threshold, consider sets as similar
            if avg_distance <= threshold:
                similar_sets[set_name1].append(set_name2)

    return similar_sets


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
        self.current_song_time = 0  # used when playing song, updated in update_time()
        self.time_until_song_end = None
        self.song_title = song_title
        self.song_id = song_id
        self.total_duration = total_duration

        self.sections = sections
        self.bars = bars
        self.beats = beats # this is a list of beat objects, each beat object has a start time and duration
        self.segments = segments

        self.corrected_section_times = self.set_corrected_section_times(song_id)

        # create a 3d array of segments by section
        self.segments_by_section = self.assign_segments_to_sections()

        self.tatums = tatums

        self.time_signature = time_signature

        self.mapped_song = False


        self.current_section_index = 0
        self.last_section = None

        self.current_beat = None
        self.current_beat_index = 0
        self.last_beat = None

        self.current_segment = None
        self.current_segment_index = 0
        self.last_segment = None

        threshold = 125  # make smaller if too many things are getting clustered together
        similar_sets = find_similar_sets(self.segments_by_section, threshold)
        # print the set size of each set
        # for set_name, set_vectors in self.segments_by_section.items():
        #     print(f"Set {set_name} has {set_vectors.shape[0]} vectors")
        #
        for set_name, similar_set_names in similar_sets.items():
            print(f"Set {set_name} is similar to sets {similar_set_names}")

        if len(similar_sets) == 0:
            print("no similar sets found")

        # this is for the volume bar
        # Calculate the 2.5th and 97.5th percentiles
        timbre_data = np.array([segment["timbre"][0] for segment in self.segments])
        self.lower_bound = np.percentile(timbre_data, 2.5)
        self.upper_bound = np.percentile(timbre_data, 97.5)  # TODO: need to update for x2-12
        self.range = self.upper_bound - self.lower_bound

        self.section_color = [255, 0, 0]
        self.color2 = None
        self.color3 = None

        self.is_special(song_id)


        self.start_song()
        # init done

    def start_song(self): # this is called only once when the song starts
        self.update_time()
        PERLIN_SIZE = 75  # this is specific to orion
        self.constellation.add_effect(
            ef.PerlinNoiseEffect(self.constellation, self.current_song_time, self.time_until_song_end, 1.0, 1,
                                 PERLIN_SIZE, 0.006, (64, 64), self.beats, 'both', ef.ColorMode.INTERPOLATE_HUES, {'hue1':(0.0/6), 'hue2':(5.999/6)}))

        print("song started")


    def set_corrected_section_times(self, song_id):
        corrected_sections = []

        if song_id == "7FbrGaHYVDmfr7KoLIZnQ7":  # cupid twin ver
            # section_starts = self.round_section_start_times([0, 9.4, 41.9, 89, 109, 119, 140])
            section_starts = self.round_section_start_times(["0", "9.4", "41.9", "1:30", "2:01", "2:20.25"])

        elif song_id == "4nWP1IKQ9jqSyRg1kFel5D":  # Feels
            section_starts = self.round_section_start_times(["0", "0:6.3", "0:23.7", "0:38.5", "0:54.7", "1:09", "1:26", "1:42"])
        else:
            return None
        section_starts.append(self.total_duration)  # Add total duration to the end of starts

        for i in range(len(section_starts) - 1):  # Exclude the last start time (total duration)
            start = section_starts[i]

            # Calculate duration as difference between current start and next start
            duration = section_starts[i + 1] - start

            corrected_sections.append({"start": start, "duration": duration})

        print("Using corrected section times")
        return corrected_sections

    def round_section_start_times(self, section_starts):
        # This takes an array of times in "minutes:seconds" format or "seconds" format and returns an array of the times of the closest beats
        section_starts_seconds = []
        for start in section_starts:
            if ':' in start:  # Time is in "minutes:seconds" format
                mins, secs = start.split(":")
                time_in_seconds = int(mins) * 60 + float(secs)
            else:  # Time is in "seconds" format
                time_in_seconds = float(start)
            section_starts_seconds.append(time_in_seconds)

        return [self.round_section_start_time(start) for start in section_starts_seconds]

    def round_section_start_time(self, section_start):
        # This takes a time and looks for the beat that is closest to it and returns the time of the closest beat
        closest_beat_time = self.beats[0]["start"]
        for beat in self.beats:
            if abs(beat["start"] - section_start) < abs(closest_beat_time - section_start):
                closest_beat_time = beat["start"]

        return closest_beat_time

    def assign_segments_to_sections(self):
        segments_by_section = {}
        if self.corrected_section_times is None:
            for section in self.sections:
                section_start = section["start"]
                section_end = section_start + section["duration"]

                # Filter segments that belong to the current section
                section_segments = [seg for seg in self.segments
                                    if section_start <= seg["start"] < section_end]

                # Represent each segment by a vector (here we consider 'pitches' and 'timbre' features)
                # Modify this according to which segment features you want to consider
                section_vectors = [seg["timbre"] for seg in section_segments]

                segments_by_section[section_start] = np.array(section_vectors)
        else:
            for section in self.corrected_section_times:
                section_start = section["start"]
                section_end = section_start + section["duration"]

                # Filter segments that belong to the current section
                section_segments = [seg for seg in self.segments
                                    if section_start <= seg["start"] < section_end]

                # Represent each segment by a vector (here we consider 'pitches' and 'timbre' features)
                # Modify this according to which segment features you want to consider
                section_vectors = [seg["timbre"] for seg in section_segments]

                segments_by_section[section_start] = np.array(section_vectors)

        return segments_by_section

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

            self.constellation.add_effect(
                ef.FillHexagonEffect(self.constellation, self.get_beat_time(122), 0.35, (255, 255, 255), 1, 1, 0.1,
                                     0.2))
            self.constellation.add_effect(
                ef.FillHexagonEffect(self.constellation, self.get_beat_time(122), 0.35, (255, 255, 255), 2, 1, 0.1,
                                     0.2))
            self.constellation.add_effect(
                ef.FillHexagonEffect(self.constellation, self.get_beat_time(122), 0.35, (255, 255, 255), 0, 1, 0.1,
                                     0.2))

            self.constellation.add_effect(
                ef.FillHexagonEffect(self.constellation, self.get_beat_time(122) + 0.25, 0.35, (255, 255, 255), 12, 1,
                                     0.1, 0.2))
            self.constellation.add_effect(
                ef.FillHexagonEffect(self.constellation, self.get_beat_time(122) + 0.25, 0.35, (255, 255, 255), 10, 1,
                                     0.1, 0.2))
            self.constellation.add_effect(
                ef.FillHexagonEffect(self.constellation, self.get_beat_time(122) + 0.25, 0.35, (255, 255, 255), 9, 1,
                                     0.1, 0.2))

            self.constellation.add_effect(
                ef.BeachBall(self.constellation, self.get_beat_time(122) + 0.75, 1.0, None, 0, 0.1, 0.3, 1))

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

    def get_beat_duration(self,
                          beat_num):  # beat_num may be 0-based or 1-based. Need to check and make sure code is consistent
        # ("Beat num: " + str(beat_num))
        return self.beats[beat_num]["duration"]

    def get_segment_duration(self, segment_index):  # segment_index is 0-based
        return self.segments[segment_index]["duration"]

    def add_effects_while_running(self):  # this is called every frame

        self.update_time()

        # if section changed, do something
        if self.update_sections() and not self.mapped_song:
            self.section_color = next_color(1, self.section_color)
            self.color2 = next_color(1, self.section_color)
            self.color3 = next_color(1, self.color2)

            if self.corrected_section_times is None:
                # get time until next section
                time_until_next_section = self.sections[self.current_section_index]["start"] + \
                                          self.sections[self.current_section_index]["duration"] - self.current_song_time
            else:  # manually mapped song
                time_until_next_section = self.corrected_section_times[self.current_section_index]["start"] + \
                                          self.corrected_section_times[self.current_section_index][
                                              "duration"] - self.current_song_time

            # self.constellation.add_effect(
            #     ef.FillAllEffect(self.constellation, self.current_song_time, time_until_next_section,
            #                      self.section_color, 0))
            # self.constellation.add_effect(
            #     ef.HexagonProgressEffect(self.constellation, self.current_song_time, time_until_next_section,
            #                              self.section_color, (111, 111, 111), 7, 2, 0))
            # self.constellation.add_effect(
            #     ef.AnimatedRingEffect(self.constellation, self.current_song_time, 1, 200, 400, self.section_color, 1200,
            #                           1200 * -1.618, 0, 0, 1, False))



        # # if beat changed, do something
        # if self.update_beats():
        #     if self.time_signature == 4:
        #         # print("Beat index: " + str(self.current_beat_index), "Length of beats: " + str(len(self.beats)))
        #         if self.current_beat_index + 2 < len(self.beats):
        #             if self.current_beat_index % 2 == 0:  # do something on a 1,3 or 2,4 beat when time signature is 4/4
        #                 self.constellation.add_effect(
        #                     ef.HexagonProgressEffect(self.constellation, self.current_song_time, self.get_beat_duration(
        #                         self.current_beat_index) + self.get_beat_duration(self.current_beat_index + 2),
        #                                              (100, 100, 100), self.color3, 2, 2, 0.5))
        #                 # self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.current_song_time, self.get_beat_duration(self.current_beat_index), self.color3, 1, 1, 0.2, 0.4))
        #                 # self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.current_song_time, self.get_beat_duration(self.current_beat_index), self.color3, 0, 1, 0.2, 0.4))
        #                 pass
        #             else:
        #                 self.constellation.add_effect(
        #                     ef.HexagonProgressEffect(self.constellation, self.current_song_time, self.get_beat_duration(
        #                         self.current_beat_index) + self.get_beat_duration(self.current_beat_index + 2),
        #                                              (100, 100, 100), self.color2, 10, 2, 0.5))
        #                 # self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.current_song_time,
        #                 #                                                    self.get_beat_duration(
        #                 #                                                        self.current_beat_index), self.color2, 12,
        #                 #                                                    1, 0.2, 0.4))
        #                 # self.constellation.add_effect(ef.FillHexagonEffect(self.constellation, self.current_song_time,
        #                 #                                                    self.get_beat_duration(
        #                 #                                                        self.current_beat_index), self.color2, 9,
        #                 #                                                    1, 0.2, 0.4))
        #                 pass
        #
        #     else:
        #         print("Time signature not supported")
        #         print(self.time_signature)
        #
        # # if segment changed, do something
        # if self.update_segments():
        #     # print("Segment changed")
        #     # print(self.current_segment)
        #     # get timbre data
        #     pass

    def update_sections(self):
        if self.corrected_section_times is None:
            for section in self.sections:
                if section["start"] <= self.current_song_time < section["start"] + section[
                    "duration"]:  # section has changed

                    self.current_section_index = self.sections.index(section)

                    if self.current_section_index != self.last_section:
                        self.last_section = self.current_section_index
                        return True
                    break
        else:
            for section in self.corrected_section_times:
                if section["start"] <= self.current_song_time < section["start"] + section[
                    "duration"]:  # section has changed

                    self.current_section_index = self.corrected_section_times.index(section)

                    if self.current_section_index != self.last_section:
                        self.last_section = self.current_section_index
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
        self.time_until_song_end = self.total_duration - self.current_song_time

    def get_current_section(sections, last_section, current_song_time):
        print("WARNING THIS CODE IS SUS songMagic.py get_current_section()")
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
