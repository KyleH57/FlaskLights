import os
from base64 import b64encode

import requests
from flask import Flask, request, redirect, session

import json
import multiprocessing as mp
import time
import datetime

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

    # request to get currently playing song
    resp = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if resp.status_code == 200:
        siteTextData = resp.json()["item"]["name"] + " by " + resp.json()["item"]["artists"][0][
            "name"] + " is currently playing."

        # send to worker
        parent_conn.send(resp.json())

        # print(resp.json()["item"]["name"])
        # print(resp.json()["item"]["id"])
    else:
        return "Request failed: " + resp.text, resp.status_code

    # request to get audio analysis of song
    resp = requests.get("https://api.spotify.com/v1/audio-analysis/" + resp.json()["item"]["id"], headers=headers)
    if resp.status_code == 200:
        # parent_conn.send(resp.json()["sections"])
        parent_conn.send(resp.json())
        # print the start times and durations of each section
        for section in resp.json()["sections"]:
            # print("section" + str(resp.json()["sections"].index(section)))
            # print(section["start"])
            # print(section["duration"])
            # print(section["confidence"])
            pass

    else:
        return "Request failed: " + resp.text, resp.status_code

    return siteTextData


def worker(conn, frequency=10.0):
    data = None
    current_section = None
    current_song_time = 0

    # array of sections
    sections = []

    while True:
        loopTimeTest = time.time()


        if conn.poll():


            data = conn.recv()

            # see if data is audio analysis or currently playing song

            if "item" in data:
                # print the song name
                print(data["item"]["name"])

                # print the artist name
                print("by")
                print(data["item"]["artists"][0]["name"])

                # # this is the time since the song started playing
                # # print(data['timestamp'])
                #
                # presentDate = datetime.datetime.now()
                # unix_timestamp = int(datetime.datetime.timestamp(presentDate) * 1000)
                # print(unix_timestamp)
                #
                # # Calculate the elapsed time since the API call in milliseconds
                # elapsed_time = int(time.time() * 1000) - data['timestamp']
                #
                # # print elapsed time
                # print(f'The time since the song started playing {elapsed_time} milliseconds')
                #
                # Current time in the song in milliseconds
                current_song_time = data['progress_ms'] / 1000


            if "sections" in data:
                print("audio analysis")

                # add the sections to the array
                sections = data["sections"]
                print(sections)

                #given the start time and duration of each section, print the start of each section
                for section in sections:
                    print(section["start"])

            # # print the list of sections
            # for section in data["sections"]:
            #     print("section" + str(data["sections"].index(section)))
            #     print(section["start"])
            #     print(section["duration"])
            #     print(section["confidence"])

        # #
        # # print the currently playing section
        # for section in sections:
        #     if section["start"] <= current_song_time < section["start"] + section["duration"]:
        #         print("section" + str(sections.index(section)))
        #         #print(section["start"])
        #         #print(section["duration"])
        #         #print(section["confidence"])



        # print the section if it has changed
        for section in sections:
            if section["start"] <= current_song_time < section["start"] + section["duration"]:
                if current_section != sections.index(section):
                    print("section" + str(sections.index(section)))
                    current_section = sections.index(section)

        current_song_time = current_song_time + 1 / frequency

        # print the current time in the song# print
        # print the list of sections

        wait_for_next_iteration(frequency)
        # endTime = time.time()
        #
        # elapsed_time2 = endTime - loopTimeTest
        #
        # print(f"Elapsed time: {elapsed_time2:.5f} seconds")




def wait_for_next_iteration(frequency):
    iteration_time = 1.0 / frequency
    start_time = time.perf_counter()
    elapsed_time = time.perf_counter() - start_time
    time_remaining = iteration_time - elapsed_time
    time.sleep(time_remaining)


if __name__ == "__main__":
    print(SPOTIFY_REDIRECT_URI)

    parent_conn, child_conn = mp.Pipe()
    process = mp.Process(target=worker, args=(child_conn,))
    process.start()

    print("Proc started")

    # this is blocking
    app.run()
