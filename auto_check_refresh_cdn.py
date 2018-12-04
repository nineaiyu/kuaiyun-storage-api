#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author : liuyu
# date : 2018/11/29 0029

import hmac
from hashlib import sha1
import uuid
import requests
import base64
import sys, urllib
import os, sqlite3, time
import hashlib
import logging

#  控制台输出
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
log_path = os.path.dirname(os.path.abspath(__file__))
log_name = os.path.join(log_path, 'check_app_up.log')
fh = logging.FileHandler(log_name, mode='a')
fh.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)


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


def getmtime(file_path):
    return str(os.stat(file_path).st_mtime)


class AliyunCdn(object):

    def __init__(self, access_key_id, access_key_secret, cdn_server_address):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.cdn_server_address = cdn_server_address

    def percent_encode(self, str):
        coding=sys.stdin.encoding
        if not coding:
            coding=sys.getdefaultencoding()
            if not coding:
                coding='UTF-8'
        #res = urllib.quote(str.decode(sys.stdin.encoding).encode('utf8'), '')
        res = urllib.quote(str.decode(coding).encode('utf8'), '')
        res = res.replace('+', '%20')
        res = res.replace('*', '%2A')
        res = res.replace('%7E', '~')
        return res

    def compute_signature(self, parameters, access_key_secret):
        sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])

        canonicalizedQueryString = ''
        for (k, v) in sortedParameters:
            canonicalizedQueryString += '&' + self.percent_encode(k) + '=' + self.percent_encode(v)

        stringToSign = 'GET&%2F&' + self.percent_encode(canonicalizedQueryString[1:])

        h = hmac.new(access_key_secret + "&", stringToSign, sha1)
        signature = base64.encodestring(h.digest()).strip()
        return signature

    def compose_url(self, user_params):
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        parameters = { \
            'Format': 'JSON', \
            'Version': '2014-11-11', \
            'AccessKeyId': self.access_key_id, \
            'SignatureVersion': '1.0', \
            'SignatureMethod': 'HMAC-SHA1', \
            'SignatureNonce': str(uuid.uuid1()), \
            'TimeStamp': timestamp, \
            }

        for key in user_params.keys():
            parameters[key] = user_params[key]

        signature = self.compute_signature(parameters, self.access_key_secret)
        parameters['Signature'] = signature
        url = self.cdn_server_address + "/?" + urllib.urlencode(parameters)
        return url

    def make_request(self, user_params):
        url = self.compose_url(user_params)
        return url

    def run(self, action, objectpath):
        #return action
        url = self.make_request({'Action': action, 'ObjectPath': objectpath})
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36',
        }
        res = requests.get(url, headers=headers)
        return res.json()


class setsqlite(object):

    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.dbfile = 'appfiles.db'
        self.ceatedatabase()

    def removedb(self):
        try:
            time.sleep(1)
            os.unlink(os.path.join(self.BASE_DIR, self.dbfile))
            self.ceatedatabase()
        except Exception as e:
            logging.error(e)

    def ceatedatabase(self):
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, self.dbfile))
        c = conn.cursor()
        try:
            c.execute(
                '''CREATE TABLE files(FILENAME CHAR(1000) PRIMARY KEY NOT NULL,md5 CHAR(100) NOT NULL,mtime CHAR(100) NOT NULL  )''')
        except Exception as e:
            logging.warning(e)
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
            logging.error(e)
        conn.commit()
        conn.close()

    def add(self, filelists):
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, self.dbfile))
        c = conn.cursor()
        for files in filelists:
            try:
                filename = files['filename']
                md5 = files['md5']
                mtime = files['mtime']
                c.execute("INSERT INTO files(FILENAME, md5,mtime) VALUES(?,?,?)", (filename, md5, mtime))
            except Exception as e:
                logging.error(e)
        conn.commit()
        conn.close()

    def update(self, filelists):
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, self.dbfile))
        c = conn.cursor()
        for files in filelists:
            try:
                filename = files['filename']
                md5 = files['md5']
                mtime = files['mtime']
                c.execute("UPDATE files SET md5=?,mtime=? where FILENAME =?", (md5, mtime, filename))
            except Exception as e:
                logging.error(e)
        conn.commit()
        conn.close()

    def query(self, filename):
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, self.dbfile))
        c = conn.cursor()
        filelists = []
        try:
            cursor = c.execute("SELECT * FROM files where FILENAME = ?", (filename,))
            for row in cursor:
                filelists.append({
                    'filename': row[0],
                    'md5': row[1],
                    'mtime': row[2]
                })
        except Exception as e:
            logging.info(e)
        conn.close()
        return filelists

    def queryall(self):
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, self.dbfile))
        c = conn.cursor()
        filelists = []
        try:
            cursor = c.execute("SELECT * FROM files")
            for row in cursor:
                filelists.append({
                    'filename': row[0],
                    'md5': row[1],
                    'mtime': row[2]
                })
        except Exception as e:
            logging.error(e)
        conn.close()
        return filelists


def deletefromsql(filenamelists, sqlobj):
    sqllists = sqlobj.queryall()
    formatsqllist = []
    for sqlkv in sqllists:
        formatsqllist.append(sqlkv.get("filename"))
    insqlists = set(formatsqllist) - set(filenamelists)
    delfilelists = []
    for filename in insqlists:
        delfilelists.append(filename)
        logging.info("filename:{}\tmessage:{}".format(filename, 'sql is exists but local is not exists,so delete:'))
    sqlobj.delete(delfilelists)


