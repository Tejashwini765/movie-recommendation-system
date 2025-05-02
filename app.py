import pickle
import streamlit as st
import os
import requests
from itertools import chain
import numpy as np

# Set Streamlit page config
st.set_page_config(
    page_title="Movie Recommender 🎬",
    page_icon="🎥",
    layout="wide",
)

# Load the data
script_directory = os.path.dirname(os.path.abspath(__file__))
movie_path = os.path.join(script_directory, 'movie_data.pkl')

with open(movie_path, 'rb') as f:
    Movies = pickle.load(f)

# Rename columns to match dropdown options
Movies.rename(columns={
    'title': 'Title',
    'genres': 'Genre',
    'casts': 'Cast',
    'directors': 'Director'
}, inplace=True)

# Load the similarity matrix (assuming it's stored as a pickle file)
with open('cosine_similarity.pkl', 'rb') as f:
    similarity_matrix = pickle.load(f)

# Function to fetch TMDB posters
def fetch_poster(title):
    try:
        url = f"https://api.themoviedb.org/3/search/movie?api_key=8265bd1679663a7ea12ac168da84d2e8&query={title}"
        response = requests.get(url)
        data = response.json()
        if data['results']:
            poster_path = data['results'][0].get('poster_path')
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500/{poster_path}"
    except:
        pass
    return "https://via.placeholder.com/500x750.png?text=No+Image"

# Flatten list-type columns for Genre, Cast, Director filters
def flatten_unique(col):
    # Flatten genres, cast, and director columns that may have multiple values
    if isinstance(Movies[col].iloc[0], str):  # Check if it's a string
        return sorted(set(chain.from_iterable(Movies[col].apply(lambda x: x.split(',') if isinstance(x, str) else [x]))))
    return sorted(set(chain.from_iterable(Movies[col])))

# Function to get similar movies based on the similarity matrix
def get_similar_movies(selected_movie, similarity_matrix, movies_df, top_n=10):
    # Get the index of the selected movie
    movie_idx = movies_df[movies_df['Title'] == selected_movie].index[0]
    
    # Get the similarity scores for the selected movie
    similarity_scores = similarity_matrix[movie_idx]
    
    # Get indices of the most similar movies
    similar_movie_indices = np.argsort(similarity_scores)[-top_n-1:-1][::-1]  # Exclude the movie itself
    
    # Get the titles of the most similar movies
    similar_movie_titles = movies_df.iloc[similar_movie_indices]['Title'].values
    return similar_movie_titles

# Background styling with dark overlay
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(
            rgba(0, 0, 0, 0.5), 
            rgba(0, 0, 0, 0.5)
        ), url("https://i.ytimg.com/vi/S5c1ZhRdf1w/maxresdefault.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: white;
    }

    h1, .stSelectbox label, .stButton, .stMarkdown {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# UI
st.title("🎬 Movie Recommender System")

# Filter options for dropdown
filter_options = ['Title', 'Genre', 'Cast', 'Director']
selected_filter = st.selectbox("Choose a filter", filter_options)

# Options for second dropdown
if selected_filter == 'Genre':
    options = flatten_unique('Genre')  # Apply the flatten function to genre
elif selected_filter == 'Cast':
    options = flatten_unique('Cast')  # Apply the flatten function to cast
elif selected_filter == 'Director':
    options = flatten_unique('Director')  # Apply the flatten function to director
else:  # 'Title' filter
    options = sorted(Movies['Title'].dropna().unique())

selected_value = st.selectbox(f"Select a {selected_filter}", options)

# Recommendation logic
if st.button("Show Recommendations"):
    if selected_filter == 'Genre':
        filtered_movies = Movies[Movies['Genre'].apply(lambda x: selected_value in x)]
    elif selected_filter == 'Cast':
        filtered_movies = Movies[Movies['Cast'].apply(lambda x: selected_value in x)]
    elif selected_filter == 'Director':
        filtered_movies = Movies[Movies['Director'] == selected_value]
    else:  # 'Title' filter
        filtered_movies = Movies[Movies['Title'] == selected_value]

    if filtered_movies.empty:
        st.warning("No matching movies found.")
    else:
        st.subheader("Matching Movies 🍿")
        cols = st.columns(5)
        for i, (_, row) in enumerate(filtered_movies.head(20).iterrows()):
            with cols[i % 5]:
                st.image(fetch_poster(row['Title']), use_container_width=True)
                st.markdown(f"**{row['Title']}**")

# When a movie is selected by title, show similar movies
if selected_filter == 'Title' and st.button("Show Similar Movies"):
    similar_movies = get_similar_movies(selected_value, similarity_matrix, Movies)
    
    st.subheader("Similar Movies 🍿")
    cols = st.columns(5)
    for i, movie_title in enumerate(similar_movies):
        movie_row = Movies[Movies['Title'] == movie_title].iloc[0]
        with cols[i % 5]:
            st.image(fetch_poster(movie_row['Title']), use_container_width=True)
            st.markdown(f"**{movie_row['Title']}**")
