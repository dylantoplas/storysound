import streamlit as st
import requests
import logging
logger = logging.getLogger()
import pymysql
import pandas as pd
import boto3
import json


BUCKET_NAME = "*******"
FOLDER_NAME = "*******"

s3_client = boto3.client("s3")

# Function to generate a pre-signed URL
def generate_presigned_url(book_id, expiration=3600):
    try:
        object_key = f"{FOLDER_NAME}/{book_id}.jpg"  # S3 object path
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": object_key},
            ExpiresIn=expiration,
        )
        return url
    except Exception as e:
        st.error(f"Error generating pre-signed URL for {book_id}: {e}")
        return None
    


st.title("Hello, welcome to StorySound! \n")

st.image("logo.jpg")

url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC10162369/"

st.write("This is a Streamlit app that gives you personalized playlist recommendations based on a selected book.\
          \n \n Select a book from the dropdown menu or paste a description to begin: \
         \n\n According to [this](%s) research, listening to musics with less words helps improve focus while reading, therefore most \
         most of the songs here are instrumental." % url)


csv_file = "books_with_presigned_urls.csv"  # Replace with your file path
books_metadata = pd.read_csv(csv_file)

st.write("Here are some songs for your reading:")
def get_books(query):
    try:
        connection = pymysql.connect(
            host = "*******",
            user = "*******n",
            password = "*******",
            database = "*******",
        )
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return []
    finally:
        if connection:
            connection.close()

# Fetch top 5 books
query = """
SELECT title, author, average_rating
FROM books
ORDER BY average_rating DESC
LIMIT 5
"""
books = get_books(query)

# Display top books
if books:
    st.write("🔥 Top Rated Books on Goodreads 🔥")
    for book in books:
        st.write(f"**{book[0]}** by {book[1]} (Rating: {book[2]})")

st.write("### Option 1: Select a Book")
# Allow the user to search for a book


# query_all_books = """
# SELECT title FROM books ORDER BY title ASC
# """
# all_books = get_books(query_all_books)
# books_dict = {book[0]: book[1] for book in all_books}  # Map book_id to titles
# books_list = list(books_dict.values())  # Dropdown displays book titles
# # books_list = [book[0] for book in all_books]  # Extract only titles

# # Add a selectbox for book selection
# search_query = st.selectbox("Search for a book:", books_list, index=0 if books_list else None)

# # Fetch and display details for the selected book
# if search_query:
#     selected_book_id = next(book_id for book_id, title in books_dict.items() if title == search_query)
#     query = f"""
#     SELECT book_id, title, author, average_rating
#     FROM books
#     WHERE title = "{search_query}"
#     """
#     search_results = get_books(query)

#     if search_results:
#         st.write("Book Details:")
#         for book in search_results:
#             st.write(f"**Title:** {book[1]}")
#             st.write(f"**Author:** {book[2]}")
#             st.write(f"**Average Rating:** {book[3]}")
#         book_image_url = generate_presigned_url(selected_book_id)
#         if book_image_url:
#             st.image(book_image_url, caption=f"Image for {book[1]}", width=300)
#         else:
#             st.write("No image available for the selected book.")
#     else:
#         st.write("No details found for the selected book.")

query_all_books = """
SELECT book_id, title FROM books ORDER BY title ASC
"""
all_books = get_books(query_all_books)

# Ensure `all_books` is not empty and has valid tuples
if all_books and all(isinstance(book, tuple) and len(book) >= 2 for book in all_books):
    # Map book_id to titles
    books_dict = {book[0]: book[1] for book in all_books}
    books_list = list(books_dict.values())  # Dropdown displays book titles
else:
    st.error("No books found in the database or unexpected data format.")
    books_dict = {}
    books_list = []

# Add a selectbox for book selection
if books_list:
    search_query = st.selectbox("Search for a book:", books_list, index=0)
else:
    search_query = None

# Fetch and display details for the selected book
if search_query:
    # Find the corresponding book_id for the selected title
    selected_book_id = next(
        (book_id for book_id, title in books_dict.items() if title == search_query), None
    )

    if selected_book_id:
        # Query the database for the selected book
        query = f"""
        SELECT book_id, title, author, average_rating
        FROM books
        WHERE book_id = "{selected_book_id}"
        """
        search_results = get_books(query)

        if search_results:
            st.write("Book Details:")
            for book in search_results:
                st.write(f"**Title:** {book[1]}")
                st.write(f"**Author:** {book[2]}")
                st.write(f"**Average Rating:** {book[3]}")

            # Generate the pre-signed URL for the book's image
            book_image_url = generate_presigned_url(selected_book_id)

            # Display the book's image if the URL is valid
            if book_image_url:
                st.image(book_image_url, caption=f"Image for {book[1]}", width=300)
            else:
                st.write("No image available for the selected book.")
        else:
            st.write("No details found for the selected book.")
    else:
        st.error("Could not find a matching book_id for the selected title.")

def get_playlist(book_title):
    try:
        connection = pymysql.connect(
            host="*******",
            user="*******",
            password="*******",
            database="*******",
        )
        with connection.cursor() as cursor:
            query = """
            SELECT 
            track_name,
            artists,
            valence
            FROM playlists
            WHERE book_title = %s
            LIMIT 30
            """
            cursor.execute(query, (book_title,))
            result = cursor.fetchall()
            return result
    except Exception as e:
        st.error(f"Error fetching playlist: {e}")
        return []
    finally:
        if connection:
            connection.close()


# Display playlist for the selected book
if search_query:
    playlist = get_playlist(search_query)
    if playlist:
        st.write(f"🎵 Playlist for **{search_query}**:")
        
        # Convert the playlist into a pandas DataFrame
        playlist_df = pd.DataFrame(playlist, columns=["Track Name", "Artists", "Valence"])
        
        # Show the DataFrame as a table
        st.table(playlist_df)
    else:
        st.write("No playlist available for this book.")


st.markdown(
    """
    <style>
    .stTextArea textarea {
        font-size: 16px;  /* Adjust font size */
        height: 150px;    /* Adjust height of the text area */
        padding: 10px;    /* Add padding for better appearance */
    }
    </style>
    """,
    unsafe_allow_html=True
)


def get_playlist_from_description(description):
    # Initialize AWS Lambda client
    lambda_client = boto3.client("lambda", region_name="us-east-1")  

    # Invoke Lambda function
    response = lambda_client.invoke(
        FunctionName="storysound-stack-playlistSentiment-8RehAW4DaTXT",  
        InvocationType="RequestResponse",
        Payload=json.dumps({"description": description}),
    )

    # Parse the response
    response_payload = json.loads(response["Payload"].read())
    if response["StatusCode"] == 200:
        return json.loads(response_payload["body"])
    else:
        st.error("Failed to fetch playlist. Please try again later.")
        return []

    

# Add description-based input
st.write("### Option 2: Describe a Book")
description = st.text_area("Can't find your book? Paste a Goodreads description here:")

if st.button("Generate Playlist"):
    if description:
        # Call Lambda function with the description
        playlist = get_playlist_from_description(description)
        
        # Display playlist
        if playlist:
            st.write("### Playlist Generated:")
            playlist_df = pd.DataFrame(playlist)
            st.table(playlist_df)
        else:
            st.write("No songs found. Try refining your description.")
    else:
        st.error("Please enter a description.")