def check_contain_chinese(check_str):
    for ch in check_str.decode('utf-8'):
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def setpids():
    lockfile = os.path.join("/var/run/","{}.run".format(__file__))
    lid = open(lockfile,'wb')
    lid.close()

def getpids():
    lockfile = os.path.join("/var/run/","{}.run".format(__file__))
    state=os.path.exists(lockfile)
    if state:
        mtime = getmtime(lockfile)
        now_time = float(time.time())  # 现在的秒
        now_time_mtime = now_time - float(mtime)
        if int(str(now_time_mtime).split(".")[0]) > 3600*3:
            os.unlink(lockfile)
            return False
        return True
    return False

def delpids():
    lockfile = os.path.join("/var/run/","{}.run".format(__file__))
    state=os.path.exists(lockfile)
    if state:
        os.unlink(lockfile)

if __name__ == "__main__":
    # logging.info("=============================================start============================================")
    if getpids():
        logging.info("check programe is running so skip...")
        exit(0)
    setpids()
    dirname = "/data/data/down/down/"
    hehedomain = "http://cdn.hehedomain.com"
    access_key_id = 'access_key_id '
    access_key_secret = 'access_key_secret '
    cdn_server_address = 'https://cdn.aliyuncs.com'
    timelimit = 40  # 秒 ，就是上次的文件的修改时间和现有时间超过的限制时间
    cndfreshlimit = 20  # 秒，就是 cdn URL刷新和预热的时间间隔
    appoperatelimit = 80  # 秒，操作等待时间，如果间隔太小，会导致预热失败率提高
    allowfilefilter = [".ipa", ".apk"]
    citylists=[]
    try:
        citylists = os.listdir(dirname)
    except Exception as e:
        logging.error(e)

    backpathlists = []
    filenamelists = []
    for cityname in citylists:
        backpathlists.append(os.path.join(dirname, cityname))
    ##处理目录下面的所有文件
    for backpath in backpathlists:
        for fpathe, dirs, fs in os.walk(backpath):
            for f in fs:
                for ff in allowfilefilter:
                    if f.split(ff)[-1] == "":
                        filefull = os.path.join(fpathe, f)
                        if check_contain_chinese(filefull):
                            logging.debug("filename:{} \tmessage:{}".format(filefull,"is chiness ,skip ..."))
                            continue
                        logging.debug("filename:{} \tmessage:{}".format(filefull, "Qualified, join the queue"))
                        filenamelists.append(filefull)

    sqlobj = setsqlite()
    cdnobj = AliyunCdn(access_key_id, access_key_secret, cdn_server_address)

    ### 检查本地和数据库信息是否一致，以本地数据为主
    deletefromsql(filenamelists, sqlobj)
    ##与数据库进行比较
    ## 先对比 mtime ,不同则比较 md5
    flag = True
    for filename in filenamelists:
        now_mtime = getmtime(filename)
        sqlinfolist = sqlobj.query(filename)
        if len(sqlinfolist) == 1:
            sqlinfo = sqlinfolist[0]
            if str(now_mtime) == str(sqlinfo.get("mtime")):
                pass
            else:
                now_md5 = getmtime(filename)
                if now_md5 == sqlinfo.get("md5"):
                    pass
                else:
                    now_time = float(time.time())  # 现在的秒
                    now_time_mtime = now_time - float(now_mtime)
                    flag = False
                    if int(str(now_time_mtime).split(".")[0]) > int(timelimit):
                        logging.info("filename:{}\tmessage:{}".format(filename,
                                                                      'this app is updated , now  start save sqlinfo and refresh and push to cdn nodes'))
                        sqlobj.update([{
                            'filename': filename,
                            'md5': now_md5,
                            'mtime': now_mtime
                        }])

                        appurl = os.path.join(hehedomain, "/".join(filename.split("/")[4:]))
                        req = cdnobj.run("RefreshObjectCaches", appurl)
                        logging.info("RefreshObjectCaches url:{}\tmessage:{}".format(appurl, req))
                        time.sleep(cndfreshlimit)
                        req2 = cdnobj.run("PushObjectCache", appurl)
                        logging.info("PushObjectCache url:{}\tmessage:{}".format(appurl, req2))
                        time.sleep(appoperatelimit)

                    else:
                        logging.info("filename:{}\tmessage:{}".format(filename, 'this app is updating...'))
        elif len(sqlinfolist) == 0:
            # sql 查询失败，可以判断sql不存在该信息。需要进行添加并更新数据库和cdn
            logging.info("filename:{}\tmessage:{}".format(filename,
                                                          'this app is new , now  start save sqlinfo and refresh and push to cdn nodes'))

            md5 = getfilemd5(filename)
            mtime = getmtime(filename)
            fileinfos = {
                'filename': filename,
                'md5': md5,
                'mtime': mtime
            }
            sqlobj.add([fileinfos])
            flag = False

            appurl = os.path.join(hehedomain, "/".join(filename.split("/")[4:]))
            req = cdnobj.run("RefreshObjectCaches", appurl)
            logging.info("RefreshObjectCaches url:{}\tmessage:{}".format(appurl, req))
            time.sleep(cndfreshlimit)
            req2 = cdnobj.run("PushObjectCache", appurl)
            logging.info("PushObjectCache url:{}\tmessage:{}".format(appurl, req2))
            time.sleep(appoperatelimit)
        else:
            logging.error("error!!! {}".format(str(sqlinfolist)))

    if flag:
        logging.info("all app not update,wait next check...")
# logging.info("=============================================end============================================")
    delpids()

