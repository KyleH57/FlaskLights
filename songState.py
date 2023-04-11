# write docs

def get_current_beat(beats, last_beat, current_song_time):
    beat_changed = False
    for beat in beats:
        if beat["start"] <= current_song_time < beat["start"] + beat["duration"]:
            current_beat = beats.index(beat)
            if current_beat != last_beat:
                beat_changed = True
            break
    else:
        # If we didn't find a beat, return the last beat
        current_beat = last_beat
    return current_beat, beat_changed


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


def get_current_segment(segments, last_segment, current_song_time):
    segment_changed = False
    for segment in segments:
        if segment["start"] <= current_song_time < segment["start"] + segment["duration"]:
            current_segment = segments.index(segment)
            if current_segment != last_segment:
                segment_changed = True

                # # update variables for changed segment
                # current_segment_duration = segment["duration"]
                # current_segment_start = segment["start"]
                # current_segment_index = current_segment
                # current_segment_SOM_coords = SOM_stuff_idk[current_segment_index]
                # segment_confidence = segment["confidence"]
            break
    else:
        # If we didn't find a segment, return the last segment
        current_segment = last_segment
    return (current_segment, segment_changed)


def get_current_tatum(tatums, last_tatum, current_song_time):
    tatum_changed = False
    for tatum in tatums:
        if tatum["start"] <= current_song_time < tatum["start"] + tatum["duration"]:
            current_tatum = tatums.index(tatum)
            if current_tatum != last_tatum:
                tatum_changed = True

                # update variables for changed tatum
                current_tatum_duration = tatum["duration"]
                current_tatum_start = tatum["start"]
                current_tatum_index = current_tatum
            break
    else:
        # If we didn't find a tatum, return the last tatum
        current_tatum = last_tatum
    return (current_tatum, tatum_changed)
