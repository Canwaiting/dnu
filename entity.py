import os
from PIL import Image
import yt_dlp
import datetime
import requests
from peewee import *


class Video(Model):
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
    is_have_info = BooleanField(default=False)
    is_have_subtitle_en = BooleanField(default=False)
    is_have_subtitle_zh = BooleanField(default=False)
    is_upload_net_disk = BooleanField(default=False)
    is_editing_video = BooleanField(default=False)
    is_upload_bilibili = BooleanField(default=False)
    is_ignored = BooleanField(default=False)
    upload_bilibili_time = CharField(null=True)
    download_time = CharField(null=True)
    create_time = CharField(null=True)


    channel_table_name = ""
    download_type = ""  # audio / video / thumbnail
    video_status_info = {
        "status" : "",
        "percent" : "",
        "speed" : "",
        "eta" : ""
    }
    audio_status_info = {
        "status" : "",
        "percent" : "",
        "speed" : "",
        "eta" : ""
    }
    thumbnail_status_info = {
        "status" : ""
    }

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
            self.is_have_info = True
            # self.is_ignored = True
            current_datetime = datetime.datetime.now()
            formatted_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            self.create_time = formatted_string

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

        current_datetime = datetime.datetime.now()
        formatted_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        self.download_time = formatted_string

    def get_channel_table_name(self):
        SubscribeChannel._meta.database = self._meta.database
        result = SubscribeChannel.get_or_none(SubscribeChannel.channel_id == self.channel_id)
        if result is not None:
            self.channel_table_name = result.table_name
        return self.channel_table_name

    def save_in_table(self, table_name):
        original_table_name = self._meta.table_name
        self._meta.set_table_name(table_name)
        self._meta.database.create_tables([self], safe=True)  # safe=True 使得不会重复创建
        self.save()
        self._meta.set_table_name(original_table_name)

class SubscribeChannel(Model):
    channel_name = CharField(null=True)
    channel_id = CharField(null=True)
    table_name = CharField(null=True)
    initial_time = CharField(null=True)
    last_update_time = CharField(null=True)
