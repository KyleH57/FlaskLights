import colorsys
import os
import socket
from base64 import b64encode
import random

import requests
from flask import Flask, request, redirect, session

import json
import multiprocessing as mp
import time
import datetime

# LED CTRL
import ledCtrl

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

led_obj = ledCtrl.square_LED_panel(8, 10)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

SPOTIFY_CLIENT_ID = "fdeab218fc904db89d4f1d278f268002"

# read a file and set the client secret
with open("config.cfg", "r") as f:
    SPOTIFY_CLIENT_SECRET = f.read()

SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/callback"
SPOTIFY_AUTHORIZATION_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


@app.route("/login/spotify")
def login_spotify():
    scope = "user-library-read user-read-email user-read-playback-state user-read-currently-playing"
    authorization_url = f"{SPOTIFY_AUTHORIZATION_URL}?client_id={SPOTIFY_CLIENT_ID}&response_type=code&redirect_uri={SPOTIFY_REDIRECT_URI}&scope={scope}"
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

        # time.sleep(3) this has no effect on lead or lag
        currently_playing_data = resp.json()

        # print(resp.json()["item"]["name"])
        # print(resp.json()["item"]["id"])
    elif resp.status_code == 401:
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

    return siteTextData


def random_color(max_brightness):
    h = random.random()
    r, g, b = colorsys.hsv_to_rgb(h, 1, max_brightness)
    return [int(r * 255), int(g * 255), int(b * 255)]


def worker(conn, frequency=20.0):
    data = None
    current_section = None
    current_song_time = 0
    testTime1 = 0
    current_song_timeAPI = 0
    api_timestamp = 0
    testVar123 = True

    local_timestamp = 0

    # array of sections
    sections = []

    while True:
        # check if there is data in the queue
        if conn.poll():
            # get the data
            data = conn.recv()

            # if type(data) is int:
            #     # print("local_timestamp: " + str(data))
            #     local_timestamp = data
            # # see if data is audio analysis or currently playing song
            # if "item" in data:
            #     # print the song name and artist
            #     print(str(data["item"]["name"]) + " by " + str(data["item"]["artists"][0]["name"]))
            #
            #     # this is the time the song started playing in UNIX milliseconds
            #     api_timestamp = data["timestamp"]
            #
            #     # print api_timestamp
            #     # this is the time the song started playing in UNIX milliseconds
            #     print("api_timestamp: " + str(api_timestamp))
            #     # print api_timestamp as a human readable time
            #     print("Song started playing at: " + str(datetime.datetime.fromtimestamp(api_timestamp / 1000.0)))
            #
            #     current_song_timeAPI = data['progress_ms'] / 1000  # current song time in seconds
            #     print("current_song_timeAPI: " + str(current_song_timeAPI))
            #     testTime1 = time.time()
            #
            #     #moved to main.py
            #     #local_timestamp = int(round(time.time() * 1000))  # current time in UNIX milliseconds
            #
            # if "sections" in data:
            #     # print("audio analysis")
            #
            #     # add the sections to the array
            #     sections = data["sections"]
            #     # print(sections)
            #
            #     # print the start times of each section and the confidence on the same line
            #     for section in sections:
            #         print("start time: " + str(section["start"]) + " confidence: " + str(section["confidence"]))

        if data is not None:

            # print("data: " + str(data))
            local_timestamp = data[0]

            currently_playing_data = data[1]

            # # print the song name and artist
            # print(str(currently_playing_data["item"]["name"]) + " by " + str(
            #     currently_playing_data["item"]["artists"][0]["name"]))

            # this is the time the song started playing in UNIX milliseconds
            api_timestamp = currently_playing_data["timestamp"]

            # # print api_timestamp
            # # this is the time the song started playing in UNIX milliseconds
            # print("api_timestamp: " + str(api_timestamp))
            # # print api_timestamp as a human readable time
            # print("Song started playing at: " + str(datetime.datetime.fromtimestamp(api_timestamp / 1000.0)))

            current_song_timeAPI = currently_playing_data['progress_ms'] / 1000  # current song time in seconds
            # print("current_song_timeAPI: " + str(current_song_timeAPI))

            analysis_data = data[2]
            # print("audio analysis")

            # add the sections to the array
            sections = analysis_data["sections"]

            # print(sections)
            #
            if testVar123:
                # print the start times of each section and the confidence on the same line
                for section in sections:
                    print("start time: " + str(section["start"]) + " confidence: " + str(section["confidence"]))
                testVar123 = False

            data = None

        # moved to main.py
        # local_timestamp = int(round(time.time() * 1000))  # current time in UNIX milliseconds

        # update the current song time
        # elapsed_time = time.time() - testTime1
        # current_song_time = current_song_timeAPI + elapsed_time

        # get current unix time in milliseconds
        current_time = int(round(time.time() * 1000))
        # print current_time in a human readable format
        # print("current_time: " + str(datetime.datetime.fromtimestamp(current_time / 1000.0)))

        # this calculates the time since the song
        # started playing but does not account for starting midway though a song
        # current_song_time = (current_time - api_timestamp) / 1000

        current_song_time = (current_time - local_timestamp) / 1000 + current_song_timeAPI

        #print("current_song_time: " + str(current_song_time))

        # print the section if it has changed
        for section in sections:
            if section["start"] <= current_song_time < section["start"] + section["duration"]:
                if current_section != sections.index(section):
                    print("section" + str(sections.index(section)))
                    current_section = sections.index(section)

                    # print(current_song_time)

                    # generate random rgb color
                    ledCtrl.setPanelColor(random_color(0.3), led_obj)

                    # send LED data
                    ledCtrl.sendPanelData(led_obj, client_socket)

        #wait_for_next_iteration(frequency)
        wait_for_next_iteration_no_sleep(frequency)
        # time.sleep(0.025)


def wait_for_next_iteration(frequency):
    iteration_time = 1.0 / frequency
    start_time = time.perf_counter()
    elapsed_time = time.perf_counter() - start_time
    time_remaining = iteration_time - elapsed_time
    # print("time_remaining: " + str(time_remaining))
    time.sleep(time_remaining)


def wait_for_next_iteration_no_sleep(frequency):
    iteration_time = 1.0 / frequency
    start_time = time.perf_counter()
    while True:
        if time.perf_counter() - start_time >= iteration_time:
            return


if __name__ == "__main__":
    print(SPOTIFY_REDIRECT_URI)

    parent_conn, child_conn = mp.Pipe()
    process = mp.Process(target=worker, args=(child_conn,))
    process.start()

    print("Proc started")

    # this is blocking
    app.run()
