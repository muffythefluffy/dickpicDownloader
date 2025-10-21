import os
import requests
import concurrent.futures
import itertools
import time
from tqdm import tqdm

subreddits = ["penis", "softies", "balls", "ratemycock", "cock"]
save_dir = 'dickpics'
os.makedirs(save_dir, exist_ok=True)

headers = {'User-agent': 'DickPicCollector 3.0'}
image_urls = []

print("Fetching dickpics from Reddit...")

for subreddit in subreddits:
    url = f"https://www.reddit.com/r/{subreddit}.json"
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        print(f"❌ Error fetching r/{subreddit} (Status Code: {response.status_code})")
        continue

    print(f"✅ Successfully fetched r/{subreddit}!")

    try:
        json_data = response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"❌ Failed to parse JSON from r/{subreddit}")
        continue

    for post in json_data.get('data', {}).get('children', []):
        post_url = post['data'].get('url', '')
        if post_url.endswith(('.jpg', '.png', '.gif')) or ('i.redd.it' in post_url):
            image_urls.append(post_url)

if not image_urls:
    print("❌ No dickpics were found :/")
    exit()

print(f"✅ Found {len(image_urls)} dickpics!")

download_choice = input("Do you want to download all of them? (yes/no): ").strip().lower()
if download_choice != 'yes':
    print("As you had a choice :3")

sizes = {}
total_size = 0

print("\nCalculating total download size... ", end="", flush=True)
spinner = itertools.cycle("/|\\-")  
start_time = time.time()

for img_url in image_urls:
    try:
        response = requests.head(img_url, headers=headers, timeout=5)
        size = int(response.headers.get('content-length', 0))
        sizes[img_url] = size
        total_size += size
    except Exception:
        sizes[img_url] = 0

    if time.time() - start_time > 0.1:
        print(next(spinner), end="\b", flush=True)
        start_time = time.time()

print(f"\rTotal download size: {total_size / 1_048_576:.2f} MB\n")

def download_image(img_url, progress_bar):
    filename = os.path.join(save_dir, os.path.basename(img_url))
    try:
        with requests.get(img_url, stream=True, timeout=15) as r:
            r.raise_for_status()
            total = sizes.get(img_url, 0)

            with open(filename, 'wb') as f:
                for chunk in r.iter_content(8192): 
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))

        return f"✅ {filename}"
    except Exception as e:
        return f"❌ Failed: {img_url} - {e}"

print("🚀 Downloading dickpics with turbo mode...")

failed_downloads = []

with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as progress_bar:
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor: # Можно понизить, если инет фигня
        futures = [executor.submit(download_image, url, progress_bar) for url in image_urls]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result.startswith("❌"):
                failed_downloads.append(result)

if failed_downloads:
    print("\nFailed to download the following images:")
    for failed in failed_downloads:
        print(failed)
else:
    print("\nAll dicpics downloaded successfully!")
