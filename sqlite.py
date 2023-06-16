import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('dnu.db')

# Create a cursor object
cur = conn.cursor()

# Create the channels table
cur.execute("""
    CREATE TABLE channels (
      channel_id TEXT PRIMARY KEY,
      channel_name TEXT,
      added_time DATETIME
    )
""")

# Create the videos table
cur.execute("""
    CREATE TABLE videos (
      video_id TEXT PRIMARY KEY,
      channel_id TEXT,
      title TEXT,
      upload_time DATETIME,
      added_time DATETIME
    )
""")

# Commit the transaction
conn.commit()

# Close the connection
conn.close()
