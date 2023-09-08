import json
import os
import sqlite3
from json import JSONDecodeError

from syrics.api import Spotify

import openai

# takes a python dictionary?
def print_lyric_color_info(json_data):
    print("Primary color:", json_data['primaryColorRGB'])
    print("Accent color:", json_data['accentColorRGB'])
    print("Lyric associations:")
    for association in json_data['lyricAssociations']:
        print("    ", association['startTime'], "-", association['duration'], "ms", "-", association['colorRGB'], "-",
              association['reasoning'])



def parse_info(json_data):
    if type(json_data) == str:
        json_data = json.loads(json_data)
    json_data['primaryColorRGB'] = hex_to_rgb(json_data['primaryColorRGB'])
    json_data['accentColorRGB'] = hex_to_rgb(json_data['accentColorRGB'])
    for i in range(len(json_data['lyricAssociations'])):
        json_data['lyricAssociations'][i]['colorRGB'] = hex_to_rgb(json_data['lyricAssociations'][i]['colorRGB'])
    return json_data


def hex_to_rgb(hex_color):
    if hex_color.startswith('0x'):
        hex_color = hex_color[2:]  # Remove '0x' prefix
    elif hex_color.startswith('#'):
        hex_color = hex_color[1:]  # Remove '#' prefix

    if len(hex_color) != 6:
        raise ValueError("Invalid hexadecimal color code. It should be 6 characters long.")

    stuff = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    return stuff


def print_lyrics(unique_id):
    sp = Spotify(os.environ["SPOTIFY_COOKIE"])
    data = sp.get_lyrics(unique_id)
    # Print the lyrics line by line
    if 'lyrics' in data and 'lines' in data['lyrics']:
        for line in data['lyrics']['lines']:
            print(line['words'])


def print_raw_lyrics(unique_id):
    sp = Spotify(os.environ["SPOTIFY_COOKIE"])
    data = sp.get_lyrics(unique_id)
    print(data)


def make_gpt4_api_call(data):
    openai.api_key = os.environ["OPENAI_API_KEY"]

    PROMPT = "Primary Color Association with a Song:\n\nRead through the lyrics of the song provided in the next " \
             "message and select a primary color that you believe encapsulates the overall mood, tone, and theme of " \
             "the song. Black, shades of grey, and silver are not to be used. Also, give an RGB color code for the " \
             "selected color.\n\nAdditionally, identify an accent color that complements your primary color choice" \
             " and further highlights the song's underlying themes or emotions. The accent color should also exclude" \
             " black, shades of grey, and silver. Provide the RGB color code.\n\n\nSpecific Lyric Color " \
             "Associations:\n\nIdentify specific lines in the song that you believe have a distinctive color " \
             "association, particularly in the context of common cultural understandings. For each line, select a" \
             " color that reflects its meaning or imagery, excluding black, shades of grey, and silver. Provide the " \
             "RGB color code for each selected color. The color associations " \
             "should be obvious and easy for someone to" \
             " understand while listening to the song. Try to do 6 per song, but if there are less than 6, that's ok." \
             " It is quality is more important than quantity. Do not do more than 6 per song. The associations should" \
             " be a times that are evenly distributed throughout the song. Do not use a line if the startTime is less" \
             " than 7000.\n\n\n\nOutput in json forat:\n{\n    \"primaryColorRGB\": \"<Primary color RGB code>\",\n" \
             "    \"accentColorRGB\": \"<Accent color RGB code>\",\n    \"lyricAssociations\": [\n        {\n  " \
             "          \"startTime\": \"<Start time of the line>\",\n           " \
             " \"colorRGB\": \"<Associated color RGB code>\",\n     " \
             "       \"reasoning\": \"<Only used in debug mode>\"\n        },\n        {\n        " \
             "    \"startTime\": \"<Start time of the line>\",\n          " \
             "  \"colorRGB\": \"<Associated color RGB code>\",\n         " \
             "   \"reasoning\": \"<Only used in debug mode>\"\n        },\n     " \
             "RR, GG, BB are from 0-FF. Do not provide any other data other than JSON data."

    response = openai.ChatCompletion.create(
        # model="gpt-3.5-turbo-16k",
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": PROMPT,
            },
            {
                "role": "user",
                "content": str(data),
            }
        ],
        temperature=1.0,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    if response['choices'][0]['finish_reason'] == 'length':
        print("API call failed. Response was too long.")
        return None
    elif response['choices'][0]['finish_reason'] == 'stop':
        return response
    else:
        print("API call failed. Reason: " + response['choices'][0]['finish_reason'])
        return None



# ... your existing imports and other code ...

def get_color_data(song_id, replace=False, debug=False):
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS mytable
                 (unique_id text PRIMARY KEY, data text, version text)''')  # Making unique_id the primary key

    version_number = "1.0"

    c.execute('SELECT * FROM mytable WHERE unique_id=?', (song_id,))
    result = c.fetchone()

    if result is not None and replace is False:
        if debug:
            print("Using cached data")

        json_str = result[1]
        info = parse_info(json_str)

        if debug:
            print_lyric_color_info(info)

        return info

    else:
        if debug:
            print("No cached data found. Sending API Requests...")

        sp = Spotify(os.environ["SPOTIFY_COOKIE"])
        lyric_data = sp.get_lyrics(song_id)
        if lyric_data is None:
            print("ERROR: lyric_data is None.")
            return None

        response = make_gpt4_api_call(lyric_data)

        if response is None:
            return None

        json_str = response['choices'][0]['message']['content']

        try:
            json_data = json.loads(json_str)


        except JSONDecodeError as e:
            print("ERROR: JSONDecodeError")
            print(e)
            print("json_str:")
            print(json_str)
            return None

        add_duration_to_lyric_associations(json_data, lyric_data)

        if debug:
            print("GPT API Request complete:")
            print(json_data)

        json_data = parse_info(json_data)

        # Convert the Python dictionary back to a JSON string
        json_str_to_save = json.dumps(json_data)

        if replace:
            c.execute("INSERT OR REPLACE INTO mytable (unique_id, data, version) VALUES (?, ?, ?)",
                      (song_id, json_str_to_save, version_number))
        else:
            c.execute("INSERT INTO mytable (unique_id, data, version) VALUES (?, ?, ?)",
                      (song_id, json_str_to_save, version_number))


        conn.commit()
        # print the database size

        # Count entries
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mytable")
        count = cursor.fetchone()[0]
        print(f"Number of entries: {count}")

        conn.close()


        if debug:
            print("Data saved to database")
            print_lyric_color_info(json_data)





        return json_data



def add_duration_to_lyric_associations(json_data, lyric_data):
    associations = json_data['lyricAssociations']
    # Access the 'lines' list from the 'lyrics' key in the dictionary
    lines = lyric_data.get('lyrics', {}).get('lines', [])

    # Extract the 'startTimeMs' values and convert them to integers
    lyric_times = [int(line['startTimeMs']) for line in lines if 'startTimeMs' in line]

    for association in associations:
        association_start = int(association['startTime'])
        next_lyric_time = next((time for time in lyric_times if time > association_start), None)

        if next_lyric_time is not None:
            association['duration'] = next_lyric_time - association_start
        else:
            association['duration'] = "N/A"  # or some default value