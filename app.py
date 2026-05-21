from flask import Flask, render_template, request, send_file
import pandas as pd
import time
import re
import os

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

# ============================================================
# YOUTUBE API
# ============================================================

API_KEY = "AIzaSyAx5hlZXqed1Vc3PvfbQC6PfSEgHJNSci0"

youtube = build('youtube', 'v3', developerKey=API_KEY)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def retry_api_call(func, retries=5, delay=5):
    for attempt in range(retries):
        try:
            return func()
        except HttpError:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise


def detect_url_type(url):

    if re.search(r'/@([^/?]+)', url):
        return 'handle'

    elif re.search(r'/channel/([^/?]+)', url):
        return 'channel_id'

    return 'unknown'


def get_channel_id_from_url(url):

    url_type = detect_url_type(url)

    if url_type == 'handle':

        handle = re.search(r'/@([^/?]+)', url).group(1)

        request = youtube.search().list(
            part="snippet",
            q=handle,
            type="channel",
            maxResults=1
        )

        response = retry_api_call(lambda: request.execute())

        if response['items']:
            return response['items'][0]['snippet']['channelId']

    elif url_type == 'channel_id':

        return re.search(r'/channel/([^/?]+)', url).group(1)

    return None


def get_channel_details(channel_id):

    request = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id
    )

    response = retry_api_call(lambda: request.execute())

    if not response['items']:
        return None

    item = response['items'][0]

    return {
        "channel_name": item['snippet']['title'],
        "uploads_playlist": item['contentDetails']['relatedPlaylists']['uploads']
    }


def get_all_video_ids_from_playlist(playlist_id):

    video_ids = []

    next_page_token = None

    while True:

        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )

        response = retry_api_call(lambda: request.execute())

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    return video_ids


def get_video_details(video_ids):

    all_videos = []

    for i in range(0, len(video_ids), 50):

        chunk = video_ids[i:i+50]

        request = youtube.videos().list(
            part="snippet,statistics,contentDetails,status",
            id=",".join(chunk)
        )

        response = retry_api_call(lambda: request.execute())

        for item in response['items']:

            snippet = item.get('snippet', {})
            statistics = item.get('statistics', {})
            status = item.get('status', {})

            raw_date = snippet.get('publishedAt', '')

            published_formatted = datetime.strptime(
                raw_date,
                "%Y-%m-%dT%H:%M:%SZ"
            ).strftime("%d %b %Y") if raw_date else "N/A"

            video_data = {

                "Title": snippet.get('title', ''),
                "Published Date": published_formatted,
                "Views": int(statistics.get('viewCount', 0)),
                "Likes": int(statistics.get('likeCount', 0)),
                "Comments": int(statistics.get('commentCount', 0)),
                "Privacy Status": status.get('privacyStatus', ''),
                "URL": f"https://www.youtube.com/watch?v={item['id']}"

            }

            all_videos.append(video_data)

    return all_videos


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def home():

    return render_template('index.html')


@app.route('/extract', methods=['POST'])
def extract():

    youtube_url = request.form.get('youtube_url')

    if not youtube_url:
        return "No YouTube URL provided"

    # ============================================================
    # CHANNEL EXTRACTION
    # ============================================================

    channel_id = get_channel_id_from_url(youtube_url)

    if not channel_id:
        return "Invalid YouTube Channel URL"

    channel_details = get_channel_details(channel_id)

    video_ids = get_all_video_ids_from_playlist(
        channel_details['uploads_playlist']
    )

    video_data = get_video_details(video_ids)

    # ============================================================
    # DATAFRAME
    # ============================================================

    df = pd.DataFrame(video_data)

    # ============================================================
    # CSV EXPORT
    # ============================================================

    output_folder = "exports"

    os.makedirs(output_folder, exist_ok=True)

    safe_name = re.sub(
        r'[\\/*?:"<>|]',
        "",
        channel_details['channel_name']
    )

    csv_path = os.path.join(
        output_folder,
        f"{safe_name}.csv"
    )

    df.to_csv(csv_path, index=False)

    # ============================================================
    # DOWNLOAD CSV
    # ============================================================

    return send_file(
        csv_path,
        as_attachment=True
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
