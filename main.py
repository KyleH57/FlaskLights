import colorsys
import os
import socket
from base64 import b64encode
import random

import requests
from flask import Flask, request, redirect, session, render_template

import json
import multiprocessing as mp
import time
import datetime

import math

# check if the OS is windows
import sys

import board
import neopixel


# LED CTRL
# import ledCtrl
# from audioChroma import run_som
from audioChroma import *
from songMagic import SongLookup, Song
from constellation import constellation
from effects import *


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

SPOTIFY_CLIENT_ID = "fdeab218fc904db89d4f1d278f268002"

# read a file and set the client secret
with open("config.cfg", "r") as f:
    SPOTIFY_CLIENT_SECRET = f.read().strip()


print("SECRET: " + SPOTIFY_CLIENT_SECRET)

SPOTIFY_REDIRECT_URI = "http://192.168.0.152:5000/callback"
SPOTIFY_AUTHORIZATION_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


@app.route("/login/spotify")
def login_spotify():
    scope = "user-library-read user-read-email user-read-playback-state user-read-currently-playing"
    authorization_url = f"{SPOTIFY_AUTHORIZATION_URL}?" \
                        f"client_id={SPOTIFY_CLIENT_ID}&" \
                        f"response_type=code&" \
                        f"redirect_uri={SPOTIFY_REDIRECT_URI}&" \
                        f"scope={scope}"
    return redirect(authorization_url)


@app.route("/callback")
def callback_spotify():
    code = request.args.get("code")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64encode(f'{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}'.encode()).decode()}"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI
    }
    resp = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
    if resp.status_code == 200:
        session["spotify_token"] = resp.json()["access_token"]
        return redirect("/")
    else:
        return "Authorization failed: " + resp.text, resp.status_code


@app.route("/")
def index():
    if "spotify_token" not in session:
        return redirect("/login/spotify")
    headers = {
        "Authorization": "Bearer " + session["spotify_token"]
    }
    siteTextData = ""

    local_timestamp = int(round(time.time() * 1000))  # current time in UNIX milliseconds

    currently_playing_data = ""
    # time.sleep(3) # this causes early

    # request to get currently playing song
    resp = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if resp.status_code == 200:
        siteTextData = resp.json()["item"]["name"] + " by " + resp.json()["item"]["artists"][0][
            "name"] + " is currently playing."

        currently_playing_data = resp.json()

        # print(resp.json()["item"]["name"])
        # print(resp.json()["item"]["id"])
    elif resp.status_code == 401 or resp.status_code == 400:
        return redirect("/login/spotify")
    else:
        return "Request failed: " + resp.text, resp.status_code

    # request to get audio analysis of song
    resp = requests.get("https://api.spotify.com/v1/audio-analysis/" + resp.json()["item"]["id"], headers=headers)
    if resp.status_code == 200:
        # parent_conn.send(resp.json()["sections"])
        parent_conn.send([local_timestamp, currently_playing_data, resp.json()])

        # print the start times aCodend durations of each section
        for section in resp.json()["sections"]:
            # print("section" + str(resp.json()["sections"].index(section)))
            # print(section["start"])
            # print(section["duration"])
            # print(section["confidence"])
            pass

    else:
        return "Request failed: " + resp.text, resp.status_code

    song = currently_playing_data["item"]["name"]  # set the song title here
    artist = currently_playing_data["item"]["artists"][0][
        "name"]  # set the artist name here
    refresh_interval = math.ceil(
        (currently_playing_data["item"]["duration_ms"] - currently_playing_data["progress_ms"]) / 1000)
    return render_template('index.html', song=song, artist=artist, refresh_interval=refresh_interval)
    # return siteTextData


def random_color(max_brightness):
    h = random.random()
    r, g, b = colorsys.hsv_to_rgb(h, 1, max_brightness)
    return [int(r * 255), int(g * 255), int(b * 255)]


def next_color(max_brightness, last_color):
    # convert last color to hsv
    last_color = colorsys.rgb_to_hsv(last_color[0] / 255, last_color[1] / 255, last_color[2] / 255)
    h_old = last_color[0]
    h = h_old + random.randrange(13, 43) / 100
    if h > 1:
        h -= 1
    r, g, b = colorsys.hsv_to_rgb(h, 1, max_brightness)
    return [int(r * 255), int(g * 255), int(b * 255)]

