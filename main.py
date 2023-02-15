import os
from base64 import b64encode

import requests
from flask import Flask, request, redirect, session

import json
import multiprocessing as mp
import time


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

SPOTIFY_CLIENT_ID = "fdeab218fc904db89d4f1d278f268002"
SPOTIFY_CLIENT_SECRET = "d709c26eb6974d8685965a1279d35cff"

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
        siteTextData = resp.json()["item"]["name"] + " by " + resp.json()["item"]["artists"][0]["name"] + " is currently playing."

        print(resp.json()["item"]["name"])
        print(resp.json()["item"]["id"])
    else:
        return "Request failed: " + resp.text, resp.status_code

    # request to get audio analysis of song
    resp = requests.get("https://api.spotify.com/v1/audio-analysis/" + resp.json()["item"]["id"], headers=headers)
    if resp.status_code == 200:
        parent_conn.send(resp.json()["sections"])
        #print the start times and durations of each section
        for section in resp.json()["sections"]:
            #print("section" + str(resp.json()["sections"].index(section)))
            #print(section["start"])
            #print(section["duration"])
            #print(section["confidence"])
            pass

    else:
        return "Request failed: " + resp.text, resp.status_code

    return siteTextData


def worker(conn, frequency=1.0):
    while True:

        wait_for_next_iteration(frequency)



        if conn.poll():
            data = conn.recv()
            # Do some processing on the received data
            #result = data * 2
            #conn.send(result)
            print(data)
        else:
            # No data received, do other processing or sleep for a short period of time
            pass


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
