from flask import Flask, request, jsonify, render_template
from openai import AzureOpenAI
import os
import requests
import json
from altitude_vibez_bot import get_playlist, generate_image
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Azure OpenAI client initialization
client = AzureOpenAI(
    api_key=os.getenv("AZURE_KEY"),
    api_version="2024-03-01-preview",
    azure_endpoint=os.getenv("AZURE_ENDPOINT")
)

# Function to get the number of flights above a country from OpenSky Network
def flights(country_name):
    url = "https://opensky-network.org/api/states/all"
    try:
        response = requests.get(url)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        data = response.json()

        if not data or "states" not in data:
            print("No flight data returned.")
            return "Error: No flight data returned from OpenSky Network."

        states = data.get('states', [])
        country_list = [state[2] for state in states if len(state) > 0]  # Check if state data exists
        country_count = country_list.count(country_name)
        return f"There are currently {country_count} planes in the sky above {country_name}"

    except requests.exceptions.RequestException as e:
        # Log detailed error for debugging purposes
        print(f"Error fetching flight data from OpenSky API: {e}")
        return "Error: Unable to fetch flight data from OpenSky Network. Please try again later."

    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error: {e}")
        return "Error: An unexpected error occurred while fetching flight data."

# Define the available functions for Azure OpenAI
functions = [
    {
        "type": "function",
        "function": {
            "name": "get_flights",
            "description": "Finds the number of planes above a country",
            "parameters": {
                "type": "object",
                "properties": {
                    "country_name": {
                        "type": "string",
                        "description": "The name of the country"
                    }
                },
                "required": ["country_name"]
            }
        }
    }
]

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to get flight count based on country
@app.route('/get_flight_count', methods=['POST'])
def get_flight_count():
    request_data = request.get_json()
    country_name = request_data.get('country_name', None)

    if not country_name:
        return jsonify({"error": "country_name is required"}), 400

    # Get flight data
    flight_count = flights(country_name)
    return jsonify({"message": flight_count})

# Route to handle image generation from user input
@app.route('/index_post1', methods=['POST'])
def index_post1():
    user_keyword = request.form['req_keyword']
    image_url = generate_image(user_keyword)  
    return render_template('index.html', image_url=image_url)

# Route to handle playlist generation based on city weather
@app.route('/index_post', methods=['POST'])
def index_post():
    user_city = request.form['req_city']
    playlist_id = get_playlist(user_city)
    
    # Construct Spotify embed URL using playlist ID
    playlist_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    
    return render_template('index.html', playlist=playlist_url, city=user_city)

if __name__ == '__main__':
    app.run(debug=True)
