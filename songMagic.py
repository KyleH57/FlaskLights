import time

import effects as ef


class Song:
    def __init__(self, constellation, local_timestamp, current_song_timeAPI, song_title, song_id, total_duration, sections, bars, beats, segments, tatums):
        self.constellation = constellation
        self.local_timestamp = local_timestamp
        self.current_song_timeAPI = current_song_timeAPI
        self.song_title = song_title
        self.song_id = song_id
        self.total_duration = total_duration


        self.sections = sections
        self.bars = []
        self.beats = []
        self.segments = []
        self.tatums = []

        self.is_special = False

        self.current_section = 0
        self.last_section = None

        self.current_song_time = 0  # used when playing song
        self.last_beat = None



    def add_effects_while_running(self):

        self.update_time()



        # if section changed, do something
        if self.update_sections():
            print("section changed")
            self.constellation.add_effect(
                ef.FillAllEffect(self.constellation, self.current_song_time, 0.5, (0, 255, 0)))

    def section_changed(self):
        if self.current_section != self.last_section:
            return True
        return False

    def update_sections(self):
        # ("updating sections")
        for section in self.sections:
            # print(section["start"], self.current_song_time, section["start"] + section["duration"])
            if section["start"] <= self.current_song_time < section["start"] + section["duration"]:

                self.current_section = self.sections.index(section)

                if self.current_section != self.last_section:
                    self.last_section = self.current_section
                    return True
                break

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


class SongLookup:
    __instance = None

    @staticmethod
    def get_instance():
        if SongLookup.__instance is None:
            SongLookup()
        return SongLookup.__instance

    def __init__(self):
        if SongLookup.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            SongLookup.__instance = self
            self.song_list = []

        # self.song_list.append(Song("63mL1DdcSFfxVJ9XGnSRQz", 176.97333, [0.0, 7.9221, 21.40309, 34.00896, 48.79903, 64.01683, 70.5222, 91.83413, 116.60762, 132.47868, 145.744, 163.1296]))

        self.song_list.append(Song("Run Wild", "2QQ5BiHTf2UnZ6LHYKLcx5",
                                   159.4737, [0.0, 8.31746, 20.16123, 43.84421, 73.05014, 95.93646, 108.5845, 120.42278,
                                              133.84496]))

    def get_song_by_id(self, id):
        for song in self.song_list:
            if song.get_song_id() == id:
                return song

        return None
