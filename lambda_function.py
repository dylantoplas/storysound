import pymysql
import json
from textblob import TextBlob

# Database connection
def connect_to_db():
    return pymysql.connect(
        host="*******",  
        user="*******",      
        password="*******",  
        database="*******",
        connect_timeout=5,
    )

# Lambda handler
def lambda_handler(event, context):
    # Extract description from the event
    description = event.get("description", "")
    if not description:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Description is required"})
        }

    # Perform sentiment analysis
    sentiment = TextBlob(description).sentiment.polarity

    # Connect to the database
    connection = connect_to_db()
    cursor = connection.cursor()

    try:
        # Query songs database to find closest matches based on valence
        query = """
        SELECT 
            track_name,
            artists,
            valence,
            ABS(valence - %s) AS distance
        FROM instrumental_songs
        ORDER BY distance ASC
        LIMIT 30
        """
        cursor.execute(query, (sentiment,))
        results = cursor.fetchall()

        # Format the results as a list of dictionaries
        playlist = [
            {"Track Name": r[0], "Artists": r[1], "Valence": r[2], "Distance": r[3]}
            for r in results
        ]

        return {
            "statusCode": 200,
            "body": json.dumps(playlist)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

    finally:
        cursor.close()
        connection.close()
