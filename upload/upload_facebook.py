"""
Facebook Reels Upload - SelTok Lens
Facebook Graph API for uploading Reels to Facebook Page.
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

def upload_to_facebook(video_path, description, title="SelTok Lens"):
    print("\n" + "=" * 60)
    print("FACEBOOK UPLOAD STARTING - SELTOK LENS")
    print("=" * 60)

    access_token = os.getenv('FACEBOOK_ACCESS_TOKEN') or os.getenv('FB_ACCESS_TOKEN')
    page_id = os.getenv('FACEBOOK_PAGE_ID') or os.getenv('FB_PAGE_ID')

    def mask(s): return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else ("PLACEHOLDER (***)" if s == "***" else "MISSING")
    print(f"[facebook] Page ID: {page_id}")
    print(f"[facebook] Access Token: {mask(access_token)}")

    if not access_token:
        print("[facebook] Skipping Facebook upload - FACEBOOK_ACCESS_TOKEN not set")
        return {'status': 'skipped', 'reason': 'Missing credentials', 'platform': 'facebook'}

    if not page_id:
        print("[facebook] Skipping Facebook upload - FACEBOOK_PAGE_ID not set")
        return {'status': 'skipped', 'reason': 'Missing credentials', 'platform': 'facebook'}

    print(f"[facebook] Credentials loaded")

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        error_msg = f"Video file not found: {video_path}"
        print(f"[facebook] {error_msg}")
        raise FileNotFoundError(error_msg)

    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[facebook] Video file found: {video_path}")
    print(f"[facebook] Video size: {file_size_mb:.2f} MB")

    print(f"[facebook] Uploading to Facebook Reels (3-step API)...")

    try:
        file_size = video_path_obj.stat().st_size

        print(f"[facebook] Step 1: Initiating upload session...")
        start_url = f"https://graph.facebook.com/v21.0/{page_id}/video_reels"
        start_data = {
            'access_token': access_token,
            'upload_phase': 'start',
            'file_size': file_size
        }
        res_start = requests.post(start_url, data=start_data, timeout=30)

        if res_start.status_code != 200:
            print(f"[facebook] Start Phase Error: {res_start.text}")
            raise Exception(f"Start Phase Failed: {res_start.text}")

        start_json = res_start.json()
        video_id = start_json.get('video_id')
        upload_url = start_json.get('upload_url')

        if not video_id:
             raise Exception(f"No video_id returned. Response: {start_json}")

        print(f"[facebook] Step 2: Transferring file to Facebook Servers...")
        headers = {
            'Authorization': f'OAuth {access_token}',
            'offset': '0',
            'file_size': str(file_size)
        }
        with open(video_path, 'rb') as f:
            res_transfer = requests.post(upload_url, headers=headers, data=f, timeout=600)

        if res_transfer.status_code != 200:
            print(f"[facebook] Transfer Phase Error: {res_transfer.text}")
            raise Exception(f"Transfer Phase Failed: {res_transfer.text}")

        print(f"[facebook] Step 3: Publishing Reel...")
        finish_url = f"https://graph.facebook.com/v21.0/{page_id}/video_reels"
        finish_data = {
            'access_token': access_token,
            'upload_phase': 'finish',
            'video_id': video_id,
            'description': description,
            'video_state': 'PUBLISHED'
        }
        res_finish = requests.post(finish_url, data=finish_data, timeout=60)

        if res_finish.status_code == 200 and res_finish.json().get('success'):
            print(f"[facebook] SUCCESS! Reel uploaded to Facebook!")
            print(f"[facebook] Video ID: {video_id}")
            print(f"[facebook] Check your Facebook Page Reels tab to see the post.")
            print("=" * 60)

            return {
                'id': video_id,
                'platform': 'facebook',
                'status': 'success',
                'url': f"https://facebook.com/{video_id}"
            }
        else:
            print(f"[facebook] Finish Phase Error: {res_finish.text}")
            raise Exception(f"Finish Phase Failed: {res_finish.text}")

    except requests.exceptions.Timeout:
        error_msg = "Upload timed out (video too large or slow connection)"
        print(f"[facebook] {error_msg}")
        print("=" * 60)
        raise Exception(error_msg)

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"[facebook] {error_msg}")
        print("=" * 60)
        raise Exception(error_msg)

    except Exception as e:
        print(f"[facebook] UNEXPECTED ERROR!")
        print(f"[facebook] Error type: {type(e).__name__}")
        print(f"[facebook] Error message: {str(e)}")
        print("=" * 60)
        raise

def upload_to_facebook_story(video_path):
    print("\n" + "=" * 60)
    print("FACEBOOK STORY UPLOAD STARTING - SELTOK LENS")
    print("=" * 60)

    access_token = os.getenv('FACEBOOK_ACCESS_TOKEN') or os.getenv('FB_ACCESS_TOKEN')
    page_id = os.getenv('FACEBOOK_PAGE_ID') or os.getenv('FB_PAGE_ID')

    if not access_token or not page_id:
        print("[facebook] Skipping Facebook Story - Missing credentials")
        return {'status': 'skipped', 'reason': 'Missing credentials', 'platform': 'facebook_story'}

    print(f"[facebook] Page ID: {page_id}")

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"[facebook] Video not found: {video_path}")

    try:
        print(f"[facebook] Uploading Story to Facebook (Sessions API)...")

        file_size = video_path_obj.stat().st_size

        print(f"[facebook] Step 1: Initiating upload session...")
        start_url = f"https://graph.facebook.com/v21.0/{page_id}/video_stories"
        start_data = {
            'access_token': access_token,
            'upload_phase': 'start',
            'file_size': file_size
        }
        res_start = requests.post(start_url, data=start_data, timeout=30)

        if res_start.status_code != 200:
             print(f"[facebook] Start Phase Error: {res_start.text}")
             raise Exception(f"Start Phase Failed: {res_start.text}")

        start_json = res_start.json()
        upload_session_id = start_json.get('upload_session_id')
        video_id = start_json.get('video_id')
        upload_url = start_json.get('upload_url')

        if upload_url:
            print(f"[facebook] Step 2: Transferring file via upload_url...")
            headers = {
                'Authorization': f'OAuth {access_token}',
                'offset': '0',
                'file_size': str(file_size)
            }
            with open(video_path, 'rb') as f:
                res_transfer = requests.post(upload_url, headers=headers, data=f, timeout=600)

            if res_transfer.status_code != 200:
                print(f"[facebook] Transfer Phase Error: {res_transfer.text}")
                raise Exception(f"Transfer Phase Failed: {res_transfer.text}")

            print(f"[facebook] Step 3: Finishing upload...")
            finish_url = f"https://graph.facebook.com/v21.0/{page_id}/video_stories"
            finish_data = {
                'access_token': access_token,
                'upload_phase': 'finish',
                'video_id': video_id
            }
            if upload_session_id:
                 finish_data['upload_session_id'] = upload_session_id

            res_finish = requests.post(finish_url, data=finish_data, timeout=60)

            if res_finish.status_code == 200 or res_finish.json().get('success'):
                print(f"[facebook] SUCCESS! Story uploaded!")
                print(f"[facebook] Video ID: {video_id}")
                print("=" * 60)
                return {'id': video_id, 'platform': 'facebook_story', 'status': 'success'}
            else:
                print(f"[facebook] Finish Phase Error: {res_finish.text}")
                raise Exception(f"Finish Phase Failed: {res_finish.text}")
        elif upload_session_id:
            print(f"[facebook] Step 2: Transferring file...")
            transfer_url = f"https://graph.facebook.com/v21.0/{page_id}/video_stories"

            with open(video_path, 'rb') as f:
                files = {'video_file_chunk': f}
                transfer_data = {
                    'access_token': access_token,
                    'upload_phase': 'transfer',
                    'start_offset': 0,
                    'upload_session_id': upload_session_id
                }
                res_transfer = requests.post(transfer_url, data=transfer_data, files=files, timeout=600)

            if res_transfer.status_code != 200:
                print(f"[facebook] Transfer Phase Error: {res_transfer.text}")
                raise Exception(f"Transfer Phase Failed: {res_transfer.text}")

            print(f"[facebook] Step 3: Finishing upload...")
            finish_url = f"https://graph.facebook.com/v21.0/{page_id}/video_stories"
            finish_data = {
                'access_token': access_token,
                'upload_phase': 'finish',
                'upload_session_id': upload_session_id,
                 'title': 'Story Upload'
            }
            res_finish = requests.post(finish_url, data=finish_data, timeout=60)

            if res_finish.status_code == 200 or res_finish.json().get('success'):
                print(f"[facebook] SUCCESS! Story uploaded!")
                print(f"[facebook] Video ID: {video_id}")
                print("=" * 60)
                return {'id': video_id, 'platform': 'facebook_story', 'status': 'success'}
            else:
                print(f"[facebook] Finish Phase Error: {res_finish.text}")
                raise Exception(f"Finish Phase Failed: {res_finish.text}")
        else:
             raise Exception(f"No upload_session_id or upload_url returned. Response: {start_json}")

    except Exception as e:
        print(f"[facebook] ERROR: {e}")
        raise e
