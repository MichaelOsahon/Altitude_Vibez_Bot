from openai import AzureOpenAI
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import requests
import json
from datetime import datetime

# Azure OpenAI client initialization
client = AzureOpenAI(
    api_key=os.getenv("AZURE_KEY"),
    api_version="2024-03-01-preview",
    azure_endpoint=os.getenv("AZURE_ENDPOINT")
)

# Spotify setup
scope = "playlist-modify-public playlist-modify-private"
credentials = "spotify_keys.json"

# Load Spotify credentials from the credentials file
with open(credentials, "r") as keys:
    api_tokens = json.load(keys)

client_id = api_tokens["client_id"]
client_secret = api_tokens["client_secret"]
redirectURI = api_tokens["redirect_uri"]
username = api_tokens["username"]
weather_api_key = api_tokens["weather_api_key"]

# Define the scope of the access needed
scope = "playlist-modify-public playlist-modify-private"

# SpotifyOAuth initialization
sp_oauth = SpotifyOAuth(client_id=client_id,
                         client_secret=client_secret,
                         redirect_uri=redirectURI,
                         scope=scope)

# Get the token (this will handle authorization via the web browser)
token_info = sp_oauth.get_access_token()

# Now you have the token and can authenticate with the Spotify client
token = token_info['access_token']
sp = spotipy.Spotify(auth=token)

# Function to generate image using DALL-E
def generate_image(prompt):
    dalle_result = client.images.generate(
        model="dalle3",
        prompt=prompt,
        n=1
    )
    json_response = json.loads(dalle_result.model_dump_json())
    image_url = json_response["data"][0]['url']
    return image_url

# Weather-based playlist mapping
weather_music = {
    'thunderstorm': ['rock', 'metal'],
    'rain': ['jazz', 'lofi'],
    'snow': ['classical', 'ambient'],
    'clear': ['pop', 'dance'],
    'clouds': ['indie', 'alternative'],
    'mist': ['ambient', 'downtempo'],
    'drizzle': ['jazz', 'lofi'],
    'fog': ['ambient', 'classical']
}

def get_playlist(city): 
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()

    weather_condition = weather_data['weather'][0]['main'].lower()
    temperature = weather_data['main']['temp']

    genres = weather_music.get(weather_condition, ['pop'])  # Default to pop if condition not found
    
    tracks = []
    for genre in genres:
        results = sp.search(
            q='genre:' + genre,
            type='track'
        )
        tracks.extend([track['uri'] for track in results['tracks']['items']])

    tracks = list(set(tracks))[:20]
    playlist_info = f"Weather-based playlist for {city}. Weather: {weather_condition}. Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}" 
    my_playlist = sp.user_playlist_create(user=username, name=city, public=True, description=playlist_info)
    sp.user_playlist_add_tracks(username, my_playlist['id'], tracks)

    return my_playlist['id']
