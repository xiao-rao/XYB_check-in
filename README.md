# XYB_check-in
校友邦 自动签到/签退
# 功能介绍
---
1. 账号密码登陆 无需抓包
2. 支持多账号签到
3. 支持签到，签退
4. 自主实习无需配置地址信息，自动获取
5. 支持windows，macos，Linux，云函数定时任务部署
## 运行环境
python3。6以上
## 使用方式
下载所需的依赖 配置 `user.json`文件的内容 运行 `main.py` 签到执行命令 python main.py --sign_in 签退执行 python main.py --sign_out
### user.json 介绍
```json
{
  "pushPlusToken": "采用pushplus公众号实现推送功能 这里的token是运行脚本人可填的 推送所有账号签到的情况 选填", 
  "user": [
    {
      "username": "账号1",
      "password": "xxxx",
      "pushPlusToken": "签到人的pushplus token  选填 一对一推送",
      "location": {
        "adcode": "城市代码",
        "address": "签到详细地址 集体实习 必填 ",
        "lng": "经度 集体实习 必填",
        "lat": "纬度 集体实习 必填"
      },
      "reason": "签到描述",
      "startDate": "这里设置需要签到的开始时间 必填",
      "endDate": "结束时间 必填"
    },
    {
      "username": "账号2",
      "password": "xxxx",
      "pushPlusToken": "",
      "location": {
        "adcode": "420111",
        "address": "位置1",
        "lng": "经度",
        "lat": "纬度"
      },
      "reason": "签到描述",
      "startDate": "2023-07-05",
      "endDate": "2023-07-31"
    }
  ]
}
```
### linux实现定时任务部署教程
1。 进入服务器 cd到存放的位置 
```shell
git clone https://github.com/xiao-rao/XYB_check-in.git
pip install requests
pip install fake_useragent
```
以上步骤完成代码拉取 下载依赖
接下来配置定时任务
```shell
crontab -e
```
进入编辑定时任务的编辑器
编辑命令 
```shell
0 18 * * * python3 /data/python/main.py --sign_out  ## 签退
0 8 * * * python3 /data/python/main.py --sign_in   ## 签到
```
编辑完成按esc :wq保存退出 或者 ctrl + x 保存 y 退出
0 18 * * * 代码每天下午六点 执行命令 可自行更换时间
python3 /data/python/main.py --sign_out 代码python命令
### 云函数部署
移步至[xiaoyoubangSign](https://github.com/Seelly/xiaoyoubangSign/tree/main)
#### 鸣谢
[xiaoyoubangSign](https://github.com/Seelly/xiaoyoubangSign/tree/main)


