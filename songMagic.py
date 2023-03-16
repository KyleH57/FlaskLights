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
