"""
Upload videos to VK (VKontakte) - SelTok Lens
"""
import os
import vk_api
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def upload_to_vk(video_path, description="", title=""):
    access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')

    def mask(s): return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else ("PLACEHOLDER (***)" if s == "***" else "MISSING")
    print(f"[vk] Group ID: {group_id}")
    print(f"[vk] Access Token: {mask(access_token)}")

    if not access_token or access_token == "***":
        print("VK Access token is missing or a placeholder. Skipping VK upload.")
        return {'status': 'skipped', 'reason': 'missing_credentials'}
    if not group_id or group_id == "***":
        print("VK Group ID is missing or a placeholder. Skipping VK upload.")
        return {'status': 'skipped', 'reason': 'missing_credentials'}

    try:
        group_id_clean = str(group_id).lstrip('-')
        group_id_int = int(group_id_clean)
    except ValueError:
        print(f"Invalid VK Group ID format: '{group_id}'. Skipping VK upload.")
        return {'status': 'skipped', 'reason': 'invalid_group_id'}

    print(f"Starting VK upload...")
    print(f"Video: {video_path}")
    print(f"Group ID: {group_id}")

    try:
        print("\nInitializing VK session...")
        vk_session = vk_api.VkApi(token=access_token)
        vk = vk_session.get_api()
        upload = vk_api.VkUpload(vk_session)

        message = description if description else "SelTok Lens - Selena Gomez Moments!\n\n#selenagomez #hollywood #celebrity #fashion"

        if not message.strip():
            message = "New video!"

        print("\nUploading video to VK...")

        video = upload.video(
            video_file=str(video_path),
            name=title or 'SelTok Lens Video',
            description=description[:220] if description else '',
            group_id=group_id_int,
            wallpost=0
        )

        print(f"Video uploaded successfully!")
        print(f"Video ID: {video['video_id']}")
        print(f"Owner ID: {video['owner_id']}")

        print("\nPosting to community wall...")

        attachment = f"video{video['owner_id']}_{video['video_id']}"

        post_result = vk.wall.post(
            owner_id=-group_id_int,
            from_group=1,
            message=message,
            attachments=attachment
        )

        post_id = post_result['post_id']
        post_url = f"https://vk.com/wall-{group_id_int}_{post_id}"

        print(f"Posted to wall successfully!")
        print(f"Post ID: {post_id}")
        print(f"View post: {post_url}")

        result = {
            'success': True,
            'video_id': video['video_id'],
            'owner_id': video['owner_id'],
            'post_id': post_id,
            'post_url': post_url,
            'message': 'Video uploaded and posted to VK successfully'
        }

        print(f"\nVK Upload Complete!")

        return result

    except vk_api.exceptions.ApiError as e:
        error_msg = f"VK API Error: {e}"
        print(f"\n{error_msg}")
        raise Exception(error_msg)

    except FileNotFoundError:
        raise Exception(f"Video file not found: {video_path}")

    except Exception as e:
        raise Exception(f"Failed to upload to VK: {e}")
