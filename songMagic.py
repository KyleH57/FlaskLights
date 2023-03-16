class Song:
    def __init__(self, song_id, total_duration, section_times):
        self.song_id = song_id
        self.total_duration = total_duration
        self.section_times = section_times
        self.section_durations = []

        # Calculate section durations
        for i in range(len(section_times)):
            if i == 0:
                section_duration = section_times[i]
            else:
                section_duration = section_times[i] - section_times[i-1]
            self.section_durations.append(section_duration)

    def get_song_id(self):
        return self.song_id

    def set_song_id(self, song_id):
        self.song_id = song_id

    def get_total_duration(self):
        return self.total_duration

    def set_total_duration(self, total_duration):
        self.total_duration = total_duration

    def get_section_times(self):
        return self.section_times

    def set_section_times(self, section_times):
        self.section_times = section_times

    def get_section_durations(self):
        return self.section_durations



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

        self.song_list.append(Song("63mL1DdcSFfxVJ9XGnSRQz", 176.97333, [0.0, 7.9221, 21.40309, 34.00896, 48.79903, 64.01683, 70.5222, 91.83413, 116.60762, 132.47868, 145.744, 163.1296]))

    def get_song_by_id(self, id):
        for song in self.song_list:
            if song.get_song_id() == id:
                return song

        return None