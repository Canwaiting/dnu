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


@app.get("/subscribechannels")
def get_subscribe_channel_list():
    subscribe_channel = SubscribeChannel()
    subscribe_channel._meta.database = db
    subscribe_channel_list = list(subscribe_channel.select())
    data_list = []
    for channel in subscribe_channel_list:
        data_list.append(channel.__data__)
    my_dict = {"len":len(data_list), "subscribechannels":data_list}
    myResponse = MyResponse(code=HTTPStatus.OK,
                            message="",
                            data=my_dict)
    return myResponse


@app.post("/channel/update/videoinfo/{channel_name}")
def update_channel(channel_name: str):
    '''

    :param channel_id:
    :return: 数量，youtube_url
    '''
    subscribe_channel = SubscribeChannel.get_or_none(SubscribeChannel.channel_name == channel_name)
    youtube_url_list = SubscribeChannel().get_update_videos_url(subscribe_channel.channel_id,
                                                                subscribe_channel.table_name)
    item = Item(value=f"{len(youtube_url_list)}", data=youtube_url_list)
    return item


@app.post("/channel/download/update/{channel_name}")
def update_channel(channel_name: str):
    channel_table_name = DNUHelper().get_channel_table_name(channel_name)
    channel_id = DNUHelper().get_channel_id(channel_name)
    thread = threading.Thread(target=SubscribeChannel().update_channel, args=(channel_id, channel_table_name,))
    thread.start()
    return {"message": "正在开始更新频道"}


@app.get("/check/update")
def check_update():
    subscribe_channel = SubscribeChannel()
    subscribe_channel._meta.database = db
    subscribe_channel_list = list(subscribe_channel.select())

    my_logger.info("**********订阅的频道**********")
    i = 0
    for subscribe_channel in subscribe_channel_list:
        i = i + 1
        my_logger.info(
            f"频道名字：{subscribe_channel.channel_name}，所在表：{subscribe_channel.table_name}，进度：{i}/{len(subscribe_channel_list)}")
    my_logger.info("****************************")

    my_logger.info("正在同步更新...")
    for subscribe_channel in subscribe_channel_list:
        # 获取该频道的更新
        youtube_url_list = SubscribeChannel().get_update_videos_url(subscribe_channel.channel_id,
                                                                    subscribe_channel.table_name)
        my_logger.info(f"频道：{subscribe_channel.channel_name} 有 {len(youtube_url_list)} 条更新")

        if len(youtube_url_list) > 0:
            video_manager.load_videos_info_to_db(youtube_url_list, subscribe_channel.table_name)
            dnu_helper.generate_youtube_url_list_to_txt(subscribe_channel.table_name, youtube_url_list)
            video_manager.download_youtube_url_list(
                youtube_url_list)  # TODO 如果前面的拉取，或者是这个流程失败的话，后面就只能单个单个手动地去拉，而不是整体地去拉
            current_datetime = datetime.datetime.now()
            formatted_string = current_datetime.strftime("%Y%m%d")
            folder_path = f"./{formatted_string}-{subscribe_channel.table_name}"
            dnu_helper.copy_mp3_to_a_folder(youtube_url_list, folder_path)
            dnu_helper.generate_whisper_script(youtube_url_list, folder_path)
            my_logger.info(f"频道：{subscribe_channel.channel_name} 同步更新完成")
        else:
            my_logger.info(f"频道：{subscribe_channel.channel_name} 无需进行同步更新")

    my_logger.info("完成所有频道的同步")
    return {"message": "完成所有频道的同步"}

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
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000)
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
