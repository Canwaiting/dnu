from peewee import Model, CharField,IntegerField,BooleanField, SqliteDatabase, DateTimeField
import yt_dlp
import datetime
from entity import *
import scrapetube

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
        subscribe_channel_video = Video()
        subscribe_channel_video._meta.table_name = table_name
        subscribe_channel_video.get_info(youtube_url)
        subscribe_channel_video.save()
        i = i + 1


if __name__ == '__main__':
    # 初始化数据库、对象

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

    print("")
    print("完成同步")


