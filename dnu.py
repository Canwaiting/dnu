from entity import *

def download(youtube_url):
    db = SqliteDatabase('dnu.db')
    db.connect()

    video = Video()
    video._meta.database = db
    video.get_info(youtube_url)
    video.create_download_directory()
    video.download_thumbnail()
    video.download_audio()
    video.download_video()

    my_save(video)

def my_save(video):
    print("")
    print("正在保存到历史下载记录...")
    video.save_in_table('history')

    channel_table_name = video.get_channel_table_name()
    if channel_table_name != "":
        print("")
        print(f"发现已订阅频道：{video.channel}，正在同步更新记录到表：{channel_table_name}...")
        print("注意：若无视频记录，则会插入。否则，更新相应字段。")
        result = search_video_in_table(video.youtube_url, channel_table_name)
        if result is not None:
            print("")
            print("存在记录，正在更新相应字段...")
            video.id = result.id
            video.create_time = result.create_time
            video.is_ignored = False
        else:
            print("")
            print("无记录，正在插入记录...")
        video.save_in_table(channel_table_name)  # save逻辑是根据自动生成的id的

def search_video_in_table(video_url, table_name):
    original_table_name = Video._meta.table_name
    Video._meta.set_table_name(table_name)
    result = Video.get_or_none(Video.youtube_url == video_url)
    Video._meta.set_table_name(original_table_name)
    return result


db = SqliteDatabase('dnu.db')
db.connect()
Video._meta.database = db

if __name__ == '__main__':
    youtube_url = input("请输入Youtube视频地址：")  # https://www.youtube.com/watch?v=BaW_jenozKc
    download(youtube_url)

db.close()