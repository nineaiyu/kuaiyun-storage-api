# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : liuyu
# date : 2018/6/26

import requests
import sqlite3
import os, time
import base64
import smtplib
from email.header import Header
from email.mime.text import MIMEText

import os, sqlite3,time
import hashlib

def getfilemd5(file_path):
    f = open(file_path, 'rb')
    md5_obj = hashlib.md5()
    while True:
        d = f.read(8096)
        if not d:
            break
        md5_obj.update(d)
    hash_code = md5_obj.hexdigest()
    f.close()
    md5 = str(hash_code).lower()
    return md5





class kuaiyunstorage(object):

    def __init__(self, voucher, accessKey, secretKey, resource):
        self.voucher = voucher
        self.accessKey = accessKey
        self.secretKey = secretKey
        self.resource = resource
        self.gettokenurl = "http://api.storagesdk.com/restful/storageapi/storage/getToken"
        self.sendfileurl = "http://api.storagesdk.com/restful/storageapi/file/uploadFile"
        self.deletefileurl = "http://api.storagesdk.com/restful/storageapi/file/deleteFile"
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

    def deletefile(self, bucketName, filename):
        self.gettoken()
        data = {
            "fileName": filename.lower(),
            "bucketName": bucketName,
            "resource": self.resource,
            "token": self.token,
        }
        r = requests.post(self.deletefileurl, json=data, timeout=2.5)
        return r.json()

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
        self.mail_user = "username@163.com"  # 用户名
        self.mail_pass = "password"  # 授权密码，非登录密码
        self.sender = "username@163.com"
        self.receivers = ['username@qq.com', self.sender]  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
        self.content = content
        self.title = status + '博客自动备份发送快云存储结果'  # 邮件主题

    def sendEmail(self):
        message = MIMEText(self.content, 'plain', 'utf-8')  # 内容, 格式, 编码
        message['From'] = "{}".format(self.sender)
        message['To'] = ",".join(self.receivers)
        message['Subject'] = self.title

        try:
            smtpObj = smtplib.SMTP_SSL(self.mail_host, 465)  # 启用SSL发信, 端口一般是465
            smtpObj.login(self.mail_user, self.mail_pass)  # 登录验证
            smtpObj.sendmail(self.sender, self.receivers, message.as_string())  # 发送
            #print("mail has been send successfully.")
        except smtplib.SMTPException as e:
            print(e)

    def send_email2(self, SMTP_host, from_account, from_passwd, to_account, subject, content):
        email_client = smtplib.SMTP(SMTP_host)
        email_client.login(from_account, from_passwd)
        # create msg
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')  # subject
        msg['From'] = from_account
        msg['To'] = to_account
        email_client.sendmail(from_account, to_account, msg.as_string())
        email_client.quit()




class setsqlite(object):

    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.dbfile = 'backfiles.db'
        self.ceatedatabase()

    def ceatedatabase(self):
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, self.dbfile))
        c = conn.cursor()
        try:
            c.execute('''CREATE TABLE files(FILENAME CHAR(1000) PRIMARY KEY NOT NULL,md5 CHAR(100) NOT NULL )''')
        except :
            os.path
        conn.commit()
        conn.close()

    def delete(self, filelists):
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, self.dbfile))
        c = conn.cursor()
        try:
            for files in filelists:
                filename = files
                c.execute("DELETE from files where FILENAME='%s';" % (filename))
        except Exception as e:
            print(e)
        conn.commit()
        conn.close()

    def add(self, filelists):
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, self.dbfile))
        c = conn.cursor()
        for files in filelists:
            try:
                    filename = files['filename']
                    md5 = files['md5']
                    c.execute("INSERT INTO files(FILENAME, md5) VALUES(?,?)", (filename, md5))
            except Exception as e:
                print(e)
        conn.commit()
        conn.close()

    def query(self):
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, self.dbfile))
        c = conn.cursor()
        filelists = []
        try:
            cursor = c.execute("SELECT * FROM files")
            for row in cursor:
                filelists.append(os.path.join(row[0],row[1]))
        except Exception as e:
            print(e)
        conn.close()
        return filelists


def rsyncfile(sqlfilelists,filenamelists):
    sqlobj = setsqlite()

    #在 sqlfilelists ，但是不在filenamelists,需要删除sql和网盘数据
    insqlists=set(sqlfilelists)-set(filenamelists)
    delfilelists = []
    for insql in insqlists:
        filename=os.path.dirname(insql)
        delfilelists.append(filename)
        print('delete:',filename)
    sqlobj.delete(delfilelists)

    # 在 本地存储 ，需要更新sql和网盘数据
    filelists = []
    filefulllists = []
    inlocal = set(filenamelists) - set(sqlfilelists)
    for insql in inlocal:
        md5=os.path.basename(insql)
        filefull=os.path.dirname(insql)
        files = {}
        files['filename'] = filefull
        files['md5'] = md5
        filelists.append(files)
        filefulllists.append(filefull)
        print('upload:',filefull)
    sqlobj.add(filelists)

    return delfilelists,filefulllists




if __name__ == "__main__":
    voucher = "632UtrNN8Va9f0dcb9UtrNN8V3IUtrNN8VuTluAfba"  # 用户凭证
    accessKey = "MD9JJ1O0UtrNUtrNUtrNN8VUtrNN8VN8VN9FC6WD"  # 用户云存储accessKey
    secretKey = "e0uol+PS70H5qarfnCjAq4iO3IuTluA6/1qX/IIGd"  # 用户云存储secretKey
    resource = "VG3OQ81wtrNN8V99KqUtrNN8VUtrNN8VJIuTluAKme"  # 调用来源
    bucketName = "username-blog"    #空间名称
    status = "失败 "
    dcode = 0
    acode=0
    kuaiyunobj = kuaiyunstorage(voucher, accessKey, secretKey, resource)

    ##处理需要备份的目录下面的所有文件
    filenamelists = []
    backpathlists = ["/www/backup/database/","/www/backup/site/"]
    for backpath in backpathlists:
        for fpathe, dirs, fs in os.walk(backpath):
            for f in fs:
                filefull = os.path.join(fpathe, f)
                md5 = getfilemd5(filefull)
                filenamelists.append(os.path.join(filefull, md5))


    ##与数据库进行比较
    sqlobj = setsqlite()
    sqlfilelists = sqlobj.query()
    delfilelists, addfilelists=rsyncfile(sqlfilelists, filenamelists)



    for backfile in addfilelists:
        localfilepath = backfile
        remotefilepath = backfile
        results = kuaiyunobj.execupload(localfilepath, remotefilepath, bucketName)
        acode = acode + results["code"]

    if acode == 0:
        for backfile in delfilelists:
            while backfile.startswith('/'):
                backfile=backfile[1:]
            results = kuaiyunobj.deletefile(bucketName, backfile)
            dcode = dcode + results["code"]
    if dcode == 0 and acode == 0:
        status = '上传删除成功'
    elif acode == 0 and dcode != 0:
        status='上传成功，删除失败'
    else:
        status='上传失败'
    mailobj = sendmail(
        status + " " + "  上传文件:" + str(addfilelists) + "  删除文件:" + str(delfilelists), status)

    mailobj.sendEmail()
