#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author  : gty0211@foxmail.com
import json
import os
import shutil
import time
import ffmpeg
import piexif
from PIL import Image, UnidentifiedImageError

#归档zip解压目录
scanDir = ''

#处理重复
def dealDuplicate(delete=True):
    fileList = {}
    dg = os.walk(scanDir)
    for path,dir_list,file_list in dg:
        for file_name in file_list:
            full_file_name = os.path.join(path, file_name)
            if file_name == '元数据.json':
                continue
            #处理重复文件
            if file_name in fileList.keys():
                DupDir = scanDir + '/Duplicate/'
                if not os.path.exists(DupDir):
                    os.makedirs(DupDir)
                if delete:
                    os.remove(full_file_name) #这里可以直接删除
                else:
                    if not os.path.exists(DupDir + file_name):
                        shutil.move(full_file_name, DupDir)
                print('重复文件：' + full_file_name + ' ------ ' + fileList[file_name])
            else:
                fileList[file_name] = full_file_name
    fileList.clear()
#文件分类
def dealClassify():
    #部分文件变了，重新扫描
    g = os.walk(scanDir)
    for path, dir_list, file_list in g:
        for file_name in file_list:
            full_file_name = os.path.join(path, file_name)
            #处理时长低于3s的视频
            if os.path.splitext(file_name)[-1] == '.MOV':
                print('根据时长分类文件：' + full_file_name)
                info = ffmpeg.probe(full_file_name)
                #print(info)
                duration = info['format']['duration'] #时长
                if float(duration) <= 2:
                    under2Dir = scanDir + '/under2/'
                    if not os.path.exists(under2Dir):
                        print('创建文件夹：' + under2Dir)
                        os.makedirs(under2Dir)
                    if not os.path.exists(under2Dir + file_name):
                        shutil.move(full_file_name, under2Dir)

                elif 2 < float(duration) <= 3:
                    under3Dir = scanDir + '/under3/'
                    if not os.path.exists(under3Dir):
                        print('创建文件夹：' + under3Dir)
                        os.makedirs(under3Dir)
                    if not os.path.exists(under3Dir + file_name):
                        shutil.move(full_file_name, under3Dir)
            #处理HEIC文件
            elif os.path.splitext(file_name)[-1] == '.HEIC':
                heicDir = scanDir + '/HEIC/'
                if not os.path.exists(heicDir):
                    os.makedirs(heicDir)
                if not os.path.exists(heicDir + file_name):
                    shutil.move(full_file_name, heicDir)
            #单独存储json文件
            elif os.path.splitext(file_name)[-1] == '.json':
                jsonDir = scanDir + '/json/'
                if not os.path.exists(jsonDir):
                    os.makedirs(jsonDir)
                if not os.path.exists(jsonDir + file_name):
                    shutil.move(full_file_name, jsonDir)
#计算lat/lng信息
def format_latlng(latlng):
    degree = int(latlng)
    res_degree = latlng - degree
    minute = int(res_degree * 60)
    res_minute = res_degree * 60 - minute
    seconds = round(res_minute * 60.0,3)

    return ((degree, 1), (minute, 1), (int(seconds * 1000), 1000))
#读json
def readJson(json_file):
    with open(json_file, 'r') as load_f:
        return json.load(load_f)
#处理照片exif信息
def dealExif():
    g = os.walk(scanDir)
    for path,dir_list,file_list in g:
        for file_name in file_list:
            full_file_name = os.path.join(path, file_name)
            ext_name = os.path.splitext(file_name)[-1]
            if ext_name.lower() in ['.jpg','.jpeg','.png']:
                # if file_name != 'ee7db1e41afc9fd342e42e0a5034006b.JPG':   #   单文件测试
                #     continue

                if not os.path.exists(scanDir + '/json/' + file_name + '.json'):
                    continue
                exifJson = readJson(scanDir + '/json/' + file_name + '.json')
                print('处理Exif：' + full_file_name)
                try:
                    img = Image.open(full_file_name)  # 读图
                    exif_dict = piexif.load(img.info['exif'])
                except UnidentifiedImageError:
                    print("图片读取失败：" + full_file_name)
                    continue
                except KeyError:
                    print("图片没有exif数据，尝试创建：" + full_file_name)
                    exif_dict = {'0th':{},'Exif': {},'GPS': {}}

                # 修改exif数据
                exif_dict['0th'][piexif.ImageIFD.DateTime] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(
                    int(exifJson['photoTakenTime']['timestamp']))).encode('utf-8')
                exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(
                    int(exifJson['creationTime']['timestamp']))).encode('utf-8')
                exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(
                    int(exifJson['modificationTime']['timestamp']))).encode('utf-8')
                exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = format_latlng(exifJson['geoDataExif']['latitude'])
                exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = format_latlng(exifJson['geoDataExif']['longitude'])
                # exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'W'
                # exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N'
                exif_bytes = piexif.dump(exif_dict)
                img.save(full_file_name, None, exif=exif_bytes)

                #修改文件时间（可选）
                # photoTakenTime = time.strftime("%Y%m%d%H%M.%S", time.localtime(int(exifJson['photoTakenTime']['timestamp'])))
                # os.system('touch -t "{}" "{}"'.format(photoTakenTime, full_file_name))
                # os.system('touch -mt "{}" "{}"'.format(photoTakenTime, full_file_name))

                # print(type(exif_dict), exif_dict)
                # for ifd in ("0th", "Exif", "GPS", "1st"):
                #     print(ifd)
                #     for tag in exif_dict[ifd]:
                #         print(piexif.TAGS[ifd][tag], exif_dict[ifd][tag])
                # exit()


if __name__ == '__main__':
    scanDir = r'/Users/XXX/Downloads/Takeout' #TODO 这里修改归档的解压目录
    dealDuplicate()
    dealClassify()
    dealExif()
    print('终于搞完了，Google Photos 辣鸡')
