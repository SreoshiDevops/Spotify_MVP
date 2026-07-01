# AI-Native Music Recommendation MVP

This project is a Streamlit app where Gemini acts as the reasoning agent and Spotify is used as the tool to fetch actual music recommendations based on a mood, activity, or taste.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Required environment variables

Set these before running or in Streamlit Cloud secrets:

```bash
export GOOGLE_API_KEY="your-google-api-key"
export SPOTIFY_CLIENT_ID="your-spotify-client-id"
export SPOTIFY_CLIENT_SECRET="your-spotify-client-secret"
```

For Streamlit Cloud, add these as secrets with the same names.

## What the app does

1. Gemini extracts a structured intent from the user's request.
2. The app uses Spotify search as the tool to retrieve real songs.
3. The UI shows the inferred mood, genre, and song recommendations.
