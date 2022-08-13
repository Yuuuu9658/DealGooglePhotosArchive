# DealGooglePhotosArchive
修复Google 相册导出时产生的Meta混乱，时间错乱，产生短视频等问题

## Env 环境要求

- Python3
- ffmpeg

## Usage 用法

> 确保你正确安装了`ffmpeg`，并在命令行执行 `ffmpeg` 语句有效

先修改`DealGooglePhotosArchive.py`最下方的`scanDir`变量值为你文件夹的绝对路径，然后执行下面的命令

```
pip3 install -r requirements.txt
python3 DealGooglePhotosArchive.py 
```


#### 思路

因为Google Photos归档的文件都是各种相册，分散在很多个文件夹里，而且有很多重复，所以脚本目前就是做了几件事：

- 整理出重复的文件，把重复文件单独归类，
- Google把HEIC分解成了JPG和MOV，脚本把MOV（一般是小于3秒的短视频）单独归类到文件夹中
- 有些图片的Meta信息丢失，或者时间混乱，脚本根据Google归档的Exif文件重新写入对应的图片中
- ...

[大概思路](./info.md)
