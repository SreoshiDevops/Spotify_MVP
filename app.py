import os

from dotenv import load_dotenv
import streamlit as st

load_dotenv()

from recommender import create_playlist, recommend_music


st.set_page_config(page_title="AI Music Agent", page_icon="🎧", layout="wide")

st.title("🎧 AI-Native Music Recommendation Agent")
st.write(
    "Describe a mood, activity, or taste. Gemini interprets it as a structured intent and Spotify becomes the recommendation tool."
)

with st.expander("Why this is AI-native", expanded=True):
    st.markdown(
        "- Traditional systems usually rely on past clicks, popularity, or fixed tags. They struggle with nuanced requests like 'cozy rainy-day indie' or 'energetic study beats'.\n"
        "- Gemini unlocks natural-language understanding, mood inference, and context-aware intent extraction.\n"
        "- Spotify provides the live tool layer for real track discovery, so the experience feels conversational instead of rigid."
    )

st.sidebar.header("How it works")
st.sidebar.write(
    "1. Gemini converts your natural-language request into a structured music intent.\n"
    "2. The app uses Spotify search as the tool to find real tracks.\n"
    "3. You get a recommendation list with links you can open instantly."
)
st.sidebar.markdown("---")
st.sidebar.write("Required secrets for deployment:")
st.sidebar.code("GOOGLE_API_KEY\nSPOTIFY_CLIENT_ID\nSPOTIFY_CLIENT_SECRET")

with st.form("music_request"):
    requirement = st.text_area(
        "Describe the vibe you want",
        placeholder="Example: upbeat songs for a morning workout, calm lo-fi for studying, or nostalgic 90s pop",
        height=120,
    )
    count = st.slider("Number of tracks", min_value=3, max_value=12, value=6)
    submitted = st.form_submit_button("Recommend songs")

if submitted:
    if not requirement.strip():
        st.error("Please describe the music you want.")
        st.stop()

    with st.spinner("Gemini is shaping the request into a music intent..."):
        result = recommend_music(requirement, num_recommendations=count)

    if result.get("error"):
        st.error(result["error"])
        st.stop()

    st.success("Music intent extracted and Spotify search completed.")

    with st.expander("Agent interpretation", expanded=True):
        st.json(result.get("intent", {}))
        st.caption(result.get("reasoning", ""))
        st.caption(f"Spotify search query: {result.get('search_query', '')}")

    if result.get("tracks"):
        st.subheader(f"Recommended tracks ({len(result['tracks'])})")
        for index, track in enumerate(result["tracks"], start=1):
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{index}. {track['name']}**")
                    st.write(f"Artist: {track.get('artist', 'Unknown')}")
                    st.write(f"Album: {track.get('album', 'Unknown')}")
                    if track.get("popularity") is not None:
                        st.write(f"Popularity: {track['popularity']}")
                with col2:
                    if track.get("spotify_url"):
                        st.link_button("Open in Spotify", track["spotify_url"])
                    else:
                        st.info("No Spotify link available")
                st.divider()
    else:
        st.info("No tracks were returned. Try a more specific mood or check your Spotify credentials.")

    with st.expander("Quick playlist preview"):
        playlist = create_playlist(requirement, playlist_size=min(6, count))
        if playlist.get("error"):
            st.warning(playlist["error"])
        else:
            st.write(playlist.get("playlist_name", "Playlist"))
            st.write(playlist.get("description", ""))
            for track in playlist.get("tracks", [])[:6]:
                st.write(f"- {track.get('name')} — {track.get('artist', 'Unknown')}")

else:
    st.info("Enter a prompt above to generate a recommendation list.")
