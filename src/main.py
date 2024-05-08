import os
import re
import logging
import bleach
import requests
import html
import sqlite3
import json
import datetime
from time import time, strftime
from flask import Flask, jsonify, request, redirect
from dateutil import parser
from steam_web_api import Steam
from waitress import serve

default_language = os.environ.get("R2S_LANG", "english")
log_level = os.environ.get("R2S_LOG_LEVEL", logging.INFO)

app = Flask(__name__)
logger = logging.getLogger()
logger.setLevel(log_level)

sanitizer = bleach.sanitizer.Cleaner(tags=[], attributes=[], strip=True, strip_comments=True, filters=[], protocols=[])

conn = sqlite3.connect('./database.sqlite', check_same_thread=False)
cursor = conn.cursor()

def clean_string(string):
    string = html.unescape(string)
    string = sanitizer.clean(string)
    string = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', string)
    string = re.sub(r'\s+', ' ', string)
    string = string.encode('ascii', 'ignore').decode('unicode_escape')
    return string

def increment_stat(stat):
    cursor.execute("INSERT OR IGNORE INTO stats (stat, count) VALUES (?, 0)", (stat,))
    cursor.execute("UPDATE stats SET count = count + 1 WHERE stat = ?", (stat,))
    conn.commit()

def get_steam_app_details(app_id, lang_parameter=default_language):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l={lang_parameter}"
    cached_data = get_cached_data(url)
    if cached_data:
        return cached_data

    response = requests.get(url)
    if response.status_code == 200 and response.content:
        data = response.json()
        app.logger.debug(data)
        cache_data(url, json.dumps(data))
        return data
    else:
        logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
        return None

def cache_data(url, data):
    cursor.execute("REPLACE INTO cache (url, data, timestamp) VALUES (?, ?, ?)", (url, data, time()))
    conn.commit()
    logger.debug(f"Cached data for {url}")

def get_cached_data(url):
    cursor.execute("SELECT data, timestamp FROM cache WHERE url = ?", (url,))
    result = cursor.fetchone()

    if result:
        data, timestamp = result
        if time() - timestamp <= 30 * 24 * 3600:
            logger.debug(f"Retrieved cached data for {url}")
            increment_stat('games_from_cache')
            return json.loads(data)
    return None

def format_game_data(game_data, app_id):
    released = game_data.get("release_date", {}).get("date", None)
    if released:
        # Fallback to none if date is invalid
        try:
            released = parser.parse(released).strftime('%Y-%m-%dT%H:%M:%SZ')
        except parser.ParserError:
            released = None
        
    return {
        "id": game_data["steam_appid"],
        "name": clean_string(game_data["name"]),
        "slug": clean_string(game_data["name"]).lower().replace(" ", "-"),
        "background_image": game_data.get("background_raw") or (game_data.get("screenshots", []) and game_data["screenshots"][0].get("path_full")) or game_data.get("header_image") or None,
        "box_image": f"https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/library_600x900_2x.jpg",
        "description_raw": clean_string(game_data.get("detailed_description", "")),
        "metacritic": game_data.get("metacritic", {}).get("score", None),
        "website": game_data.get("website", None),
        "genres": [{"id": int(genre.get("id", None)), "name": genre.get("description", None)} for genre in game_data.get("genres", [])],
        "tags": [{"id": int(tag.get("id", None)), "name": tag.get("description", None), "language": "eng"} for tag in game_data.get("categories", [])],
        "released": released,
        "developers": [{"id": abs(hash(dev)) % (10 ** 9), "name": dev} for dev in game_data.get("developers", [])],
        "publishers": [{"id": abs(hash(pub)) % (10 ** 9), "name": pub} for pub in game_data.get("publishers", [])],
    }

@app.route("/api/games", methods=["GET"])
def search_steam_games():
    search = request.args.get("search", "")
    steam = Steam("")
    steam_games = steam.apps.search_games(search)
    app.logger.debug(steam_games)
    formatted_games = {
        "count": len(steam_games["apps"]),
        "results": [
            {
                "id": game["id"][0],
                "slug": clean_string(game["name"]).lower().replace(" ", "-"),
                "name": clean_string(game["name"]),
                "background_image": f"https://cdn.akamai.steamstatic.com/steam/apps/{game['id'][0]}/capsule_231x87.jpg",
                "platforms": [{"platform": {"id": 1, "name": "Steam"}}],
                "box_art": f"https://steamcdn-a.akamaihd.net/steam/apps/{game['id'][0]}/library_600x900_2x.jpg"
            }
            for game in steam_games["apps"]
        ]
    }
    increment_stat('searches')
    return jsonify(formatted_games)

@app.route("/api/games/<int:app_id>", methods=["GET"])
def get_steam_game(app_id):
    steam_game = get_steam_app_details( app_id, request.args.get("lang", default_language))
    if not steam_game or str(app_id) not in steam_game or steam_game.get(str(app_id))["success"] == False:
        return jsonify({"error": "Game not found"}), 404
    game_data = steam_game[str(app_id)]["data"]
    increment_stat('games')
    return jsonify(format_game_data(game_data, app_id))

@app.route("/api/stats")
def stats():
    cursor.execute("SELECT * FROM stats")
    stats_data = cursor.fetchall()
    style_string ="<head><link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css'/></head>"
    stats_string = "<br>".join([f"✅ {stat[0]}: {stat[1]}" for stat in stats_data])
    return f"{style_string}<h1>🙏 This rawg-to-steam-redirect instance has proudly served: ✨</h1>{stats_string}"

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def help(path):
    return redirect("https://github.com/Phalcode/rawg-to-steam-redirect", code=302)

@app.after_request
def log_request(response):
    timestamp = strftime("[%Y-%b-%d %H:%M]")
    original_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.environ.get("HTTP_X_REAL_IP", request.remote_addr))
    app.logger.error("%s %s %s %s %s %s", timestamp, original_ip, request.method, request.scheme, request.path, response.status)
    return response

if __name__ == "__main__":
    cursor.execute('''DROP TABLE IF EXISTS games''')
    cursor.execute('''DROP TABLE IF EXISTS games_v2''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cache (url TEXT PRIMARY KEY, data TEXT, timestamp REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS stats (stat TEXT PRIMARY KEY, count INTEGER)''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_url ON cache (url)''')
    serve(app, host="0.0.0.0", port=9999)
