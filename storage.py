#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author : liuyu
# date : 2018/6/26

import requests
import os
import base64
import smtplib
from email.header import Header
from email.mime.text import MIMEText


class kuaiyunstorage(object):

    def __init__(self, voucher, accessKey, secretKey, resource):
        self.voucher = voucher
        self.accessKey = accessKey
        self.secretKey = secretKey
        self.resource = resource
        self.gettokenurl = "http://api.storagesdk.com/restful/storageapi/storage/getToken"
        self.sendfileurl = "http://api.storagesdk.com/restful/storageapi/file/uploadFile"
        self.token = ""

    def gettoken(self):
        data = {
            "voucher": self.voucher,
            "accessKey": self.accessKey,
            "secretKey": self.secretKey,
            "resource": self.resource,
        }
        r = requests.post(self.gettokenurl, json=data, timeout=2.5)
        jsonrequest = r.json()
        if jsonrequest["code"] == 0:
            self.token = (jsonrequest["message"]).split("token:")[1]

    def geturl(self, bucketName, filename):
        url = "http://api.storagesdk.com/restful/storageapi/file/getFileUrl"
        data = {
            "fileName": filename,
            "bucketName": bucketName,
            "resource": self.resource,
            "token": self.token,
        }

        r = requests.post(url, json=data)
        print(r.json())

    def sendfile(self, localfilepath, remotefilepath, bucketName):

        size = os.path.getsize(localfilepath)
        filename = remotefilepath
        headers = {
            "token": self.token,
            "resource": self.resource,
            "bucketName": bucketName,
            "fileName": str(base64.urlsafe_b64encode(bytes(filename, encoding='utf8')), encoding='utf8'),
            "length": str(size),
        }
        with open(localfilepath, 'rb') as files:
            r = requests.post(self.sendfileurl, data=files, headers=headers, timeout=3600)
            return r.json()

    def execupload(self, localfilepath, remotefilepath, bucketName):
        resultsinfo = {
            "code": 1,
            "message": "失败"
        }
        try:
            self.gettoken()
            if self.token != "":
                try:
                    sendresults = self.sendfile(localfilepath, remotefilepath, bucketName)
                    resultsinfo["code"] = sendresults["code"]
                    resultsinfo["message"] = sendresults["message"]
                except:
                    resultsinfo["code"] = 1
                    resultsinfo["message"] = "上传异常"
            else:
                resultsinfo["message"] = "获取token失败"
        except Exception as e:
            resultsinfo["message"] = e
        finally:
            return resultsinfo


class sendmail(object):

    def __init__(self, content, status):
        self.mail_host = "smtp.163.com"  # SMTP服务器
        self.mail_user = "l****@163.com"  # 用户名
        self.mail_pass = "l*****9"  # 授权密码，非登录密码
        self.sender = "l****om"      #发送者
        self.receivers = ['n****@qq.com', self.sender]  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
        self.content = content
        self.title = status + '备份博客发送快云存储结果'  # 邮件主题

    def sendEmail(self):
        message = MIMEText(self.content, 'plain', 'utf-8')  # 内容, 格式, 编码
        message['From'] = "{}".format(self.sender)
        message['To'] = ",".join(self.receivers)
        message['Subject'] = self.title

        try:
            smtpObj = smtplib.SMTP_SSL(self.mail_host, 465)  # 启用SSL发信, 端口一般是465
            smtpObj.login(self.mail_user, self.mail_pass)  # 登录验证
            smtpObj.sendmail(self.sender, self.receivers, message.as_string())  # 发送
            print("mail has been send successfully.")
        except smtplib.SMTPException as e:
            print(e)



if __name__ == "__main__":
    voucher = "632a972***812fce69**43e" # 用户凭证
    accessKey = "MD9****C6W****D"  # 用户云存储accessKey
    secretKey = "Hu***3ljAq4****iOGd"  # 用户云存储secretKey
    resource = "VG3****1wtrN****rfnC"  # 调用来源
    bucketName = "n***-blog"
    status = "失败 "

    kuaiyunobj = kuaiyunstorage(voucher, accessKey, secretKey, resource)
    localfilepath = "/data/minepython/kuaiyunstorage/storage.py"
    remotefilepath = "/kuaiyunstorage/storage.py"
    results = kuaiyunobj.execupload(localfilepath, remotefilepath, bucketName)
    if results["code"] == 0:
        status = '成功'
    mailobj = sendmail(
        status + " " + str(results["message"]) + "  本地文件:" + localfilepath + "  远端文件:" + remotefilepath,status)
    mailobj.sendEmail()
