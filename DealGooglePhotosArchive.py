#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author  : gty0211@foxmail.com
import json
import os
import sys
import shutil
import time
import ffmpeg
import piexif
import hashlib
from PIL import Image, UnidentifiedImageError

#归档zip解压目录
scanDir = ''
outPutDir = ''
HEICNum = JsonNum = PhotoNum = Under2Num = Under3Num = DumpNum = ExifNum = 0
#获取文件MD5
def GetMD5FromFile(filename):
    file_object = open(filename, 'rb')
    file_content = file_object.read()
    file_object.close()
    file_md5 = hashlib.md5(file_content)
    return file_md5.hexdigest()
#处理重复
def dealDuplicate(delete=True):
    fileMD5List = {}
    dg = os.walk(scanDir)
    DupDir = outPutDir + '/Duplicate/'  #重复文件存放文件夹
    if not os.path.exists(DupDir):
        os.makedirs(DupDir)

    for path,dir_list,file_list in dg:
        if path == DupDir:
            print('跳过 '+DupDir+' 文件夹')
            continue;
        for file_name in file_list:
            full_file_name = os.path.join(path, file_name)
            if file_name == '元数据.json':
                continue
            #处理重复文件
            _md5 = GetMD5FromFile(full_file_name)
            if _md5 in fileMD5List.keys() and full_file_name != fileMD5List[_md5]:
                DumpNum += 1
                if delete:
                    os.remove(full_file_name) #这里可以直接删除
                else:
                    if not os.path.exists(DupDir + file_name):
                        shutil.move(full_file_name, DupDir)
                    else: #存在多个就删除
                        os.remove(full_file_name)
                print('重复文件：' + full_file_name + ' ------ ' + fileMD5List[_md5])
            else:
                fileMD5List[_md5] = full_file_name
    fileMD5List.clear()
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
                    Under2Num += 1
                    under2Dir = outPutDir + '/under2/'
                    if not os.path.exists(under2Dir):
                        print('创建文件夹：' + under2Dir)
                        os.makedirs(under2Dir)
                    if not os.path.exists(under2Dir + file_name):
                        shutil.move(full_file_name, under2Dir)

                elif 2 < float(duration) <= 3:
                    Under3Num += 1
                    under3Dir = outPutDir + '/under3/'
                    if not os.path.exists(under3Dir):
                        print('创建文件夹：' + under3Dir)
                        os.makedirs(under3Dir)
                    if not os.path.exists(under3Dir + file_name):
                        shutil.move(full_file_name, under3Dir)
            #处理HEIC文件
            elif os.path.splitext(file_name)[-1] == '.HEIC':
                HEICNum += 1
                heicDir = outPutDir + '/HEIC/'
                if not os.path.exists(heicDir):
                    os.makedirs(heicDir)
                if not os.path.exists(heicDir + file_name):
                    shutil.move(full_file_name, heicDir)
            #单独存储json文件
            elif os.path.splitext(file_name)[-1] == '.json':
                JsonNum += 1
                jsonDir = outPutDir + '/json/'
                if not os.path.exists(jsonDir):
                    os.makedirs(jsonDir)
                if not os.path.exists(jsonDir + file_name):
                    shutil.move(full_file_name, jsonDir)
            #其他文件存储到Photos文件夹
            else:
                PhotoNum += 1
                photosDir = outPutDir + '/Photos/'
                if not os.path.exists(photosDir):
                    os.makedirs(photosDir)
                if not os.path.exists(photosDir + file_name):
                    shutil.move(full_file_name, photosDir)
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
    with open(json_file, 'r',encoding='UTF-8') as load_f:
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

                if not os.path.exists(outPutDir + '/json/' + file_name + '.json'):
                    continue
                exifJson = readJson(outPutDir + '/json/' + file_name + '.json')
                print('处理Exif：' + full_file_name)
                try:
                    img = Image.open(full_file_name)  # 读图
                    exif_dict = piexif.load(img.info['exif'])
                    # 修改exif数据
                    if 'photoTakenTime' in exifJson.keys():
                        exif_dict['0th'][piexif.ImageIFD.DateTime] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(exifJson['photoTakenTime']['timestamp']))).encode('utf-8')
                    if 'creationTime' in exifJson.keys():
                        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(exifJson['creationTime']['timestamp']))).encode('utf-8')
                    if 'photoLastModifiedTime' in exifJson.keys():
                        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(exifJson['photoLastModifiedTime']['timestamp']))).encode('utf-8')
                    if 'geoDataExif' in exifJson.keys():
                        exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = format_latlng(exifJson['geoDataExif']['latitude'])
                        exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = format_latlng(exifJson['geoDataExif']['longitude'])
                    # exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'W'
                    # exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N'
                    exif_bytes = piexif.dump(exif_dict)
                    img.save(full_file_name, None, exif=exif_bytes)
                    ExifNum += 1
                    #修改文件时间（可选）
                    # photoTakenTime = time.strftime("%Y%m%d%H%M.%S", time.localtime(int(exifJson['photoTakenTime']['timestamp'])))
                    # os.system('touch -t "{}" "{}"'.format(photoTakenTime, full_file_name))
                    # os.system('touch -mt "{}" "{}"'.format(photoTakenTime, full_file_name))

                    # print(type(exif_dict), exif_dict)
                    # for ifd in ("0th", "Exif", "GPS", "1st"):
                    #     print(ifd)
                    #     for tag in exif_dict[ifd]:
                    #         print(piexif.TAGS[ifd][tag], exif_dict[ifd][tag])
                except UnidentifiedImageError:
                    print("图片读取失败：" + full_file_name)
                    continue
                except KeyError:
                    print("图片没有exif数据" + full_file_name)
                    continue
                    # exif_dict = {'0th':{},'Exif': {},'GPS': {}}

#check
def check():
    global outPutDir
    if scanDir == r'/Users/XXX/Downloads/Takeout':
        print("\033[31mPlease modify scanDir\033[0m")
        print("\033[31m请修改scanDir变量你的归档解压文件夹路径\033[0m")
        sys.exit()
    if not os.path.exists(scanDir + outPutDir):
        os.makedirs(scanDir + outPutDir)
    else:
        print("\033[31m请先移除路径\033[0m" + " \033[31m" + scanDir + outPutDir +"\033[0m" + " \033[31m避免重复扫描\033[0m" )
        sys.exit()
    outPutDir = scanDir + outPutDir            


if __name__ == '__main__':
    scanDir = r'/Users/XXX/Downloads/Takeout' #TODO 这里修改归档的解压目录
    outPutDir = '/DealGoogleOutput'
    check()
    dealDuplicate()
    dealClassify()
    dealExif()
    
    print("HEIC数量："+HEICNum)
    print("Json数量："+JsonNum)
    print("图片数量："+PhotoNum)
    print("小于2s视频"+Under2Num)
    print("小于3s视频"+Under3Num)
    print("HEIC数量："+HEICNum)
    print("重新文件数量："+DumpNum)
    print("处理Meta数量："+ExifNum)
    print('处理完成，文件输出在：' + outPutDir)
    # print('终于搞完了，Google Photos 辣鸡')
