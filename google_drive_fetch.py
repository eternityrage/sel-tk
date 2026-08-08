"""
Google Drive Integration Module
Fetch videos from a specific Google Drive folder for processing.
Uses Google Drive API v3 with service account or OAuth credentials.

Supports weighted random repost mode: when all videos have been published,
selects a random video for reposting, prioritizing ones posted fewer times.
"""
import os
import json
import sys
import random
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.http import MediaIoBaseDownload

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
LOCAL_INPUT_DIR = os.getenv("LOCAL_INPUT_DIR", "Videos")

PUBLISHED_LOG = "published_videos.json"


def get_published_videos():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return [item.get('video_name', '') for item in data]
            except json.JSONDecodeError:
                return []
    return []


def get_published_history():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    history = get_published_history()
    counts = {}
    for entry in history:
        video_name = entry.get('video_name', '')
        counts[video_name] = counts.get(video_name, 0) + 1
    return counts


def get_drive_service():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

        if not GOOGLE_SERVICE_ACCOUNT_KEY:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY not set")

        if os.path.exists(GOOGLE_SERVICE_ACCOUNT_KEY):
            creds = service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_KEY, scopes=SCOPES)
            service = build('drive', 'v3', credentials=creds)
            print("Google Drive initialized with Service Account file")
            return service
        elif GOOGLE_SERVICE_ACCOUNT_KEY.strip().startswith('{'):
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            temp_file.write(GOOGLE_SERVICE_ACCOUNT_KEY)
            temp_file.close()

            creds = service_account.Credentials.from_service_account_file(
                temp_file.name, scopes=SCOPES)
            service = build('drive', 'v3', credentials=creds)
            print("Google Drive initialized with Service Account JSON")

            os.unlink(temp_file.name)
            return service
        else:
            raise ValueError("Google Service Account key is invalid")

    except ImportError as e:
        print(f"Installing required Google Drive libraries... Error: {e}")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-auth", "google-auth-oauthlib", "google-auth-httplib2", "google-api-python-client"])
        return get_drive_service()
    except Exception as e:
        print(f"Error initializing Google Drive: {e}")
        return None


def list_drive_videos(service):
    if not service:
        return []

    try:
        query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false"
        video_mime_types = [
            "video/mp4",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-matroska"
        ]

        videos = []
        for mime_type in video_mime_types:
            query_with_mime = f"{query} and mimeType contains '{mime_type}'"
            results = service.files().list(
                q=query_with_mime,
                fields="files(id, name, size, mimeType)",
                spaces='drive'
            ).execute()

            videos.extend(results.get('files', []))

        videos.sort(key=lambda x: x.get('name', ''))
        return videos
    except Exception as e:
        print(f"Google Drive API error: {e}")
        return []


def download_video(service, file_info, local_path):
    try:
        request = service.files().get_media(fileId=file_info['id'])

        with open(local_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"  Download progress: {int(status.progress() * 100)}%")

        print(f"Downloaded: {file_info['name']}")
        return True
    except Exception as e:
        print(f"Failed to download {file_info['name']}: {e}")
        return False


def fetch_one_video_from_drive(allow_repost=False):
    """
    Fetch ONE video from Google Drive for processing.

    Args:
        allow_repost: If True and no new videos exist, select a random
                      already-published video for reposting (weighted by
                      repost count - less posted = more likely).
                      If False, only fetch new (unpublished) videos.

    Returns:
        Path to downloaded video or None
    """
    Path(LOCAL_INPUT_DIR).mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("FETCHING VIDEO FROM GOOGLE DRIVE - SELTOK LENS")
    print("=" * 60)

    published = get_published_videos()
    print(f"Already published: {len(published)} video(s)")
    if published:
        for vid in published[:3]:
            print(f"  - {vid}")
        if len(published) > 3:
            print(f"  ... and {len(published) - 3} more")

    if not GOOGLE_DRIVE_FOLDER_ID:
        print("Error: GOOGLE_DRIVE_FOLDER_ID not set in .env")
        return None

    service = get_drive_service()
    if not service:
        return None

    videos = list_drive_videos(service)

    if not videos:
        print("No videos found in Google Drive folder.")
        return None

    print(f"\nFound {len(videos)} video(s) in Google Drive.")

    download_attempts = 0
    download_failures = 0
    all_are_published = True

    for video_info in videos:
        video_name = video_info['name']

        if video_name in published:
            print(f"Skipping {video_name} - already published")
            continue

        all_are_published = False

        download_attempts += 1
        local_path = os.path.join(LOCAL_INPUT_DIR, video_name)
        if download_video(service, video_info, local_path):
            print(f"\nSelected: {video_name}")
            return local_path
        else:
            download_failures += 1
            print(f"Download failed, trying next video...")

    if download_attempts > 0 and download_failures == download_attempts:
        print(f"\nFailed to download all {download_attempts} video(s). Check permissions.")
        return None

    if all_are_published:
        if not allow_repost:
            print("\nAll videos have already been published (no repost mode).")
            return None

        print("\nREPOST MODE: No new videos. Selecting random published video (weighted by repost count)...")

        repost_counts = get_repost_counts()

        video_choices = []
        weights = []
        for video_info in videos:
            vname = video_info['name']
            count = repost_counts.get(vname, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            video_choices.append(video_info)
            weights.append(weight)

        selected_video = random.choices(video_choices, weights=weights, k=1)[0]
        video_name = selected_video['name']
        post_count = repost_counts.get(video_name, 0)
        print(f"  Selected (posted {post_count} time(s) before): {video_name}")

        local_path = os.path.join(LOCAL_INPUT_DIR, video_name)
        if download_video(service, selected_video, local_path):
            print(f"\nSelected for repost: {video_name}")
            return local_path
        else:
            print(f"\nFailed to download repost video.")
            return None

    return None


if __name__ == "__main__":
    fetch_one_video_from_drive()
