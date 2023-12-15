import zipfile
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

    def get_info(self, youtube_url = None):
        if youtube_url == None:
            youtube_url = self.youtube_url
        get_info_ydl_opts = ydl_opts.copy()
        get_info_ydl_opts.update({})

        my_logger.info(f"开始拉取视频信息，链接：{self.youtube_url}")
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

    def only_download_and_save(self):
        self._meta.database = DatabaseManager().db
        self.create_download_directory()
        self.download_thumbnail()
        self.download_audio()
        self.download_video()
        self.my_save()

    def create_download_directory(self):
        my_logger.info(f"创建目录：{self.save_directory}")
        os.makedirs(self.save_directory, exist_ok=True)

    def download_thumbnail(self):
        # 下载缩略图，并将其转换为 RGB 格式
        file_name = f"{self.save_directory}{self.save_name}" # 命名规则
        my_logger.info(f"正在下载壁纸，下载到：{file_name}.png")
        imgData = requests.get(self.thumbnail).content
        with open(f"{file_name}.webp", "wb") as handler:
            handler.write(imgData)
        im = Image.open(f"{file_name}.webp").convert("RGB")
        im.save(f"{file_name}.png")
        if os.path.exists(f"{file_name}.webp"):
            os.remove(f"{file_name}.webp")

    def download_audio(self):
        my_logger.info("正在下载音频...")
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

    def my_save(self):
        my_logger.info("")
        my_logger.info("正在保存到历史下载记录...")
        self.save_in_table('history')

        channel_table_name = self.get_channel_table_name()
        if channel_table_name != "":
            my_logger.info("")
            my_logger.info(f"发现已订阅频道：{self.channel}，正在同步更新记录到表：{channel_table_name}...")
            my_logger.info("注意：若无视频记录，则会插入。否则，更新相应字段。")
            result = VideoManager().search_video_in_table(self.youtube_url, channel_table_name)
            if result is not None:
                my_logger.info("")
                my_logger.info("存在记录，正在更新相应字段...")
                self.id = result.id
                self.create_time = result.create_time
                self.is_ignored = False
            else:
                my_logger.info("")
                my_logger.info("无记录，正在插入记录...")
            self.save_in_table(channel_table_name)  # save逻辑是根据自动生成的id的

