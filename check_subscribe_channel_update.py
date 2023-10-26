from peewee import Model, CharField,IntegerField,BooleanField, SqliteDatabase, DateTimeField
import yt_dlp
import datetime
from entity import *
import shutil
import scrapetube
import re
from dnu import *

db = SqliteDatabase('dnu.db')
db.connect()


def is_video_already_in_db(youtube_url,table_name):
    Video._meta.database = db
    Video._meta.table_name = table_name
    result = Video.get_or_none(Video.youtube_url == youtube_url)
    if result is not None:
        return True
    else:
        return False

def get_update_videos_url(channel_id, table_name):
    videos_url = []
    result = scrapetube.get_channel(channel_id)  # videos[0] 为最新发布的， videos[last] 为最久之前发布的
    for video in result:
        youtube_url = "https://www.youtube.com/watch?v=" + str(video['videoId'])
        print("")
        if is_video_already_in_db(youtube_url, table_name) is False:
            videos_url.append(youtube_url)
        else:
            break
        print("")

    return videos_url

def load_videos_info_to_db(videos_youtube_url_list, table_name):
    i = 1
    for youtube_url in videos_youtube_url_list:  # videos[0] 为最新发布的， videos[last] 为最久之前发布的
        print(f"获取第{i}个视频的信息")
        original_table_name = Video._meta.table_name
        subscribe_channel_video = Video()
        subscribe_channel_video._meta.set_table_name(table_name)
        subscribe_channel_video.get_info(youtube_url)
        subscribe_channel_video.save()
        i = i + 1

def generate_youtube_url_list_to_txt(channel_table_name,youtube_url_list):
    current_datetime = datetime.datetime.now()
    formatted_string = current_datetime.strftime("%Y%m%d")
    file_name = f"./{formatted_string}-{channel_table_name}.txt"
    with open(f"{file_name}", "w") as file:
        file.write("\n".join(youtube_url_list))
    print(f"正在生成本次更新的记录到 {file_name} 文件中")

def download_youtube_url_list(youtube_url_list):
    db = SqliteDatabase('dnu.db')
    db.connect()
    Video._meta.database = db

    for youtube_url in youtube_url_list:
        download(youtube_url)
def copy_mp3_to_a_folder(youtube_url_list, folder_path):
    print("正在拷贝.mp3到对应的文件夹中")
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    for youtube_url in youtube_url_list:
        youtube_id = get_youtube_id_from_url(youtube_url)
        mp3_name = f"{youtube_id}.mp3"
        mp3_path = f"./{youtube_id}/{mp3_name}"
        new_mp3_path = f"{folder_path}/{mp3_name}"
        shutil.copy(mp3_path, new_mp3_path)  # source, destination


def get_youtube_id_from_url(youtube_url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )

    match = re.match(youtube_regex, youtube_url)
    if not match:
        return None

    return match.group(6)

def generate_whisper_script(youtube_url_list, folder_path):
    script = ""
    script_srt = "mkdir -p srt"
    for youtube_url in youtube_url_list:
        youtube_id = get_youtube_id_from_url(youtube_url)
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

if __name__ == '__main__':
    subscribe_channel = SubscribeChannel()
    subscribe_channel._meta.database = db
    subscribe_channel_list = list(subscribe_channel.select())
    print("**********订阅的频道**********")
    for subscribe_channel in subscribe_channel_list :
        print(f"频道名字：{subscribe_channel.channel_name}，所在表：{subscribe_channel.table_name}")
    print("****************************")

    print("")
    print("正在同步更新，请稍候...")
    for subscribe_channel in subscribe_channel_list :
        youtube_url_list = get_update_videos_url(subscribe_channel.channel_id, subscribe_channel.table_name)
        print(f"频道：{subscribe_channel.channel_name} 有 {len(youtube_url_list)} 条更新")
        load_videos_info_to_db(youtube_url_list , subscribe_channel.table_name)
        print(f"频道：{subscribe_channel.channel_name} 同步更新完成")
        generate_youtube_url_list_to_txt(subscribe_channel.table_name,youtube_url_list)
        download_youtube_url_list(youtube_url_list)

        current_datetime = datetime.datetime.now()
        formatted_string = current_datetime.strftime("%Y%m%d")
        folder_path = f"./{formatted_string}-{subscribe_channel.table_name}"
        copy_mp3_to_a_folder(youtube_url_list,folder_path)
        generate_whisper_script(youtube_url_list,folder_path)

    print("")
    print("完成同步")


