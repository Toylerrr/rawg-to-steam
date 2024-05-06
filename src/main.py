import os
import re
import logging
import bleach
import requests
from time import strftime
from flask import Flask, jsonify, request, redirect
from steam_web_api import Steam

app = Flask(__name__)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Initialize sanitizer
sanitizer = bleach.sanitizer.Cleaner(tags=[], attributes=[], strip=True, strip_comments=True, filters=[], protocols=[])
language = os.environ.get("LANG", "english")

# Function to clean strings
def clean_string(string):
    string = sanitizer.clean(string)
    string = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', string)
    string = re.sub(r'\s+', ' ', string)
    return string

# Function to get Steam app details
def get_steam_app_details(app_id, lang=language):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l={lang}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        app.logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
        return None

# Endpoint to search for Games
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
                "slug": game["name"].lower().replace(" ", "-"),
                "name": game["name"],
                "background_image": f"https://cdn.akamai.steamstatic.com/steam/apps/{game['id'][0]}/capsule_231x87.jpg",
                "platforms": [{"platform": {"id": 1, "name": "Steam"}}],
                "box_art": f"https://steamcdn-a.akamaihd.net/steam/apps/{game['id'][0]}/library_600x900_2x.jpg"
            }
            for game in steam_games["apps"]
        ]
    }
    return jsonify(formatted_games)

# Endpoint to get details of a specific game
@app.route("/api/games/<int:app_id>", methods=["GET"])
def get_steam_game(app_id):
    steam_game = get_steam_app_details(app_id, request.args.get("lang", language))
    app.logger.debug(steam_game)
    if not steam_game or str(app_id) not in steam_game:
        return jsonify({"error": "Game not found"}), 404
    game_data = steam_game[str(app_id)]["data"]
    formatted_game = {
        "id": game_data["steam_appid"],
        "name": game_data["name"],
        "slug": game_data["name"].lower().replace(" ", "-"),
        "background_image": game_data.get("background", game_data.get("background_raw", game_data.get("screenshots", [])[0].get("path_full", game_data.get("header_image", "")))),
        "box_art": f"https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/library_600x900_2x.jpg",
        "description_raw": clean_string(game_data.get("detailed_description", "")),
        "metacritic": game_data.get("metacritic", {}).get("score", None),
        "website": game_data.get("website", None),
        "genres": game_data.get("genres", []),
        "tags": game_data.get("categories", []),
        "released": game_data.get("release_date", {}).get("date", None) + "Z",
        "developers": [{"id": abs(hash(dev)) % (10 ** 9), "name": dev} for dev in game_data.get("developers", [])],
        "publishers": [{"id": abs(hash(pub)) % (10 ** 9), "name": pub} for pub in game_data.get("publishers", [])],
    }
    return jsonify(formatted_game)

# Redirect to GitHub repository for help
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def help(path):
    return redirect("https://github.com/Phalcode/rawg-to-steam-redirect", code=302)

# Log request details after each request
@app.after_request
def log_request(response):
    timestamp = strftime("[%Y-%b-%d %H:%M]")
    original_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.environ.get("HTTP_X_REAL_IP", request.remote_addr))
    app.logger.error("%s %s %s %s %s %s", timestamp, original_ip, request.method, request.scheme, request.path, response.status)
    return response

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=9999)