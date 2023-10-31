import socket
import subprocess
import time
import uvicorn
import asyncio
import sys
from fastapi import FastAPI
app = FastAPI()

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
            print(f"端口 {port} 已被占用,正在尝试杀死占用的进程...")
            if not kill_process_on_port(port):
                print(f"未能成功杀死端口号 {port} 的进程,正在重试...")
                retries += 1
            else:
                print(f"成功杀死端口号 {port} 的进程")
        else:
            print(f"端口 {port} 可用, 正在启动服务")
            break

        if retries == max_retries:
            print("已经超过最大重试次数,服务已停止")

    # 启动服务器
    print("开始启动服务器...")
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000)
    server = uvicorn.Server(config=config)
    loop = None

    try:
        config.setup_event_loop()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(server.serve())
    except:
        print("程序已经关闭")
        sys.exit()
        # 正常情况下不会走到这，但是防止应用程序无法关闭，所以多一重保障
        time.sleep(2)
        sys.exit()
