import colorsys
import os
import socket
from base64 import b64encode
import random

import requests
from flask import Flask, request, redirect, session, render_template

import json
import multiprocessing as mp
import threading

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
from audioChroma import *
# from songMagic import SongLookup, Song
from Constellation2 import Constellation
from effects import *
from effects2 import rainbow_wave_2
from effects2 import transition_perlin as tp
from effects2 import loudness_perlin as lp
from songState import *

import songMagic as sm
import show_generator as sg

import lyrics_chroma as lc

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

SPOTIFY_CLIENT_ID = "fdeab218fc904db89d4f1d278f268002"
STATIC_IP = '192.168.0.152'
SERVER_PORT = 5000

with open("config.cfg", "r") as f:
    lines = f.readlines()
    SPOTIFY_CLIENT_SECRET = lines[0].strip()
    os.environ["SPOTIFY_COOKIE"] = lines[1].strip()
    os.environ["OPENAI_API_KEY"] = lines[2].strip()

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
        player_paused = False
        if resp is None:
            player_paused = True

        song_id = resp.json()["item"]["id"]
        siteTextData = resp.json()["item"]["name"] + " by " + resp.json()["item"]["artists"][0][
            "name"] + " is currently playing."

        currently_playing_data = resp.json()
        if currently_playing_data["progress_ms"] == last_currently_playing_data_progress_ms or player_paused:
            print("Paused")
            parent_conn.send([0, 0, 0, 0])
            return render_template('paused.html')
        else:
            last_currently_playing_data_progress_ms = currently_playing_data["progress_ms"]


    elif resp.status_code == 401 or resp.status_code == 400:
        return redirect("/login/spotify")
    else:
        return "Request failed: " + resp.text, resp.status_code

    # request to get audio analysis of song
    resp = requests.get("https://api.spotify.com/v1/audio-analysis/" + song_id, headers=headers)
    if resp.status_code == 200:
        audio_analysis_data = resp.json()


    else:
        return "Request failed: " + resp.text, resp.status_code

    resp = requests.get("https://api.spotify.com/v1/audio-features/" + song_id, headers=headers)
    if resp.status_code == 200:
        audio_features_data = resp.json()

    else:
        return "Request failed: " + resp.text, resp.status_code

    # get next song
    queue_resp = requests.get("https://api.spotify.com/v1/me/player/queue", headers=headers)
    if queue_resp.status_code == 200:
        # Assuming queue_resp.json() contains your JSON response
        response_data = queue_resp.json()

        # Check if there is at least one song in the queue
        if response_data.get('queue') and len(response_data['queue']) > 0:
            next_song = response_data['queue'][0]
            next_song_id = next_song['id']
            next_song_name = next_song['name']

            print(f"Next song ID: {next_song_id}")
            print(f"Next song name: {next_song_name}")

            database_thread = threading.Thread(target=add_next_song_to_db, args=(next_song_id,))
            database_thread.start()

        else:
            print("The queue is empty.")


    # send timestamp, currently playing data, and audio analysis data to the child process
    parent_conn.send([local_timestamp, currently_playing_data, audio_analysis_data, audio_features_data])

    # Get loudness of sections and beat confidence
    sections = []
    beats_confidence_per_section = []

    total_beat_confidence = 0  # total beat confidence for whole song
    total_beats = 0  # total number of beats for whole song

    for section in audio_analysis_data["sections"]:
        sections.append([section["start"], section["duration"], section["loudness"]])  # start of section

        beats_in_section = [beat for beat in audio_analysis_data["beats"] if
                            section["start"] <= beat["start"] < (section["start"] + section["duration"])]

        if beats_in_section:
            avg_confidence = sum(beat["confidence"] for beat in beats_in_section) / len(beats_in_section)
            total_beat_confidence += sum(beat["confidence"] for beat in beats_in_section)
            total_beats += len(beats_in_section)
        else:
            avg_confidence = 0

        beats_confidence_per_section.append([section["start"], avg_confidence])
        beats_confidence_per_section.append([section["start"] + section["duration"], avg_confidence])  # end of section

    # Calculate average beat confidence for the whole song
    average_beat_confidence_whole_song = total_beat_confidence / total_beats if total_beats else 0

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
    for section in audio_analysis_data["sections"]:
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

    web_song_bpm = audio_analysis_data["track"]["tempo"]

    #histogram stuff
    timbre_data = [segment["timbre"][0] for segment in audio_analysis_data["segments"]]

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



    refresh_interval = math.floor(
        (currently_playing_data["item"]["duration_ms"] - currently_playing_data["progress_ms"]) / 1000)
    return render_template('index.html', song=song, artist=artist, song_id=web_song_id, song_bpm=web_song_bpm,
                           song_bc=average_beat_confidence_whole_song,
                           refresh_interval=refresh_interval,
                           loudness_chart_html=loudness_chart_html,
                           section_confidences_chart_html=section_confidences_chart_html,
                           timbre_histogram_html=timbre_histogram_html,audio_features=audio_features_data)


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

    MAX_BRIGHTNESS = 0.4

    NUM_LEDS_SEGMENT = 15
    SEGMENT_LED_SPACING = 15
    SEGMENT_EDGE_SPACING = 13
    my_constellation = Constellation(ARRANGEMENT, NUM_LEDS_SEGMENT, SEGMENT_LED_SPACING, SEGMENT_EDGE_SPACING, MAX_BRIGHTNESS)

    # make it so it checks if a file exists
    # my_constellation.plot_constellation()
    # my_constellation.plot_constellation_centroid()



    # effects variables
    last_idle_effect_time = time.time()
    wave_progress = 0
    last_idle_effect_time = 0


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

                # add features data to the array
                features_data = data[3]

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

                # create a song object
                song_obj = sm.Song(my_constellation, local_timestamp, current_song_timeAPI, song_name, song_id,
                                   song_duration, sections, bars, beats, segments,
                                   tatums, analysis_data["track"]["time_signature"], features_data)

                # generate a show
                sg.generate_show(my_constellation, song_obj)



        # end of do once

        # get current unix time in milliseconds
        current_time = int(round(time.time() * 1000))

        current_song_time = (current_time - local_timestamp) / 1000 + current_song_timeAPI



        if song_playing:
            # remove all effects
            my_constellation.remove_all_effects()

            idle_rainbow_playing = False

            song_obj.add_effects_while_running() # this is needed to update time and other things

            my_constellation.run_effects2(song_obj, debug=False)


        else: # display a generic rainbow wave if no song is playing

            IDLE_EFFECT_TIME = 600 # 10 minutes

            # if it has been more than 5 seconds since the last rainbow wave, add a new one
            if time.time() - last_idle_effect_time > IDLE_EFFECT_TIME:

                last_idle_effect_time = time.time()
                my_constellation.remove_all_effects()

                idle_pattern_number = random.randint(1, 3)

                if idle_pattern_number == 1:
                    # generate a random int between 300 and 3000
                    rainbow_wave_length = random.randint(1000, 9000)
                    rainbow_wave_speed = rainbow_wave_length / random.randint(2, 9)


                    my_constellation.add_effect(
                        rainbow_wave_2.RainbowWaveEffect2(my_constellation, time.time(), IDLE_EFFECT_TIME, rainbow_wave_length, rainbow_wave_speed, 1.0))
                elif idle_pattern_number == 2:
                    # generate a list of random numbers between 0 and 1 that is 3 long
                    random_hue_list = [random.random(), random.random(), random.random()]
                    my_constellation.add_effect(tp.TransitionPerlinNoiseEffect(my_constellation, time.time(), IDLE_EFFECT_TIME, 1.0, 1, 65, 0.00375*3, (64, 64),[0.9, 0.5, .1], [time.time()+150, time.time()+300,time.time()+ 450]))
                elif idle_pattern_number == 3:
                    my_constellation.add_effect(lp.LoudnessPerlin(my_constellation, time.time(), IDLE_EFFECT_TIME, 1.0, 1, 65, 0.00375*3, (64, 64), None, 'both', ColorMode.INTERPOLATE_HUES, {'hue1': 0, 'hue2': 1}))



            my_constellation.run_effects(time.time())


        wait_for_next_iteration_no_sleep(frequency, start_time)


def wait_for_next_iteration_no_sleep(frequency, start_time):
    iteration_time = 1.0 / frequency

    fps = 1 / (time.perf_counter() - start_time)

    WARN_FPS = 8
    if fps < WARN_FPS:
        print("WARNING LOW FPS - fps: " + str(fps))

    while True:
        if time.perf_counter() - start_time >= iteration_time:
            return


def add_next_song_to_db(song_id):
    print("Adding next song to db")
    info = lc.get_color_data2(song_id, fetch_only=False, debug=False)
    if info.status == "error":
        print("database in use")
    elif info.status == "success":
        print("added to database")
    else:
        print(info.status)

if __name__ == "__main__":
    print(SPOTIFY_REDIRECT_URI)

    parent_conn, child_conn = mp.Pipe()
    process = mp.Process(target=worker, args=(child_conn,))
    process.start()



    app.run(host=STATIC_IP, port=SERVER_PORT)

