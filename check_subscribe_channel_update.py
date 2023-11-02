from time import sleep
from rich.console import Console
from dnu import *
from entity import *
import logging

db = DatabaseManager().db
dnu_helper = DNUHelper()
video_manager = VideoManager()
my_logger = Logger(__name__).get_logger()


if __name__ == '__main__':
    subscribe_channel = SubscribeChannel()
    subscribe_channel._meta.database = db
    subscribe_channel_list = list(subscribe_channel.select())

    my_logger.info("**********订阅的频道**********")
    i = 0
    for subscribe_channel in subscribe_channel_list:
        i = i + 1
        my_logger.info(f"频道名字：{subscribe_channel.channel_name}，所在表：{subscribe_channel.table_name}，进度：{i}/{len(subscribe_channel_list)}")
    my_logger.info("****************************")

    my_logger.info("正在同步更新...")
    for subscribe_channel in subscribe_channel_list:
        # 获取该频道的更新
        youtube_url_list = SubscribeChannel().get_update_videos_url(subscribe_channel.channel_id, subscribe_channel.table_name)
        my_logger.info(f"频道：{subscribe_channel.channel_name} 有 {len(youtube_url_list)} 条更新")

        if len(youtube_url_list) > 0:
            video_manager.load_videos_info_to_db(youtube_url_list, subscribe_channel.table_name)
            dnu_helper.generate_youtube_url_list_to_txt(subscribe_channel.table_name,youtube_url_list)
            video_manager.download_youtube_url_list(youtube_url_list)  #TODO 如果前面的拉取，或者是这个流程失败的话，后面就只能单个单个手动地去拉，而不是整体地去拉
            current_datetime = datetime.datetime.now()
            formatted_string = current_datetime.strftime("%Y%m%d")
            folder_path = f"./{formatted_string}-{subscribe_channel.table_name}"
            dnu_helper.copy_mp3_to_a_folder(youtube_url_list,folder_path)
            dnu_helper.generate_whisper_script(youtube_url_list,folder_path)
            my_logger.info(f"频道：{subscribe_channel.channel_name} 同步更新完成")
        else:
            my_logger.info(f"频道：{subscribe_channel.channel_name} 无需进行同步更新")

    my_logger.info("完成所有频道的同步")


db.close()