def check_match(string):
    table = ["value1", "value2", "value3"]  # example table of values
    if string in table:
        return True
    else:
        return False


def worker(conn, frequency=16.0):
    data = None
    current_section = None
    current_song_time = 0
    testTime1 = 0
    current_song_timeAPI = 0
    api_timestamp = 0
    testVar123 = True
    current_section_duration = 1
    current_section_start = 0
    song_playing = False
    current_beat = None
    beat_even = False

    current_segment = None
    segment_color = [255, 0, 0]
    segment_timbre = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # 12 values
    current_segment_index = 0
    current_segment_SOM_coords = [0, 0]
    SOM_stuff_idk = []

    # tatums
    current_tatum = 0
    current_tatum_index = 0

    bg_color = [255, 0, 0]

    rap_color = [255, 0, 0]

    local_timestamp = 0

    # array of sections
    sections = []

    # array of beats
    beats = []

    # intialize the song "database"
    song_database = SongLookup.get_instance()

    NUM_SEGMENTS = 38

    ARRANGEMENT = "-120, -180, 120, 60, 0r, 120, 60, 0r, 120, 60, 0, -60, -120, -60, -120, -60, " \
                  "0, -60, 0, 60, 120, -180, -120r, 120, -180r, 60, 120, 180r, 60, 0, 060, 0120, " \
                  "-180r, -60, -120r, 0, -60,-120, -180r, -60, 0, 60, 120, -180r, 60, 120,-180, " \
                  "-120r, 120, -180r, 60, 0, -60, -120"

    MAX_BRIGHTNESS = 0.11

    # intialize the constellation
    my_constellation = constellation(ARRANGEMENT, 15, 15, 13, MAX_BRIGHTNESS, debug=True)

    # print all the segments
    # my_constellation.print_XY_coords()

    # effects variables
    last_rainbow_time = time.time()
    wave_progress = 0


    while True:
        # get the time the loop started
        start_time = time.perf_counter()

        # check if there is data in the queue
        if conn.poll():
            # get the data
            data = conn.recv()

        if data is not None:
            song_playing = True

            song_name = data[1]["item"]["name"]

            song_id = data[1]["item"]["id"]

            # print("data: " + str(data))
            local_timestamp = data[0]

            currently_playing_data = data[1]

            # this is the time the song started playing in UNIX milliseconds
            api_timestamp = currently_playing_data["timestamp"]

            current_song_timeAPI = currently_playing_data['progress_ms'] / 1000  # current song time in seconds
            # print("current_song_timeAPI: " + str(current_song_timeAPI))

            analysis_data = data[2]
            # print("audio analysis")

            # add the sections to the array
            sections = analysis_data["sections"]

            # add beat data to the array
            beats = analysis_data["beats"]

            # print the length of the beats array
            # print("beats length: " + str(len(beats)))

            # add segment data to the array
            segments = analysis_data["segments"]

            # add taum data to the array
            tatums = analysis_data["tatums"]


            # create a new array of segments with the timbre data
            X_list = []
            for segment in segments:
                X_list.append(segment["timbre"])

            # SOM stuff
            SOM_stuff_idk = run_som(X_list, song_name, segments, False)

            timbre_colors = []
            for i in range(20):
                timbre_colors.append(random_color(1.0))




            time_offset = -1000
            current_time = int(round(time.time() * 1000))  # current time in UNIX milliseconds

            current_song_time = (current_time - local_timestamp) / 1000 + current_song_timeAPI

            data = None


            # start printing song info
            print("\nSong name: " + song_name)

            print("song id: " + str(song_id))

            #print duration of the song
            print(analysis_data["track"]["duration"])

            sections_only_times = []
            for section in sections:
                sections_only_times.append(section["start"])

            print(sections_only_times)

            # print num of sections
            print("num of sections: " + str(len(sections)))

            # print num of beats
            print("num of beats: " + str(len(beats)))

            # print num of segments
            print("num of segments: " + str(len(segments)))

            # print num of tatums
            print("num of tatums: " + str(len(tatums)))

            # check if the song is special
            special_song_obj = song_database.get_song_by_id(song_id)

        # end of do once

        # get current unix time in milliseconds
        current_time = int(round(time.time() * 1000))
        # print current_time in a human readable format
        # print("current_time: " + str(datetime.datetime.fromtimestamp(current_time / 1000.0)))

        current_song_time = (current_time - local_timestamp) / 1000 + current_song_timeAPI
        # print("current_song_time: " + str(current_song_time))





        if song_playing:
            # Do something if the section changes
            for section in sections:
                if section["start"] <= current_song_time < section["start"] + section["duration"]:
                    if current_section != sections.index(section):
                        # print("section" + str(sections.index(section)))
                        current_section = sections.index(section)
                        current_section_duration = section["duration"]
                        current_section_start = section["start"]



            section_progress = (current_song_time - current_section_start) / current_section_duration

            # there is a bug where at the beginning of the next song, section_progress is above 1, this is becase
            # the variables are not reset when the song changes

            # check if the progress is greater than 1 or less than 0
            if section_progress > 1:
                # print("Section progress: " + str(section_progress) + " current_section_start: " + str(
                #     current_section_start) + " current_song_time: " + str(
                #     current_song_time) + " current_section_duration: " + str(current_section_duration))
                section_progress = 0
            elif section_progress < 0:
                print("Section progress: " + str(section_progress) + " current_section_start: " + str(
                    current_section_start) + " current_song_time: " + str(
                    current_song_time) + " current_section_duration: " + str(current_section_duration))
                section_progress = 0

            # Do something if the beat has changed
            for beat in beats:
                if beat["start"] <= current_song_time < beat["start"] + beat["duration"]:
                    if current_beat != beats.index(beat):
                        # print("beat" + str(beats.index(beat)))
                        current_beat = beats.index(beat)
                        current_beat_duration = beat["duration"]
                        current_beat_start = beat["start"]

                        beat_even = not beat_even

                        my_constellation.clear()
                        my_constellation.set_random_segments_color([255, 255, 255], 0.3)


            # print the segment if it has changed
            for segment in segments:
                if segment["start"] <= current_song_time < segment["start"] + segment["duration"]:
                    if current_segment != segments.index(segment):
                        # segment has changed

                        # update variables
                        current_segment = segments.index(segment)
                        current_segment_duration = segment["duration"]
                        current_segment_start = segment["start"]

                        current_segment_index = segments.index(segment)

                        current_segment_SOM_coords = SOM_stuff_idk[current_segment_index]
                        # print("current_segment_SOM_coords: " + str(current_segment_SOM_coords))

                        rap_color = next_color(1.0, rap_color)


                        # print segment confidence
                        # print("segment confidence: " + str(segment["confidence"]))
                        segment_confidence = segment["confidence"]

                        rap_color = next_color(1.0, rap_color)



            # do something if the tatum has changed
            for tatum in tatums:
                if tatum["start"] <= current_song_time < tatum["start"] + tatum["duration"]:
                    if current_tatum != tatums.index(tatum):
                        # print("tatum" + str(tatums.index(tatum)))
                        current_tatum = tatums.index(tatum)
                        current_tatum_duration = tatum["duration"]
                        current_tatum_start = tatum["start"]

                        current_tatum_index = tatums.index(tatum)






            my_constellation.show()

        else: # display a generic rainbow wave if no song is playing
            # wavelength, speed
            wave_progress = my_constellation.rainbow_wave_x(2400, 1600, frequency, wave_progress)

            # this is very slow, need to use multiple simultaneous threads
            my_constellation.show()
            # end of if song_playing



        wait_for_next_iteration_no_sleep(frequency, start_time)


def progress_bar_2(section_progress, pixels, color, bg_color, n, blur_size=3):
    # Calculate the number of pixels in the section based on the progress and the total number of pixels
    section_size = int(section_progress * n)

    # Set the color of the pixels in the section
    for i in range(section_size):
        if i < section_size - 1:
            pixels[i] = color
        elif i == section_size - 1:
            old_r, old_g, old_b = bg_color
            new_r, new_g, new_b = color
            pixels[i] = [int(old_r * 0.5), int(old_g * 0.5), int(old_b * 0.5)]




def wait_for_next_iteration_no_sleep(frequency, start_time):
    iteration_time = 1.0 / frequency

    fps = 1 / (time.perf_counter() - start_time)

    if fps < frequency:
        print("WARNING LOW FPS - fps: " + str(fps))

    while True:
        if time.perf_counter() - start_time >= iteration_time:
            return


if __name__ == "__main__":
    print(SPOTIFY_REDIRECT_URI)

    parent_conn, child_conn = mp.Pipe()
    process = mp.Process(target=worker, args=(child_conn,))
    process.start()

    app.run(host='192.168.0.152', port=5000)

