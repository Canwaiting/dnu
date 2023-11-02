import logging
import shutil
import os
from PIL import Image
import yt_dlp
import re
import datetime
import requests
from peewee import *
import scrapetube
from dnu import *
from dnu import download


class NullLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass
    def error(self, msg):
        pass

ydl_opts = {
    'quiet': True,
    'logger': NullLogger(),
    'noprogress': True
}

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
        get_info_ydl_opts = ydl_opts.copy()
        get_info_ydl_opts.update({})

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
            my_logger.info(f"成功拉取视频信息，标题：{self.title}，链接：{self.youtube_url}")

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

    def update_in_table(self, table_name):
        original_table_name = self._meta.table_name
        self._meta.set_table_name(table_name)
        self.save()
        self._meta.set_table_name(original_table_name)

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

    def get_update_videos_url(self,channel_name, table_name):
        my_logger.info(f"正在拉取最新，频道：{channel_name}")
        my_logger.info(f"正在拉取最新，频道表名：{table_name}")
        videos_url = []
        result = scrapetube.get_channel(channel_name)  # videos[0] 为最新发布的， videos[last] 为最久之前发布的
        for video in result:
            youtube_url = "https://www.youtube.com/watch?v=" + str(video['videoId'])
            if VideoManager().is_video_already_in_db(youtube_url, table_name) is False:
                videos_url.append(youtube_url)
            else:
                break

        return videos_url

class SingletonMeta(type):
    """简单实现懒汉单例模式"""
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class DatabaseManager(metaclass=SingletonMeta):
    def __init__(self, db_path='dnu.db'):
        self.db = SqliteDatabase(db_path)
        self.db.connect()

        # 创建默认表（下载历史-history，订阅频道-subscribechannel）
        original_table_name = Video._meta.table_name
        Video._meta.set_database(self.db)
        Video._meta.set_table_name('history')
        self.db.create_tables([Video], safe=True)
        Video._meta.set_table_name(original_table_name)

        SubscribeChannel._meta.set_database(self.db)
        self.db.create_tables([SubscribeChannel], safe=True)

    def close(self):
        self.db.close()


class Logger(metaclass=SingletonMeta):
    def __init__(self, name=__name__, level=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s','%Y-%m-%d %H:%M:%S')
        ch.setFormatter(formatter)

        # 给logger添加handler
        self.logger.addHandler(ch)

    def get_logger(self):
        return self.logger

my_logger = Logger(__name__).get_logger()

class DNUHelper():
    def generate_youtube_url_list_to_txt(self,channel_table_name,youtube_url_list):
        current_datetime = datetime.datetime.now()
        formatted_string = current_datetime.strftime("%Y%m%d")
        file_name = f"./{formatted_string}-{channel_table_name}.txt"
        with open(f"{file_name}", "w") as file:
            file.write("\n".join(youtube_url_list))
        my_logger.info(f"正在生成本次更新的记录到 {file_name} 文件中")

    def copy_mp3_to_a_folder(self,youtube_url_list, folder_path):
        my_logger.info("正在拷贝.mp3到对应的文件夹中");
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        for youtube_url in youtube_url_list:
            youtube_id = self.get_youtube_id_from_url(youtube_url)
            mp3_name = f"{youtube_id}.mp3"
            mp3_path = f"./{youtube_id}/{mp3_name}"
            new_mp3_path = f"{folder_path}/{mp3_name}"
            shutil.copy(mp3_path, new_mp3_path)  # source, destination

    def get_youtube_id_from_url(self,youtube_url):
        youtube_regex = (
            r'(https?://)?(www\.)?'
            '(youtube|youtu|youtube-nocookie)\.(com|be)/'
            '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )

        match = re.match(youtube_regex, youtube_url)
        if not match:
            return None

        return match.group(6)


    def generate_whisper_script(self,youtube_url_list, folder_path):
        script = ""
        script_srt = "mkdir -p srt"
        for youtube_url in youtube_url_list:
            youtube_id = self.get_youtube_id_from_url(youtube_url)
            mp3_name = f"{youtube_id}.mp3"

            script += f"whisper --model large-v2 {folder_path}/{mp3_name}"
            script += "\n"


            script_srt += "\n"
            script_srt += f"cp {folder_path}/{mp3_name} {folder_path}/srt/"



        file_name = f"{folder_path}-whisper.sh"
        with open(f"{file_name}", "w") as file:
            file.write(script)

        srt_file_name = f"{folder_path}-srt.sh"
        with open(f"{srt_file_name}", "w") as file:
            file.write(script_srt)

class VideoManager(metaclass=SingletonMeta):
    def is_video_already_in_db(self, youtube_url, table_name):
        Video._meta.table_name = table_name
        result = Video.get_or_none(Video.youtube_url == youtube_url)
        if result is not None:
            return True
        else:
            return False

    def load_videos_info_to_db(self,videos_youtube_url_list, table_name):
        i = 0
        for youtube_url in videos_youtube_url_list:  # videos[0] 为最新发布的， videos[last] 为最久之前发布的
            i = i + 1
            my_logger.info(f"正在获取视频的信息，进度：{i} / {len(videos_youtube_url_list)}")
            original_table_name = Video._meta.table_name
            subscribe_channel_video = Video()
            subscribe_channel_video._meta.set_table_name(table_name)
            subscribe_channel_video.get_info(youtube_url)
            subscribe_channel_video.save()  # TODO 怎么有日志知道保存了哪一些？到哪里就没有保存了？检测到哪里停了？
    def download_youtube_url_list(self,youtube_url_list):
        for youtube_url in youtube_url_list:
            download(youtube_url)
