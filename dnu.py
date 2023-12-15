import json
import traceback
import concurrent
import copy
import uuid
from enum import Enum

from fastapi.responses import JSONResponse
import asyncio
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import psutil
import uvicorn
from fastapi import FastAPI,Form,BackgroundTasks
from peewee import *
from pydantic import BaseModel

from entity import *
from http import HTTPStatus

class CommonResponse(BaseModel):
    code: int = 0
    message: str = ""
    data: dict = {}

class MyResponse(BaseModel):
    code: int
    message: str
    data: dict

class MyRequest(BaseModel):
    data: dict


class DownloadInfo(BaseModel):
    status: str = ""  # Info, Thumbnail, Audio, Video, Done
    status_message: str = ""
    percent: int = 0


class Item(BaseModel):
    value: str
    data: list


db = DatabaseManager().db
dnu_helper = DNUHelper()
video_manager = VideoManager()
my_logger = Logger(__name__).get_logger()
info_list = []
download_tasks_dict = {}

# 自定义日志配置
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "WARNING"},
        "uvicorn.error": {"level": "WARNING"},
        "uvicorn.access": {"handlers": ["default"], "level": "WARNING"},
    },
}


def change_progress(youtube_id, progress):
    for info in info_list:
        if youtube_id == info['youtube_id']:
            info['progress'] = progress


def download(youtube_url):
    global download_tasks_dict

    video = Video()
    video._meta.database = db

    download_tasks_dict[youtube_url].status = "Info"
    download_tasks_dict[youtube_url].status_message = "开始获取相关信息..."
    download_tasks_dict[youtube_url].percent= 10
    video.get_info(youtube_url)

    download_tasks_dict[youtube_url].status = "Thumbnail"
    download_tasks_dict[youtube_url].status_message = "开始下载封面..."
    download_tasks_dict[youtube_url].percent= 30
    video.create_download_directory()
    video.download_thumbnail()

    download_tasks_dict[youtube_url].status = "Audio"
    download_tasks_dict[youtube_url].status_message = "开始下载音频..."
    download_tasks_dict[youtube_url].percent= 60
    video.download_audio()

    download_tasks_dict[youtube_url].status = "Video"
    download_tasks_dict[youtube_url].status_message = "开始下载视频..."
    download_tasks_dict[youtube_url].percent= 80
    video.download_video()

    download_tasks_dict[youtube_url].status = "Done"
    download_tasks_dict[youtube_url].status_message = "下载完成"
    download_tasks_dict[youtube_url].percent= 100
    my_save(video)


def find_and_kill_process_by_port(port):
    for connection in psutil.net_connections(kind='inet'):
        try:
            # 检查状态是 LISTEN 的连接，并且地址和端口匹配
            if connection.status == psutil.CONN_LISTEN and connection.laddr == ('127.0.0.1', port):
                # 获取进程ID
                pid = connection.pid
                if pid:
                    # 根据进程ID创建进程对象
                    p = psutil.Process(pid)
                    # 尝试终止进程
                    p.terminate()
                    my_logger.info(f"Process with PID {pid} on port {port} has been terminated.")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


def my_save(video):
    my_logger.info("")
    my_logger.info("正在保存到历史下载记录...")
    video.save_in_table('history')

    channel_table_name = video.get_channel_table_name()
    if channel_table_name != "":
        my_logger.info("")
        my_logger.info(f"发现已订阅频道：{video.channel}，正在同步更新记录到表：{channel_table_name}...")
        my_logger.info("注意：若无视频记录，则会插入。否则，更新相应字段。")
        result = search_video_in_table(video.youtube_url, channel_table_name)
        if result is not None:
            my_logger.info("")
            my_logger.info("存在记录，正在更新相应字段...")
            video.id = result.id
            video.create_time = result.create_time
            video.is_ignored = False
        else:
            my_logger.info("")
            my_logger.info("无记录，正在插入记录...")
        video.save_in_table(channel_table_name)  # save逻辑是根据自动生成的id的


