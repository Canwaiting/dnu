from entity import *
import scrapetube

db = SqliteDatabase('dnu.db')
db.connect()


def get_channel_all_videos(channel_id):
    videos = list(scrapetube.get_channel(channel_id))
    return videos

def record_subscribe_channel(dict_info,table_name):
    subscribe_channel = SubscribeChannel()
    subscribe_channel._meta.database = db
    subscribe_channel.create_table(fail_silently=True)

    current_datetime = datetime.datetime.now()
    formatted_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    result = subscribe_channel.get_or_none(subscribe_channel.channel_id == dict_info['channel_id'])
    if result is not None:
        result.last_update_time = formatted_string
        result.save()
        return

    subscribe_channel = SubscribeChannel()
    subscribe_channel._meta.database = db
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

def is_video_already_in_db(youtube_url,table_name):
    Video._meta.database = db
    Video._meta.table_name = table_name
    result = Video.get_or_none(Video.youtube_url == youtube_url)
    if result is not None:
        return True
    else:
        return False


if __name__ == '__main__':
    print("找到你想要持续关注的频道，输入该频道的任意一个 Youtube 视频链接即可记录该频道的所有视频信息入库")
    youtube_url = input(">> ")
    dict_info = parse_info(youtube_url)
    print(f"解析出 channel_name 为：{dict_info['channel_name']}")
    print(f"解析出 channel_id 为：{dict_info['channel_id']}")
    table_name = get_table_name(dict_info['channel_name'])
    print("正在记录到订阅的频道列表中...")
    record_subscribe_channel(dict_info, table_name)
    print(f"正在为频道：{dict_info['channel_name']} 创建表，表名：{table_name}")
    channel_video = Video()
    channel_video ._meta.database = db
    channel_video ._meta.table_name = table_name
    db.create_tables([channel_video], safe=True)  # safe=True 使得不会重复创建
    video_list = get_channel_all_videos(dict_info['channel_id'])
    print(f"频道：{dict_info['channel_name']}，共有：{len(video_list)}条视频")
    print("正在拉取该频道的所有视频信息到数据库，请稍候...")
    for video in video_list:  # videos[0] 为最新发布的， videos[last] 为最久之前发布的
        youtube_url = "https://www.youtube.com/watch?v=" + str(video['videoId'])
        subscribe_channel_video = Video()
        if is_video_already_in_db(youtube_url, table_name) == False:
            subscribe_channel_video.get_info(youtube_url)
            subscribe_channel_video.is_ignored = True
            subscribe_channel_video.save()
