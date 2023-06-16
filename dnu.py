from PIL import Image
import sqlite3
import requests
import json
import urllib.parse as p
from datetime import datetime, timezone, timedelta
import toml
import yt_dlp
import subprocess
import sys

# 从配置文件中读取 YouTube Data API 的密钥
config = toml.load('config.toml')
youtube_data_api_key = config['youtube']['data_api_key']

video_info = {}

def get_video_info() -> dict:
    # 从视频的 URL 中解析出视频的 ID
    url_data = p.urlparse(video_info["youtube_url"])
    query = p.parse_qs(url_data.query)
    video_id = query["v"][0]

    # 构建 API 请求的 URL
    base_video_url = 'https://www.googleapis.com/youtube/v3/videos?'
    first_url = base_video_url+'key={}&id={}&part=snippet,contentDetails,statistics'.format(youtube_data_api_key, video_id)

    # 发送请求并获取响应
    inp = requests.get(first_url)
    resp = json.loads(inp.text)
    
    full_video_info = resp['items'][0]

    # 提取所需的字段
    video_info["video_id"] = full_video_info["id"]
    video_info["channel_id"] = full_video_info["snippet"]["channelId"]
    video_info["title"] = full_video_info["snippet"]["title"]
    upload_time_utc = datetime.strptime(full_video_info['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
    upload_time_east8 = (upload_time_utc + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    video_info["upload_time"] = upload_time_east8

    return video_info

def save_video_info() -> None:
    conn = sqlite3.connect('dnu.db')
    cur = conn.cursor()

    # 在数据库中查询该视频是否已存在
    cur.execute("SELECT video_id FROM videos WHERE video_id = ?", (video_info["video_id"],))
    result = cur.fetchone()

    # 如果视频在数据库中不存在，则插入新纪录
    if result is None:
        cur.execute("""
            INSERT INTO videos (video_id, channel_id, title, upload_time, added_time) 
            VALUES (?, ?, ?, ?, ?)
        """, (
            video_info["video_id"], 
            video_info["channel_id"], 
            video_info["title"], 
            video_info["upload_time"], 
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    conn.commit()
    conn.close()

def download_video():
    # 设置下载音频的选项
    audio_ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'outtmpl': './resource/%(channel)s/%(id)s',
        'socket_timeout': 180,
        'retries': 10
    }
    # 设置下载视频的选项
    video_ydl_opts = {
        'format' : 'bv[height<=1080][ext=mp4]+ba[ext=m4a]',
        'outtmpl': './resource/%(channel)s/%(id)s.mp4',
        'socket_timeout': 180,
        'retries': 10
    }

    with yt_dlp.YoutubeDL(audio_ydl_opts) as ydl:
        # 下载音频文件
        ydl.download([video_info["youtube_url"]])

    with yt_dlp.YoutubeDL(video_ydl_opts) as ydl:
        # 获取视频信息
        extract_info = ydl.extract_info(video_info["youtube_url"], download=False)
        # 更新视频信息并存储下载的文件路径
        video_info['description'] = extract_info['description']
        video_info['video_path'] = f"./resource/{extract_info['channel']}/{extract_info['id']}.mp4"
        video_info['audio_path'] = f"./resource/{extract_info['channel']}/{extract_info['id']}.mp3"
        video_info['thumbnail_path'] = f"./resource/{extract_info['channel']}/{extract_info['id']}.png"
        # 下载视频文件
        ydl.download([video_info["youtube_url"]])
        # 下载缩略图，并将其转换为 RGB 格式
        imgData = requests.get(extract_info['thumbnail']).content
        with open(f"./resource/{extract_info['channel']}/{extract_info['id']}.webp", "wb") as handler:
            handler.write(imgData)
        im = Image.open(f"./resource/{extract_info['channel']}/{extract_info['id']}.webp").convert("RGB")
        im.save(f"./resource/{extract_info['channel']}/{extract_info['id']}.png")

def upload_video_to_bilibili():
    # 使用 biliup 工具上传视频到 B 站
    return_code = subprocess.run([
    './biliup', 'upload', f"{video_info['video_path']}",
    '--copyright', '2',
    '--cover', f"{video_info['thumbnail_path']}",
    '--desc', f"{video_info['description'][:99]}",
    '--source', f'{video_info["youtube_url"][:79]}',
    '--tag', 'youtube',
    '--title', f'{video_info["title"][:79]}',
    ])
    print("return code:", return_code)

if __name__ == '__main__':
    video_info["youtube_url"] = sys.argv[1]
    get_video_info()
    download_video()
    save_video_info()
    upload_video_to_bilibili()