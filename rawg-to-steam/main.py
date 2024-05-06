from flask import Flask, jsonify, request
from steam_web_api import Steam

app = Flask(__name__)

# Endpoint to search for Games
@app.route('/api/games', methods=['GET'])
def search_steam_games():
    query = request.args.get('search')
    if not query:
        return jsonify({"error": "Query parameter 'search' is required"}), 400
    key = request.args.get('key')

    steam = Steam(key)

    steam_games = steam.apps.search_games(query)

    app.logger.info(steam_games)
    formatted_games = {
        "count": len(steam_games["apps"]),
        "results": [
            {
                "id": game["id"][0],
                "slug": game["name"].lower().replace(" ", "-"),
                "name": game["name"],
                "background_image": f"https://cdn.akamai.steamstatic.com/steam/apps/{game["id"][0]}/capsule_231x87.jpg",
                "platforms": [{"platform": {"id": 1, "name": "Steam"}}],
                "box_art": f"https://steamcdn-a.akamaihd.net/steam/apps/{game["id"][0]}/library_600x900_2x.jpg"  # Example: Box art field from Steam API
            }
            for game in steam_games["apps"]
        ]
    }

    return jsonify(formatted_games)

# Endpoint to search for Games
@app.route('/api/games/<int:app_id>', methods=['GET'])
def get_steam_game(app_id):
    key = request.args.get('key')
    steam = Steam(key)

    steam_game = steam.apps.get_app_details(app_id)

    app.logger.info(steam_game)

    formatted_game = {
        "id": steam_game[str(app_id)]["data"]["steam_appid"],
        "name": steam_game[str(app_id)]["data"]["name"],
        "slug": steam_game[str(app_id)]["data"]["name"].lower().replace(" ", "-"),
        "background_image": steam_game[str(app_id)]["data"]["header_image"],
        "box_art": f"https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/library_600x900_2x.jpg",
        "description_raw": steam_game[str(app_id)]["data"]["short_description"],
        "metacritic": steam_game[str(app_id)]["data"].get("metacritic", {}).get("score", None),
        "website": steam_game[str(app_id)]["data"].get("website", None)
    }

    return jsonify(formatted_game)




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9999)
