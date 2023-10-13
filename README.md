# dnu

给出yotuube链接，即可完成下载（download)，并（and）上传（upload）到bilibili的操作

# 附言
目前只实现了下载（download），因为我感觉盲目地上传（upload），很容易制造垃圾，污染环境，没有什么意思。

# 快速开始

在页面右侧 Releases 下载最新的 .exe 程序，双击打开 或者 从 cmd 中打开

# 上手把玩

1、拉取项目
```shell
git clone https://github.com/Canwaiting/dnu
```

2、进入项目目录

3、安装依赖（推荐使用 anaconda）
```
conda create -n dnu python=3.9.18
conda activate dnu
pip install pdm
pdm install
```

4、打包源程序（.exe）
```
pyinstaller --onefile dnu.py
```

# 效果展示
启动

![run](https://cdn.jsdelivr.net/gh/Canwaiting/picfornote/202310131712107.jpg)

输入 Youtube 视频链接，并等待下载
![input](https://cdn.jsdelivr.net/gh/Canwaiting/picfornote/202310131731514.jpg)

下载成功后

![data](https://cdn.jsdelivr.net/gh/Canwaiting/picfornote/202310131732756.jpg)

下载后的资源：音频.mp3（最好的音质）、视频.mp4（最高画质不大于1080P）、封面.png

![resource](https://cdn.jsdelivr.net/gh/Canwaiting/picfornote/202310131731481.jpg)

相关数据将会插入数据库中

![](https://cdn.jsdelivr.net/gh/Canwaiting/picfornote/202310131733672.png)

数据行转换成JSON格式
```
{
	"table": "video",
	"rows":
	[
		{
			"id": 1,
			"title": "Kanye West - Suzy / Things Change [DONDA 2] [REMASTERED LEAK]",
			"description": "Kanye West - Suzy / Things Change [DONDA 2] [REMASTERED LEAK]\nUsed AI to increase the quality of Ye's vocals (as the original leak had low quality vocals from the worst mike possible)....",
			"upload_date": "20231011",
			"thumbnail": "https://i.ytimg.com/vi/iA9muRwstbs/maxresdefault.jpg",
			"youtube_id": "iA9muRwstbs",
			"youtube_url": "https://www.youtube.com/watch?v=iA9muRwstbs",
			"channel_id": "UCjUki3Pj93EZbs49idRw0Gw",
			"channel": "[yeunreleased]",
			"save_name": "iA9muRwstbs",
			"save_directory": "./iA9muRwstbs"
		}
	]
}
```
