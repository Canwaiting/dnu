import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import psutil
from pydantic import BaseModel
import uvicorn
import asyncio
from fastapi import FastAPI
import sys
import uvicorn
from dnu import *
from entity import *
from peewee import *

from entity import Video

my_logger = Logger(__name__).get_logger()
info_list = []

def change_progress(youtube_id, progress):
    for info in info_list:
        if youtube_id == info['youtube_id']:
            info['progress'] = progress

def download(youtube_url):
    youtube_id = DNUHelper().get_youtube_id_from_url(youtube_url)

    db = SqliteDatabase('dnu.db')
    db.connect()

    video = Video()
    video._meta.database = db
    change_progress(youtube_id, 10)

    video.get_info(youtube_url)
    change_progress(youtube_id, 30)

    video.create_download_directory()
    change_progress(youtube_id, 50)

    video.download_thumbnail()
    change_progress(youtube_id, 60)

    video.download_audio()
    change_progress(youtube_id, 70)

    video.download_video()
    change_progress(youtube_id, 90)

    my_save(video)
    change_progress(youtube_id, 100)

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


db = SqliteDatabase('dnu.db')
db.connect()
Video._meta.database = db


app = FastAPI()
executor = ThreadPoolExecutor(max_workers=1)

class Item(BaseModel):
    value: str

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

@app.post("/download/all")
def download_all(item: Item):
    youtube_url = item.value
    thread = threading.Thread(target=download, args=(youtube_url,))
    thread.start()
    youtube_id = DNUHelper().get_youtube_id_from_url(youtube_url)
    global info_list
    info = {}
    info['youtube_id'] = youtube_id
    info['progress'] = 0
    info_list.append(info)
    return {"message": youtube_id}


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