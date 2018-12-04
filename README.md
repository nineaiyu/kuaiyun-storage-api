# kuaiyun-storage-api
快云存储，python 接口


存储页面 https://www.kuaiyun.cn/storage/kystorageindex

对象存储5G免费领，每月更有30G流量不限使用！

可以将本地备份的数据自动上传到存储空间


auto_check_refresh_cdn.py
APP分发平台有问题，于是使用阿里云的cdn 进行APP分发，该程序是自己根据 apk 和 ipa 后缀的文件，自动分发到cdn节点上面
需要安装requests ,仅支持python2.7
需要将该脚本放到定时任务里面，每一分钟执行一次
功能：检查匹配文件的mtime时候发生变化，如果变化，继续检查md5是否一致，如果不一致，将最新的数据插入数据库，并调用阿里云cdn的刷新和预热接口
