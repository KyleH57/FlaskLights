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

# frontend
import plotly.graph_objs as go



# LED CTRL
# import ledCtrl
# from audioChroma import run_som
from audioChroma import *
# from songMagic import SongLookup, Song
from Constellation2 import Constellation
from effects import *
from songState import *

import songMagic as sm

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

SPOTIFY_CLIENT_ID = "fdeab218fc904db89d4f1d278f268002"

# read a file and set the client secret
with open("config.cfg", "r") as f:
    SPOTIFY_CLIENT_SECRET = f.read().strip()



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


last_currently_playing_data_progress_ms = -1

@app.route("/")
def index():
    global last_currently_playing_data_progress_ms

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
        if currently_playing_data["progress_ms"] == last_currently_playing_data_progress_ms:
            print("Paused")
            parent_conn.send([0, 0, 0])
            return render_template('index.html', song="Paused", artist="Paused", refresh_interval=9999)
        else:
            last_currently_playing_data_progress_ms = currently_playing_data["progress_ms"]


    elif resp.status_code == 401 or resp.status_code == 400:
        return redirect("/login/spotify")
    else:
        return "Request failed: " + resp.text, resp.status_code

    # request to get audio analysis of song
    resp = requests.get("https://api.spotify.com/v1/audio-analysis/" + resp.json()["item"]["id"], headers=headers)
    if resp.status_code == 200:
        # send timestamp, currently playing data, and audio analysis data to the child process
        parent_conn.send([local_timestamp, currently_playing_data, resp.json()])

    else:
        return "Request failed: " + resp.text, resp.status_code

    # Get loudness of sections
    sections = []
    beats_confidence_per_section = []
    for section in resp.json()["sections"]:
        sections.append([section["start"], section["duration"], section["loudness"]])  # start of section
        beats_in_section = [beat for beat in resp.json()["beats"] if
                            section["start"] <= beat["start"] < (section["start"] + section["duration"])]
        avg_confidence = sum(beat["confidence"] for beat in beats_in_section) / len(
            beats_in_section) if beats_in_section else 0
        beats_confidence_per_section.append([section["start"], avg_confidence])
        beats_confidence_per_section.append([section["start"] + section["duration"], avg_confidence])  # end of section

    loudness_data = {
        'x': [section[0] for section in sections],  # start time of each section
        'y': [section[2] for section in sections]  # loudness of each section
    }

    loudness_chart = go.Scatter(
        x=loudness_data['x'],
        y=loudness_data['y'],
        mode='lines+markers',  # add markers
        line=dict(shape='hv'),  # horizontal - vertical lines
        name='Loudness',
        yaxis='y1'
    )

    # Get beats data
    beats_data = {
        'x': [beat[0] for beat in beats_confidence_per_section],  # start time of each beat
        'y': [beat[1] for beat in beats_confidence_per_section]  # average confidence of each beat per section
    }

    beats_chart = go.Scatter(
        x=beats_data['x'],
        y=beats_data['y'],
        mode='lines+markers',  # add markers
        line=dict(shape='hv'),  # horizontal - vertical lines
        name='Beats',
        yaxis='y2'
    )

    layout = go.Layout(
        title='Loudness vs Time & Average Beats Confidence per Section',
        xaxis=dict(title='Time (s)'),
        yaxis=dict(title='Loudness (dBFS)', range=[-12, 0]),  # Set range for loudness
        yaxis2=dict(title='Average Confidence', overlaying='y', side='right', range=[0, 1])  # Set range for confidence
    )

    fig = go.Figure(data=[loudness_chart, beats_chart], layout=layout)
    loudness_chart_html = fig.to_html(full_html=False)

    # Get section confidences
    section_confidences = []
    for section in resp.json()["sections"]:
        section_confidences.append([section["start"], section["confidence"]])  # start of section
        section_confidences.append([section["start"] + section["duration"], section["confidence"]])  # end of section

    section_confidences_data = {
        'x': [section[0] for section in section_confidences],  # start time of each section
        'y': [section[1] for section in section_confidences]  # confidence of each section
    }

    section_confidences_chart = go.Scatter(
        x=section_confidences_data['x'],
        y=section_confidences_data['y'],
        mode='lines+markers',  # add markers
        line=dict(shape='hv'),  # horizontal - vertical lines
        name='Section Confidence'
        # yaxis = dict(title='Confidence', range=[1, 0]),  # Set range for loudness

    )

    layout = go.Layout(
        title='Section Confidence vs Time',
        xaxis=dict(title='Time (s)'),
        yaxis=dict(title='Section Confidence', range=[0, 1])
    )

    fig = go.Figure(data=[section_confidences_chart], layout=layout)
    section_confidences_chart_html = fig.to_html(full_html=False)

    song = currently_playing_data["item"]["name"]  # set the song title here

    artist = currently_playing_data["item"]["artists"][0][
        "name"]  # set the artist name here

    web_song_id = currently_playing_data["item"]["id"]

    web_song_bpm = resp.json()["track"]["tempo"]

    #histogram stuff
    timbre_data = [segment["timbre"][0] for segment in resp.json()["segments"]]



    # Create the histogram
    timbre_histogram = go.Histogram(
        x=timbre_data,
        name='Timbre[0] Distribution'
    )

    layout = go.Layout(
        title='Timbre[0] Distribution',
        xaxis=dict(title='Timbre[0] Value'),
        yaxis=dict(title='Count')
    )

    fig = go.Figure(data=[timbre_histogram], layout=layout)
    timbre_histogram_html = fig.to_html(full_html=False)



    refresh_interval = math.ceil(
        (currently_playing_data["item"]["duration_ms"] - currently_playing_data["progress_ms"]) / 1000)
    return render_template('index.html', song=song, artist=artist, song_id=web_song_id, song_bpm=web_song_bpm,
                           refresh_interval=refresh_interval,
                           loudness_chart_html=loudness_chart_html,
                           section_confidences_chart_html=section_confidences_chart_html,
                           timbre_histogram_html=timbre_histogram_html)