class SubscribeChannel(Model):
    channel_name = CharField(null=True)
    channel_id = CharField(null=True)
    table_name = CharField(null=True)
    initial_time = CharField(null=True)
    last_update_time = CharField(null=True)

    def get_update_videos_url(self,channel_name, channel_id, table_name):
        my_logger.info(f"正在拉取最新，频道：{channel_name}，表名：{table_name}")
        videos_url = []
        result = scrapetube.get_channel(channel_id)  # videos[0] 为最新发布的， videos[last] 为最久之前发布的
        for video in result:
            youtube_url = "https://www.youtube.com/watch?v=" + str(video['videoId'])
            if VideoManager().is_video_already_in_db(youtube_url, table_name) is False:
                videos_url.append(youtube_url)
            else:
                break

        return videos_url

    # def update_channel(self,channel_id,channel_table_name):
    #     # 获取该频道的更新
    #     youtube_url_list = SubscribeChannel().get_update_videos_url(channel_id, channel_table_name)
    #     my_logger.info(f"频道表：{channel_table_name} 有 {len(youtube_url_list)} 条更新")
    #
    #     if len(youtube_url_list) > 0:
    #         dnu_helper = DNUHelper()
    #         video_manager = VideoManager()
    #         video_manager.load_videos_info_to_db(youtube_url_list, channel_table_name)
    #         dnu_helper.generate_youtube_url_list_to_txt(channel_table_name,youtube_url_list)
    #         video_manager.download_youtube_url_list(youtube_url_list)
    #         current_datetime = datetime.datetime.now()
    #         formatted_string = current_datetime.strftime("%Y%m%d")
    #         folder_path = f"./{formatted_string}-{channel_table_name}"
    #         dnu_helper.copy_mp3_to_a_folder(youtube_url_list,folder_path)
    #         dnu_helper.generate_whisper_script(youtube_url_list,folder_path)
    #         my_logger.info(f"频道表：{channel_table_name} 同步更新完成")
    #     else:
    #         my_logger.info(f"频道表：{channel_table_name} 无需进行同步更新")

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

    def copy_mp3_to_one_zip(self,youtube_url_list, folder_path):
        self.copy_mp3_to_a_folder(youtube_url_list, folder_path)
        zip_path = f"{folder_path}.zip"
        my_logger.info(f"正在压缩.mp3到{folder_path}")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arc_name)


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

    def get_channel_table_name(self,channel_name):
        SubscribeChannel._meta.database = DatabaseManager().db
        result = SubscribeChannel.get_or_none(SubscribeChannel.channel_name == channel_name)
        if result is not None:
            return result.table_name
        return ""

    def get_channel_id(self,channel_name):
        SubscribeChannel._meta.database = DatabaseManager().db
        result = SubscribeChannel.get_or_none(SubscribeChannel.channel_name == channel_name)
        if result is not None:
            return result.channel_id
        return ""


    def generate_whisper_script(self,youtube_url_list, folder_path):
        script = ""
        script_srt = ""
        script_srt += f"mkdir -p {folder_path}/srt/"
        for youtube_url in youtube_url_list:
            youtube_id = self.get_youtube_id_from_url(youtube_url)
            mp3_name = f"{youtube_id}.mp3"

            script += f"whisper --model large-v3 {folder_path}/{mp3_name}"
            script += "\n"

            script_srt += "\n"
            script_srt += f"cp {folder_path}/{youtube_id}.srt {folder_path}/srt/{youtube_id}.srt"



        file_name = f"{folder_path}-whisper.sh"
        with open(f"{file_name}", "w") as file:
            file.write(script)

        srt_file_name = f"{folder_path}-srt.sh"
        script_srt += f"zip -q -r {folder_path}-zh-srt.zip {folder_path}/srt"
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
        download_task_list = DownloadTaskList()
        for youtube_url in youtube_url_list:
            download_task = DownloadTask(youtube_url)
            download_task_list.add(download_task)
            download_task.run()

    def search_video_in_table(self,video_url, table_name):
        original_table_name = Video._meta.table_name
        Video._meta.set_table_name(table_name)
        result = Video.get_or_none(Video.youtube_url == video_url)
        Video._meta.set_table_name(original_table_name)
        return result

class DownloadTaskList(metaclass=SingletonMeta):
    def __init__(self,initial_data=None):
        self._data = initial_data if initial_data is not None else []

    def add(self,download_task):
        self._data.append(download_task)

    def delete(self,download_task_id):
        for download_task in self._data:
            if download_task.download_task_id == download_task_id:
                self._data.remove(download_task)

    def get(self, download_task_id):
        for download_task in self._data:
            if download_task.download_task_id == download_task_id:
                return download_task
        return None



class DownloadTask:
    def __init__(self,youtube_url):
        self.youtube_url = youtube_url
        self.download_task_id = DNUHelper().get_youtube_id_from_url(youtube_url)
        self.status = ""
        self.percent = 0
        self.speed = ""
        self.eta = ""

    def run(self):
        video = Video()
        video._meta.database = DatabaseManager().db
        self.percent = 10

        video.get_info(self.youtube_url)
        self.percent = 30

        video.create_download_directory()
        self.percent = 50

        video.download_thumbnail()
        self.percent = 60

        video.download_audio()
        self.percent = 70

        video.download_video()
        self.percent = 90

        video.my_save()
        self.percent = 100


class UpdateSubscribedChannels:
    update_subscribed_channel_list = []

class UpdateSubscribedChannel:
    def __init__(self, channel_name="", channel_id="", update_count=-1, update_video_list=None):
        self.channel_name = channel_name
        self.channel_id = channel_id
        self.update_count = update_count
        self.update_video_list = update_video_list if update_video_list is not None else []

    def convert(self,subscribe_channel):
        self.channel_name = subscribe_channel.channel_name
        self.channel_id = subscribe_channel.channel_id

class TaskDict(metaclass=SingletonMeta):
    def __init__(self,initial_data=None):
        self._data = initial_data if initial_data is not None else {}

    @classmethod
    def add(cls,uuid,task):
        instance = cls()
        instance._data[uuid] = task

    @classmethod
    def delete(cls,uuid):
        instance = cls()
        del instance ._data[uuid]

    @classmethod
    def get(cls,uuid):
        instance = cls()
        return instance._data[uuid]
