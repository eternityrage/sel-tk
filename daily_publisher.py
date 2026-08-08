import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        if os.path.exists(specific_video):
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"Error: Specific video {name} not found")
            return None, None

    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Selena Gomez's Most Iconic Red Carpet Moments",
        "Selena Gomez's Best Fashion Looks That Stun Everyone",
        "Selena Gomez's Most Iconic Roles Ranked",
        "Selena Gomez on the Red Carpet - Pure Elegance",
        "Selena Gomez's Best Talk Show Appearances",
        "The Rise of Selena Gomez - From Disney to Pop Icon",
        "Selena Gomez's Most Glamorous Met Gala Looks",
        "Selena Gomez Behind the Scenes - So Authentic",
        "Selena Gomez's Style Evolution",
        "Selena Gomez - Queen of Pop and Fashion",
    ]

    fallback_descriptions = [
        "Selena Gomez doesn't just walk red carpets - she owns them. From her iconic Wizards of Waverly Place days to her stunning Met Gala appearances, every look is a moment. She works with the biggest designers to create fashion history every single time. The way she carries herself, the confidence, the elegance - it's unmatched. Drop a fire emoji if you think Selena Gomez is the best-dressed celebrity of our generation! #selenagomez #hollywood #wizards #onlymurders #fashion #celebrity #redcarpet #selenagomezfan #actress #singer #icon #glamour #rarebeauty #disney",
        "Selena Gomez's portrayal of Alex Russo on Wizards of Waverly Place is one of the most iconic roles in Disney Channel history. The charm, the humor, the talent - she brought something real to every single scene. From Wizards to Only Murders in the Building, she left us speechless. Share this if you think Selena Gomez deserves ALL the recognition! #selenagomez #wizards #onlymurders #icon #celebrity #fashion #selenagomezfan #actress #singer #disney #rarebeauty #music",
        "When Selena Gomez won the hearts of millions on Wizards of Waverly Place, she made history. But when she built a beauty empire with Rare Beauty, she cemented her legacy. Her moments are always heartfelt, glamorous, and inspiring. She reminded us that there's beauty in being unapologetically yourself. Selena Gomez is proof that hard work, talent, and staying true to yourself pays off. Comment below with your favorite Selena Gomez role! #selenagomez #wizards #rarebeauty #hollywood #actress #icon #fashion #inspiring #selenagomezfan #talent #disney #music",
        "Selena Gomez on the interview circuit is an absolute joy to watch. Whether she's getting emotional talking about her mental health journey or giving profound answers about her career, she lights up every room. Her chemistry with interviewers is unmatched - she's funny, sharp, thoughtful, and down-to-earth. She's the kind of star who makes you feel like you're just chatting with a friend. Like if you could watch Selena Gomez interviews all day! #selenagomez #interviews #talkshow #hollywood #celebrity #selenagomezfan #funny #personality #icon #mentalhealth",
        "Before she was a beauty mogul and UNICEF ambassador, Selena Gomez was a Disney Channel star! She joined Wizards of Waverly Place and became one of the most memorable contestants EVER. Her performances brought energy and grace that wowed the judges week after week. She was a winner in our hearts. This girl was born to perform. Follow for more Selena Gomez throwback content! #selenagomez #wizards #disney #throwback #talent #selenagomezfan #actress #singer #performer #legendary #unicef",
        "Fashion has never seen a powerhouse quite like Selena Gomez. Each red carpet appearance is a masterclass in style - from her red carpet glam to Old Hollywood elegance at the Oscars. She works with the biggest designers to create moments that define fashion history. The elegant gowns. The bold choices. The stunning accessories. Every single time, she takes risks and every single time, she delivers. Comment which Selena Gomez look is your favorite! #selenagomez #fashionicon #style #redcarpet #metgala #highfashion #celebritystyle #couture #selenagomezstyle #fashiongoals #iconic",
        "Selena Gomez's talk show appearances are comedy gold! From teaching hosts how to dance to playing games and giving hilarious answers, she always brings the energy. Her impressions are hilarious, her stories are captivating, and she never takes herself too seriously. She's the celebrity everyone wants to interview because you never know what she'll do next. Like if Selena Gomez's laugh is your favorite sound! #selenagomez #funnymoments #talkshow #comedy #hollywood #celebrity #personality #selenagomezfan #entertainment #icon",
        "From her Wizards of Waverly Place roots to her music career and beauty empire, Selena Gomez has become one of the most versatile icons of her generation. She doesn't just play characters - she IS the character. Whether it's the Disney star, the pop singer, or the beauty mogul, she disappears into every role. Her filmography and career are already legendary. Follow for daily Selena Gomez content! #selenagomez #wizards #music #rarebeauty #hollywood #actress #singer #cinema #versatile #talent",
        "Selena Gomez's journey from Disney Channel star to pop icon is nothing short of inspirational. She started on Wizards of Waverly Place, graced every magazine cover, and proved everyone wrong with every step. She's used her platform to speak up about mental health and build an empire. She's not just a star - she's a role model for an entire generation. Her story proves that with talent, hard work, and authenticity, you can achieve anything. Share this if Selena Gomez inspires you! #selenagomez #inspiration #hollywood #successstory #wizards #rolemodel #rarebeauty #motivation #selenagomezfan #journey",
        "Selena Gomez's style evolution is one for the history books. From her early Disney days with colorful prints to becoming a full-blown fashion icon working with the biggest designers in the world. She's not afraid to take risks - short hair, long hair, suits, gowns, avant-garde, minimalist. She does it all and makes it look effortless. Every single look tells a story. Follow for style inspiration from the queen herself! #selenagomez #fashion #styleevolution #icon #celebrityfashion #streetstyle #ootd #redcarpet #glamour #beauty #selenagomezstyle #fashionista",
        "There's something about Selena Gomez behind the scenes that makes her even more lovable. The way she hypes up her friends, the genuine friendships she's built, the silly dance breaks, the kindness she shows to everyone around her - she's the real deal. Everyone who knows her says she's one of the most professional, humble, and talented people they've ever met. Hollywood needs more stars like Selena Gomez. Like if you agree! #selenagomez #bts #behindthescenes #real #authentic #hollywood #kindness #humble #talent #selenagomezfan #wholesome",
        "Selena Gomez at the Met Gala is appointment viewing. Year after year, she delivers some of the most talked-about looks in Met Gala history. She doesn't just attend the Met Gala - she defines it. Her commitment to the theme, her attention to detail, and her ability to transform is unmatched. Comment your favorite Selena Gomez Met Gala look! #selenagomez #metgala #fashion #vogue #redcarpet #highfashion #art #costume #selenagomezfan",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "exciting and celebratory - hype up Selena Gomez's talent, style, and iconic moments",
        "fun and engaging - make it feel like you're talking about your favorite celebrity with a friend",
        "inspiring and uplifting - highlight how Selena Gomez's journey motivates her fans",
        "glamorous and stylish - focus on her incredible fashion and red carpet looks",
        "emotional and heartfelt - showcase her powerful moments and the moments that move us",
        "funny and lighthearted - capture her amazing personality and hilarious interview moments",
        "nostalgic and throwback - celebrate her journey from Wizards of Waverly Place to icon status",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"about Selena Gomez for the Facebook page 'SelTok Lens'. "
        f"The page posts the best Selena Gomez moments - red carpet looks, interviews, music videos, "
        f"fashion, behind-the-scenes, and everything that makes Selena Gomez a pop culture icon. "
        f"Speak as a passionate Selena Gomez fan who loves celebrating her talent and style. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and fun. "
        f"Include engagement calls-to-action such as: "
        f"- Like if you love Selena Gomez! "
        f"- Comment your favorite Selena Gomez movie or moment! "
        f"- Share this with another Selena Gomez fan! "
        f"- Follow SelTok Lens for the best Selena Gomez content! "
        f"Include relevant hashtags in ALL LOWERCASE such as #selenagomez #hollywood #wizards #onlymurders #fashion #celebrity #redcarpet #selenagomezfan #actress #singer #icon #glamour #rarebeauty #disney. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("DAILY AUTOMATION STARTING - SELTOK LENS")
    print("=" * 60)

    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("No new videos found to publish. Exiting.")
        return

    print(f"Selected Video: {video_name}")
    print("Generating caption via Pollination AI...")
    title, description = generate_caption()

    print(f"Title: {title}")
    print(f"Description:\n{description}")

    combined_caption = f"{title}\n\n{description}"

    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }

    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"Instagram Reel upload failed: {e}")

    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"Instagram Story upload failed: {e}")

    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"Facebook Reel upload failed: {e}")

    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"Facebook Story upload failed: {e}")

    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"Threads upload failed: {e}")

    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["selenagomez", "hollywood", "wizards", "onlymurders", "fashion", "celebrity", "redcarpet", "selenagomezfan", "actress", "singer", "icon", "glamour", "rarebeauty", "disney", "seltoklens"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"YouTube upload failed: {e}")

    print("\nMarking video as published.")

    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)

    if is_recycled:
        print(f"   This is a recycled video (re-publishing)")

    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })

    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)

    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"Moved published video to {dest_path}")
    except Exception as e:
        print(f"Failed to move published video: {e}")

    print("DAILY AUTOMATION COMPLETE - SELTOK LENS")

if __name__ == "__main__":
    main()
