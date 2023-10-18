from PIL import Image
from peewee import Model, CharField,IntegerField,BooleanField, SqliteDatabase, DateTimeField
import datetime
import json
import requests
import yt_dlp
import os
import scrapetube


db = SqliteDatabase('dnu.db')

class BaseModel(Model):
    class Meta:
        database = db

class SubscribeChannelVideo(BaseModel):
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
            self.is_ignored = True
            current_datetime = datetime.datetime.now()
            formatted_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            self.create_time = formatted_string

    class Meta:
        table_name = ''


def get_channel_all_videos(channel_id):
    videos = list(scrapetube.get_channel(channel_id))
    return videos

class SubscribeChannel(BaseModel):
    channel_name = CharField(null=True)
    channel_id = CharField(null=True)
    table_name = CharField(null=True)
    initial_time = CharField(null=True)
    last_update_time = CharField(null=True)

db.connect()

def record_subscribe_channel(dict_info,table_name):
    SubscribeChannel.create_table(fail_silently=True)

    current_datetime = datetime.datetime.now()
    formatted_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    result = SubscribeChannel.get_or_none(SubscribeChannel.channel_id == dict_info['channel_id'])
    if result is not None:
        result.last_update_time = formatted_string
        result.save()
        return

    subscribe_channel = SubscribeChannel()
    subscribe_channel.channel_name = dict_info['channel_name']
    subscribe_channel.channel_id = dict_info['channel_id']
    subscribe_channel.table_name = table_name
    subscribe_channel.initial_time = formatted_string
    subscribe_channel.last_update_time = formatted_string
    subscribe_channel.save()

def get_table_name(channel_name):
    # 只保留英文，且转换成小写
    result = []
    for char in channel_name:
        if char.isalpha():
            result.append(char.lower())
    return ''.join(result)

def parse_info(youtube_url):
    ydl_opts = {}
    dict_info = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        info_dict = ydl.sanitize_info(info)
        dict_info['channel_name'] = info_dict['channel']
        dict_info['channel_id'] = info_dict['channel_id']
    return dict_info

def is_video_already_in_db(youtube_url):
    video = SubscribeChannelVideo.get_or_none(SubscribeChannelVideo.youtube_url == youtube_url)
    if video is not None:
        return True
    else:
        return False

print("找到你想要持续关注的频道，输入该频道的任意一个 Youtube 视频链接即可记录该频道的所有视频信息入库")
youtube_url = input(">> ")
dict_info = parse_info(youtube_url)
print(f"解析出 channel_name 为：{dict_info['channel_name']}")
print(f"解析出 channel_id 为：{dict_info['channel_id']}")
table_name = get_table_name(dict_info['channel_name'])
print(f"正在创建表，名为：{table_name}")
record_subscribe_channel(dict_info, table_name)
SubscribeChannelVideo._meta.table_name = table_name
SubscribeChannelVideo.create_table(fail_silently=True)
videos = get_channel_all_videos(dict_info['channel_id'])
print(f"合计有：{len(videos)}条视频")

print("正在拉取该频道的所有视频信息，请稍候...")
for video in videos:  # videos[0] 为最新发布的， videos[last] 为最久之前发布的
    youtube_url = "https://www.youtube.com/watch?v=" + str(video['videoId'])
    subscribe_channel_video = SubscribeChannelVideo()
    if is_video_already_in_db(youtube_url) == False:
        subscribe_channel_video.get_info(youtube_url)
        subscribe_channel_video.save()