def search_video_in_table(video_url, table_name):
    original_table_name = Video._meta.table_name
    Video._meta.set_table_name(table_name)
    result = Video.get_or_none(Video.youtube_url == video_url)
    Video._meta.set_table_name(original_table_name)
    return result


app = FastAPI()
executor = ThreadPoolExecutor(max_workers=1)


def kill_process_on_port(port):
    try:
        # 查找使用给定端口的进程
        command = f"netstat -aon | findstr :{port}"
        result = subprocess.check_output(command, shell=True, text=True).strip().split("\n")[-1]
        process_id = result.split()[-1]

        if process_id:
            # 终止进程
            subprocess.run(f"taskkill /F /PID {process_id}", shell=True)
            return True
    except Exception as e:
        my_logger.info(f"Error while killing process on port {port}: {e}")


def is_port_in_use(port: int, host='127.0.0.1') -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False  # 端口未被占用
        except OSError:
            return True  # 端口被占用


@app.get("/")
def greet():
    return {"message": "Hello, world"}



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

def func(youtube_url):
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

@app.post("/subscribechannels")
def subscribe_channels(background_tasks: BackgroundTasks,youtube_url : str = Form(...)):
    background_tasks.add_task(func,youtube_url=youtube_url)
    response_data = CommonResponse(
        code=0,
        data={"youtube_url": youtube_url},
        message="正在开始订阅对应的频道",
    )
    return JSONResponse(content=response_data.model_dump())

@app.post("/update/subscribedchannels")
def post_update_subscribedchannels(background_tasks: BackgroundTasks):
    """更新所订阅的频道"""
    # 初始化任务，并添加到任务队列中
    unique_id = uuid.uuid4()
    unique_id_str = str(unique_id)
    update_subscribed_channels = UpdateSubscribedChannels()
    TaskDict.add(unique_id_str, update_subscribed_channels)

    background_tasks.add_task(update_subscribedchannels_background,uuid=unique_id_str)

    response_data = CommonResponse(
        code=0,
        data={"uuid": unique_id_str},
        message="",
    )
    return JSONResponse(content=response_data.model_dump())

def update_subscribedchannels_background(uuid):
    try:
        update_subscribed_channels = TaskDict.get(uuid)
        sc = SubscribeChannel()
        sc._meta.database = db
        sc_list = list(sc.select())
        # 填充基本信息：频道信息、需要更新的视频链接
        my_logger.info(f"开始更新频道，uuid：{uuid}")
        for sc_db in sc_list:
            update_sc = UpdateSubscribedChannel()
            update_sc.convert(sc_db)
            update_youtube_url_list = SubscribeChannel().get_update_videos_url(sc_db.channel_name,sc_db.channel_id,sc_db.table_name)
            update_sc.update_count = len(update_youtube_url_list)
            my_logger.info(f"频道：{update_sc.channel_name}，需更新数：{update_sc.update_count}")
            for update_youtube_url in update_youtube_url_list:
                video = Video()
                video.youtube_url = update_youtube_url
                update_sc.update_video_list.append(video)
            update_subscribed_channels.update_subscribed_channel_list.append(update_sc)
        # 开始获取信息、下载操作
        my_logger.info("开始获取信息并下载...")
        for update_sc in update_subscribed_channels.update_subscribed_channel_list:
            my_logger.info(f"频道：{update_sc.channel_name},需要更新的视频数：{len(update_sc.update_video_list)}")
            futures = [executor.submit(process_update, update_video) for update_video in update_sc.update_video_list]
            concurrent.futures.wait(futures)
    except Exception as e:
        my_logger.error(f"异常：{e}，堆栈信息：\n{traceback.format_exc()}")

def process_update(video : Video):
    my_logger.info(f"视频链接：{video.youtube_url}")
    video.get_info()
    video.only_download_and_save()


@app.get("/update/subscribedchannels")
def get_update_subscribedchannels(uuid : str = Form(...)):
    """获取更新的频道的进度"""
    update_subscribed_channels = TaskDict.get(uuid)

    # 直接返回字典
    response_data = CommonResponse(
        code=0,
        data={"update_subscribed_channels":update_subscribed_channels }, # TODO 还不能直接返回，要进行序列化
        message="",
    )
    return JSONResponse(content=response_data.model_dump())


