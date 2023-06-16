# dnu

给出yotuube链接，即可完成下载（download)，并（and）上传（upload）到bilibili的操作

## 运行要求

- python（建议使用[Anaconda](https://www.anaconda.com/)的虚拟环境配置）
- biliup（本项目已包含，[原项目地址](https://github.com/biliup/biliup-rs)）
- youtube data api（[获取api密钥文档地址](https://developers.google.com/youtube/v3/quickstart/python?hl=zh-cn)）

## 快速使用

1、拉取项目
```shell
git clone https://github.com/Canwaiting/dnu
```

2、进入项目

3、运行biliup获取哔哩哔哩cookie（建议使用扫码）
```shell
./biliup
```

4、运行sqlite.py创建对应的表
```shell
python sqlite.py
```

5、修改config.toml中的youtube data api字段
```shell
[youtube]
data_api_key = "必填"
```

6、已完成所有前期步骤，下面是使用例子
```shell
# 替换youtube_url为对应youtube视频链接即可
python dnu.py youtube_url
```