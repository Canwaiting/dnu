from PIL import Image
from peewee import Model, CharField,IntegerField,BooleanField, SqliteDatabase, DateTimeField
import datetime
import json
import requests
import yt_dlp
import os

db = SqliteDatabase('dnu.db')

class BaseModel(Model):
    class Meta:
        database = db
class Video(BaseModel):
    title = CharField(null=True)
    description = CharField(null=True)
    upload_date = CharField(null=True)
    thumbnail = CharField(null=True)
    youtube_id = CharField(null=True)
    youtube_url = CharField(null=True)
    channel_id = CharField(null=True)
    channel = CharField(null=True)
    save_name = CharField(null=True)
    save_directory = CharField(null=True)
    is_have_subtitle_en = BooleanField(null=True)
    is_have_subtitle_zh = BooleanField(null=True)
    is_upload_net_disk = BooleanField(null=True)
    is_editing_video = BooleanField(default=False)
    is_upload_bilibili = BooleanField(default=False)
    upload_bilibili_time = CharField(null=True)
    download_time = CharField(null=True)

    def __str__(self):
        return f"""
        Video:
            Title: {self.title}
            Description: {self.description}
            Upload Date: {self.upload_date}
            Thumbnail: {self.thumbnail}
            YouTube ID: {self.youtube_id}
            YouTube URL: {self.youtube_url}
            Channel ID: {self.channel_id}
            Channel: {self.channel}
            Save Name: {self.save_name}
            Save Directory: {self.save_directory}
        """

    def get_info(self, youtube_url):
        ydl_opts = {}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            info_dict = ydl.sanitize_info(info)

            self.title = info_dict['title']
            self.description = info_dict['description']
            self.upload_date = info_dict['upload_date']
            self.thumbnail = info_dict['thumbnail']
            self.youtube_id = info_dict['id']
            self.youtube_url = info_dict['webpage_url']
            self.channel_id = info_dict['channel_id']
            self.channel = info_dict['channel']
            self.save_name = f"{self.youtube_id}"
            self.save_directory = f"./{self.youtube_id}/"

    def create_download_directory(self):
        os.makedirs(self.save_directory, exist_ok=True)

    def download_thumbnail(self):
        # 下载缩略图，并将其转换为 RGB 格式
        imgData = requests.get(self.thumbnail).content
        file_name = f"{self.save_directory}{self.save_name}" # 命名规则
        with open(f"{file_name}.webp", "wb") as handler:
            handler.write(imgData)
        im = Image.open(f"{file_name}.webp").convert("RGB")
        im.save(f"{file_name}.png")
        if os.path.exists(f"{file_name}.webp"):
            os.remove(f"{file_name}.webp")

    def download_audio(self):
        ydl_opts = {
            'format': 'm4a/bestaudio/best',
            'outtmpl': f'{self.save_directory}{self.save_name}.mp3',
            # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
            'postprocessors': [{  # Extract audio using ffmpeg
                'key': 'FFmpegExtractAudio',
            }]
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download(self.youtube_url)

    def download_video(self):
        ydl_opts = {
            'format' : 'bv[height<=1080][ext=mp4]+ba[ext=m4a]',
            'outtmpl': f'{self.save_directory}{self.save_name}.mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download(self.youtube_url)

        current_datetime = datetime.now()
        formatted_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        self.download_time = formatted_string

db.connect()
Video.create_table(fail_silently=True)


youtube_url = input("请输入Youtube视频地址：")  # https://www.youtube.com/watch?v=BaW_jenozKc

video = Video()
video.get_info(youtube_url)
video.create_download_directory()
video.download_thumbnail()
video.download_audio()
video.download_video()
video.save()