def log_subscribed_channels(subscribe_channel_list):
    my_logger.info("**********订阅的频道**********")
    i = 0
    for subscribe_channel in subscribe_channel_list:
        i = i + 1
        my_logger.info(
            f"频道名字：{subscribe_channel.channel_name}，所在表：{subscribe_channel.table_name}，进度：{i}/{len(subscribe_channel_list)}")
    my_logger.info("****************************")

# def process_channel_updates(subscribe_channel_list):
#     my_logger.info("正在同步更新...")
#     for subscribe_channel in subscribe_channel_list:
#         # 获取该频道的更新
#         youtube_url_list = SubscribeChannel().get_update_videos_url(subscribe_channel.channel_id,
#                                                                     subscribe_channel.table_name)
#         my_logger.info(f"频道：{subscribe_channel.channel_name} 有 {len(youtube_url_list)} 条更新")
#
#         if len(youtube_url_list) > 0:
#             video_manager.load_videos_info_to_db(youtube_url_list, subscribe_channel.table_name)
#             dnu_helper.generate_youtube_url_list_to_txt(subscribe_channel.table_name, youtube_url_list)
#             video_manager.download_youtube_url_list(youtube_url_list)
#             current_datetime = datetime.datetime.now()
#             formatted_string = current_datetime.strftime("%Y%m%d")
#             folder_path = f"./{formatted_string}-{subscribe_channel.table_name}"
#             dnu_helper.copy_mp3_to_one_zip(youtube_url_list, folder_path)
#             dnu_helper.generate_whisper_script(youtube_url_list, folder_path)
#             my_logger.info(f"频道：{subscribe_channel.channel_name} 同步更新完成")
#         else:
#             my_logger.info(f"频道：{subscribe_channel.channel_name} 无需进行同步更新")
#     my_logger.info("完成所有频道的同步")

@app.post("/download")
def download_all(background_tasks: BackgroundTasks,youtube_url : str = Form(...)):
    global download_tasks_dict
    download_tasks_dict[youtube_url] = DownloadInfo()
    background_tasks.add_task(download,youtube_url=youtube_url)
    response_data = CommonResponse(
        code=0,
        data={"youtube_url": youtube_url},
        message="正在开始下载",
    )
    return JSONResponse(content=response_data.model_dump())

@app.get("/download/progress")
def get_download_progress(youtube_url:str):
    response_data = CommonResponse(
        code=0,
        data=download_tasks_dict[youtube_url].model_dump(),
        message="查询成功",
    )
    return JSONResponse(content=response_data.model_dump())

@app.post("/getinfo")
def get_info(item: Item):
    global info_list
    youtube_id = item.value
    for info in info_list:
        if info['youtube_id'] == youtube_id:
            return {"message": info['progress']}
    return {"message": 0}


@app.get("/server/shutdown")
async def shutdown():
    global server
    global loop
    loop.stop()
    await server.shutdown()


port = 8000
max_retries = 5
retries = 0

if __name__ == "__main__":
    while retries < max_retries:
        if is_port_in_use(port):
            my_logger.info(f"端口 {port} 已被占用,正在尝试杀死所有占用的进程...")
            if not find_and_kill_process_by_port(port):
                my_logger.info(f"未能成功杀死端口号 {port} 的进程,正在重试...")
                retries += 1
            else:
                my_logger.info(f"成功杀死端口号 {port} 的进程")
        else:
            my_logger.info(f"端口 {port} 可用, 正在启动服务")
            break

        if retries == max_retries:
            my_logger.info("已经超过最大重试次数,服务已停止")

    # 启动服务器
    my_logger.info("开始启动服务器...")
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000,log_config=log_config)
    server = uvicorn.Server(config=config)
    loop = None

    try:
        config.setup_event_loop()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(server.serve())
    except:
        my_logger.info("程序已经关闭")
        sys.exit()

db.close()
