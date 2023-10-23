import threading
import time
import os
from fastapi import FastAPI
import uvicorn
import subprocess
import socket
import signal
from pydantic import BaseModel
import dnu

# 定义Pydantic模型
class DownloadRequest(BaseModel):
    youtube_url: str

app = FastAPI()
should_exit = False
server_pid = -1

@app.post("/download")
def download(request_data: DownloadRequest):
    youtube_url = request_data.youtube_url
    dnu.download(youtube_url)
    return {"message": f"成功下载 {youtube_url}"}

@app.get("/test")
def test():
    return {"message": "成功启动DNU服务器"}

@app.get("/server/shutdown")
def shutdown():
    global should_exit
    global server_pid
    should_exit = True
    server_pid = os.getpid()
    return {"message": "成功关闭DNU服务器"}


def is_port_in_use(port: int, host='127.0.0.1') -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False  # 端口未被占用
        except OSError:
            return True  # 端口被占用


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
        print(f"Error while killing process on port {port}: {e}")
        return False


def run_uvicorn():
    port = 8000
    max_retries = 5
    retries = 0

    while retries < max_retries:
        if is_port_in_use(port):
            print(f"端口 {port} 已被占用,正在尝试杀死占用的进程...")
            if not kill_process_on_port(port):
                print(f"未能成功杀死端口号 {port} 的进程,正在重试...")
                retries += 1
            else:
                print(f"成功杀死端口号 {port} 的进程")
        else:
            print(f"端口 {port} 可用, 正在启动服务")
            uvicorn.run(app, host="127.0.0.1", port=port)

        if retries == max_retries:
            print("已经超过最大重试次数,服务已停止")

# uvicorn main:app --reload
if __name__ == "__main__":
    t = threading.Thread(target=run_uvicorn)
    t.start()

    while True:
        if should_exit:
            time.sleep(2)
            print("开始关闭服务进程")
            os.kill(server_pid, signal.SIGTERM)
            t.join()
            print("5秒后开始关闭主线程")
            time.sleep(5)
            os.kill(os.getpid(), signal.SIGTERM)