def random_color(max_brightness):
    h = random.random()
    r, g, b = colorsys.hsv_to_rgb(h, 1, max_brightness)
    return [int(r * 255), int(g * 255), int(b * 255)]






def check_match(string):
    table = ["value1", "value2", "value3"]  # example table of values
    if string in table:
        return True
    else:
        return False


def worker(conn, frequency=20.0):
    song_duration = 0
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


    current_segment = None
    segment_color = [255, 0, 0]
    segment_timbre = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # 12 values
    current_segment_index = 0
    current_segment_SOM_coords = [0, 0]
    SOM_stuff_idk = []

    # tatums
    current_tatum = 0
    current_tatum_index = 0


    segment_color = [255, 0, 0]

    rap_color = [255, 0, 0]

    local_timestamp = 0

    idle_rainbow_playing = False

    selection_var = 0 # delete this later



    # array of sections
    sections = []
    section_color = [255, 0, 0]

    # array of beats
    beats = []
    current_beat = None
    beat_even = False

    # intialize the song "database"
    # song_database = SongLookup.get_instance()

    # NUM_SEGMENTS = 38

    ARRANGEMENT = "-120, -180, 120, 60, 0r, 120," \
                  "60, 0r, 120, 60, 0, -60," \
                  "-120, -60, -120, -60, 0, -60," \
                  "0, 60, 120, -180, -120r, 120," \
                  "-180r, 60, 120, 180r, 60, 0," \
                  "-60, -120, -180r, -60, -120r, 0," \
                  "-60,-120, -180r, -60, 0, 60," \
                  "120, -180r, 60, 120,-180, -120r," \
                  "120, -180r, 60, 0, -60, -120"

    MAX_BRIGHTNESS = 0.5

    NUM_LEDS_SEGMENT = 15
    SEGMENT_LED_SPACING = 15
    SEGMENT_EDGE_SPACING = 13
    my_constellation = Constellation(ARRANGEMENT, NUM_LEDS_SEGMENT, SEGMENT_LED_SPACING, SEGMENT_EDGE_SPACING, MAX_BRIGHTNESS)
    # my_constellation.plot_constellation()
    # my_constellation.plot_constellation_centroid()



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
            if data[0] == 0 and data[1] == 0 and data[2] == 0:
                song_playing = False
            else:
                song_playing = True

                song_name = data[1]["item"]["name"]

                song_id = data[1]["item"]["id"]

                song_duration = data[1]["item"]["duration_ms"] / 1000  # song duration in seconds

                local_timestamp = data[0]

                currently_playing_data = data[1]

                # this is the time the song started playing in UNIX milliseconds
                api_timestamp = currently_playing_data["timestamp"]

                current_song_timeAPI = currently_playing_data['progress_ms'] / 1000  # current song time in seconds
                # print("current_song_timeAPI: " + str(current_song_timeAPI))

                analysis_data = data[2]

                # add the sections to the array
                sections = analysis_data["sections"]

                # add the bars to the array
                bars = analysis_data["bars"]

                # add beat data to the array
                beats = analysis_data["beats"]



                # add segment data to the array
                segments = analysis_data["segments"]

                # add taum data to the array
                tatums = analysis_data["tatums"]


                # # create a new array of segments with the timbre data
                # X_list = []
                # for segment in segments:
                #     X_list.append(segment["timbre"])
                #
                # # SOM stuff
                # SOM_stuff_idk = run_som(X_list, song_name, segments, False)
                #
                # timbre_colors = []
                # for i in range(20):
                #     timbre_colors.append(random_color(1.0))


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


                # print num of sections
                # print("num of sections: " + str(len(sections)))

                # print num of beats
                print("num of beats: " + str(len(beats)))

                # print num of segments
                print("num of segments: " + str(len(segments)))

                # print num of tatums
                print("num of tatums: " + str(len(tatums)))

                # print song time signature
                print("time signature: " + str(analysis_data["track"]["time_signature"]) + "/4")

                my_constellation.remove_all_effects()

                song_obj = sm.Song(my_constellation, local_timestamp, current_song_timeAPI, song_name, song_id, song_duration, sections, bars, beats, segments, tatums, analysis_data["track"]["time_signature"])

        # end of do once

        # get current unix time in milliseconds
        current_time = int(round(time.time() * 1000))

        current_song_time = (current_time - local_timestamp) / 1000 + current_song_timeAPI



        if song_playing:

            song_obj.add_effects_while_running()

            my_constellation.run_effects2(song_obj)


        else: # display a generic rainbow wave if no song is playing


            if idle_rainbow_playing == False:
                # remove all effects
                my_constellation.remove_all_effects()

                my_constellation.add_effect(RainbowWaveEffect(my_constellation, time.time(), 72000, 1500, 750, 1.0))
                idle_rainbow_playing = True
            #
            # current_song_data = []
            # current_song_data.append(time.time())
            my_constellation.run_effects(time.time())


            pass




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

    WARN_FPS = 8
    if fps < WARN_FPS:
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

