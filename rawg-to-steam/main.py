from flask import Flask, jsonify, request
from steam_web_api import Steam

app = Flask(__name__)

# Steam API initialization
KEY = "" #NOT NEEDED It just works if you don't have an API key
#https://steamcommunity.com/dev/apikey
steam = Steam(KEY)

# Endpoint to search for Steam games (simulating RAWG API)
@app.route('/api/games', methods=['GET'])
def search_steam_games():
    query = request.args.get('search')
    if not query:
        return jsonify({"error": "Query parameter 'search' is required"}), 400

    # Use Steam API to search for games
    steam_games = steam.apps.search_games(query)

    # Format the output to match RAWG API structure
    formatted_games = {
        "count": len(steam_games["apps"]),
        "next": None,  # Assuming no pagination for simplicity
        "previous": None,  # Assuming no pagination for simplicity
        "results": [
            {
                "id": game["id"][0],
                "slug": game["name"].lower().replace(" ", "-"),
                "name": game["name"],
                "background_image": f"https://cdn.akamai.steamstatic.com/steam/apps/{game["id"][0]}/capsule_231x87.jpg",
                "rating": None,
                "released": None,
                "platforms": [{"platform": {"id": 1, "name": "Steam"}}],
                "genres": [],
                "developers": [],  
                "metacritic": 2, 
                "publishers": [], 
                "box_art": f"https://steamcdn-a.akamaihd.net/steam/apps/{game["id"][0]}/library_600x900_2x.jpg"  # Example: Box art field from Steam API
            }
            for game in steam_games["apps"]
        ]
    }

    return jsonify(formatted_games)

@app.route('/api/games/<int:app_id>', methods=['GET'])
def get_steam_game(app_id):
    # Use Steam API to get game details
    steam_game = steam.apps.get_app_details(app_id)

    # Format the output to match RAWG API structure
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
    app.run(debug=True, host='0.0.0.0', port=80)
