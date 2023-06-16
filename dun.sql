-- 创建数据库
CREATE DATABASE dnu;
-- 使用库
USE dnu;

-- 创建 channels 表
CREATE TABLE channels (
  channel_id TEXT PRIMARY KEY,
  channel_name TEXT,
  added_time DATETIME
);

-- 创建 videos 表
CREATE TABLE videos (
  video_id TEXT PRIMARY KEY,
  channel_id TEXT,
  title TEXT,
  upload_time DATETIME,
  added_time DATETIME
);