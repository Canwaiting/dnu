from entity import *

def download(youtube_url):
    # 初始化数据库、对象
    db = SqliteDatabase('dnu.db')
    db.connect()
    video = Video()
    video._meta.database = db
    video._meta.table_name = 'history'
    db.create_tables([video], safe=True)  # safe=True 使得不会重复创建

    video.get_info(youtube_url)
    video.create_download_directory()
    video.download_thumbnail()
    video.download_audio()
    video.download_video()
    video.save()

    # 如果是已经订阅的频道，那么也更新相应频道表的数据
    SubscribeChannel._meta.database = db
    result = SubscribeChannel.get_or_none(SubscribeChannel.channel_id == video.channel_id)
    if result is not None:
        print("发现您已订阅该视频的频道，正在查询是否需要同步更新...")
        Video._meta.database = db
        Video._meta.table_name = result.table_name
        another_result = Video.get_or_none(Video.youtube_url == video.youtube_url)
        if another_result is not None:
            print("记录已存在，更新下载时间...")
            current_datetime = datetime.datetime.now()
            formatted_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            another_result.download_time = formatted_string
            another_result.save()
        else:
            print("记录未存在，正在记录...")
            video._meta.table_name = result.table_name
            video.save()


def main():
    # 初始化数据库、对象
    db = SqliteDatabase('dnu.db')
    db.connect()
    video = Video()
    video._meta.database = db
    video._meta.table_name = 'history'
    db.create_tables([video], safe=True)  # safe=True 使得不会重复创建

    youtube_url = input("请输入Youtube视频地址：")  # https://www.youtube.com/watch?v=BaW_jenozKc

    video.get_info(youtube_url)
    video.create_download_directory()
    video.download_thumbnail()
    video.download_audio()
    video.download_video()
    video.save()

    # 如果是已经订阅的频道，那么也更新相应频道表的数据
    SubscribeChannel._meta.database = db
    result = SubscribeChannel.get_or_none(SubscribeChannel.channel_id == video.channel_id)
    if result is not None:
        print("发现您已订阅该视频的频道，正在查询是否需要同步更新...")
        Video._meta.database = db
        Video._meta.table_name = result.table_name
        another_result = Video.get_or_none(Video.youtube_url == video.youtube_url)
        if another_result is not None:
            print("记录已存在，更新下载时间...")
            current_datetime = datetime.datetime.now()
            formatted_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            another_result.download_time = formatted_string
            another_result.save()
        else:
            print("记录未存在，正在记录...")
            video._meta.table_name = result.table_name
            video.save()


if __name__ == '__main__':
    main()
