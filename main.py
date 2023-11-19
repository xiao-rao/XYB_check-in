# -*- coding: utf-8 -*-
import argparse
import hashlib
import json
import random
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests
from fake_useragent import UserAgent

ua = UserAgent()
msg = []

urls = {
    'login': 'https://xcx.xybsyw.com/login/login.action',
    'loadAccount': 'https://xcx.xybsyw.com/account/LoadAccountInfo.action',
    'ip': 'https://xcx.xybsyw.com/behavior/Duration!getIp.action',
    'trainId': 'https://xcx.xybsyw.com/student/clock/GetPlan!getDefault.action',
    'sign': 'https://app.xybsyw.com/behavior/Duration.action',
    'autoSign': 'https://xcx.xybsyw.com/student/clock/Post!autoClock.action',
    'newSign': 'https://xcx.xybsyw.com/student/clock/PostNew.action',
    # 'updateSign': 'https://xcx.xybsyw.com/student/clock/PostNew!updateClock.action',
    'updateSign': 'https://xcx.xybsyw.com/student/clock/Post!updateClock.action',
    'status': 'https://xcx.xybsyw.com/student/clock/GetPlan!detail.action'
}

host = 'xcx.xybsyw.com'


def getTimeStr():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M:%S")


def str2md5(str):
    return hashlib.md5(str.encode(encoding='UTF-8')).hexdigest()


def sign_header(data: dict, noce=None, now_time: int = None) -> dict:
    """
    请求签名
    :param data: 请求体数据
    :param noce: 随机数列表(下标不能超过密码本长度)
    :param now_time: 时间戳
    :return: 签名用Headers
    """
    re_punctuation = re.compile("[`~!@#$%^&*()+=|{}':;',\\[\\].<>/?~！@#￥%……&*（）——+|{}【】‘；：”“’。，、？]")
    cookbook = ["5", "b", "f", "A", "J", "Q", "g", "a", "l", "p", "s", "q", "H", "4", "L", "Q", "g", "1", "6", "Q",
                "Z", "v", "w", "b", "c", "e", "2", "2", "m", "l", "E", "g", "G", "H", "I", "r", "o", "s", "d", "5",
                "7", "x", "t", "J", "S", "T", "F", "v", "w", "4", "8", "9", "0", "K", "E", "3", "4", "0", "m", "r",
                "i", "n"]
    except_key = ["content", "deviceName", "keyWord", "blogBody", "blogTitle", "getType", "responsibilities",
                  "street", "text", "reason", "searchvalue", "key", "answers", "leaveReason", "personRemark",
                  "selfAppraisal", "imgUrl", "wxname", "deviceId", "avatarTempPath", "file", "file", "model",
                  "brand", "system", "deviceId", "platform"]
    noce = noce if noce else [random.randint(0, len(cookbook) - 1) for _ in range(20)]
    now_time = now_time if now_time else int(time.time())
    sorted_data = dict(sorted(data.items(), key=lambda x: x[0]))

    sign_str = ""
    for k, v in sorted_data.items():
        v = str(v)
        if k not in except_key and not re.search(re_punctuation, v):
            sign_str += str(v)
    sign_str += str(now_time)
    sign_str += "".join([cookbook[i] for i in noce])
    sign_str = re.sub(r'\s+', "", sign_str)
    sign_str = re.sub(r'\n+', "", sign_str)
    sign_str = re.sub(r'\r+', "", sign_str)
    sign_str = sign_str.replace("<", "")
    sign_str = sign_str.replace(">", "")
    sign_str = sign_str.replace("&", "")
    sign_str = sign_str.replace("-", "")
    sign_str = re.sub(f'\uD83C[\uDF00-\uDFFF]|\uD83D[\uDC00-\uDE4F]', "", sign_str)
    sign_str = quote(sign_str)
    sign = hashlib.md5(sign_str.encode('ascii'))

    return {
        "n": ",".join(except_key),
        "t": str(now_time),
        "s": "_".join([str(i) for i in noce]),
        "m": sign.hexdigest(),
        "v": "1.6.36"
    }


def log(content):
    print(getTimeStr() + ' ' + str(content))
    sys.stdout.flush()


# 获取Header
def getHeader(host):
    headers = {
        'user-agent': ua.random,
        'content-type': 'application/x-www-form-urlencoded',
        'host': host,
        'Connection': 'keep-alive',
        "Accept-Encoding": "gzip, deflate"
    }
    return headers


# 获取账号和密码
def getuser(userInfo):
    data = {
        'username': userInfo['username'],
        'password': str2md5(userInfo['password'])
    }
    return data


# 登录获取sessionId和loginerId
def login(userInfo):
    data = getuser(userInfo)
    headers = getHeader(host)
    url = urls['login']
    resp = requests.post(url=url, headers=headers, data=data).json()
    if '200' == resp['code']:
        sessionId = resp['data']['sessionId']
        loginerId = resp['data']['loginerId']
        log(f"sessionId:{sessionId}")
        log(f"loginerId:{loginerId}")
        return sessionId, loginerId
    else:
        log(resp['msg'])
        pushMessge(userInfo['pushPlusToken'], resp['msg'])
        msg.append(f'账号 {userInfo["username"]}  {resp["msg"]}.')
        return False, False


# 获取trainID
def getTrainID(sessionId):
    headers = getHeader(host)
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls['trainId']
    resp = requests.post(url=url, headers=headers).json()
    if '200' == resp['code']:
        clockVo = resp['data'].get('clockVo')
        if not clockVo:
            log("该账号实习已结束！！")
            return False, False
        ret = clockVo['traineeId']
        moduleName = clockVo['moduleName']
        log(f'traineeId:{ret}')
        log(f'moduleName:{moduleName}')
        return ret, moduleName
    else:
        log(resp['msg'])
        return False, False


# 获取姓名
def getUsername(sessionId):
    headers = getHeader(host)
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls['loadAccount']
    resp = requests.post(url=url, headers=headers).json()
    if '200' == resp['code']:
        ret = resp['data']['loginer']
        log(f"姓名:{ret}")
        return ret
    else:
        log(resp['msg'])


# 获取ip
def getIP(sessionId):
    headers = getHeader(host)
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls['ip']
    resp = requests.post(url=url, headers=headers).json()
    if '200' == resp['code']:
        ret = resp['data']['ip']
        log(f'ip:{ret}')
        return ret
    else:
        log(resp['msg'])


# 获取经纬度\签到地址
def getPosition(sessionId, trainId):
    headers = getHeader(host)
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls['status']
    data = {
        'traineeId': trainId
    }
    resp = requests.post(url=url, headers=headers, data=data).json()
    # print(resp)
    if '200' == resp['code']:
        postInfo = resp['data']['postInfo']
        address = postInfo['address']
        lat = postInfo['lat']
        lng = postInfo['lng']
        log(f'经度:{lng}|纬度:{lat}')
        log(f'签到地址:{address}')
        return address, lng, lat
    else:
        log(resp['msg'])


# 执行签到
def autoSign(sessionId, data, signHeader):
    headers = getHeader(host)
    headers.update(signHeader)
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls['autoSign']
    resp = requests.post(url=url, headers=headers, data=data).json()
    print(resp)
    log(resp['msg'])
    return resp['msg']


# 签退
def newSign(sessionId, data, signHeader):
    headers = getHeader(host)
    headers.update(signHeader)
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls['newSign']
    resp = requests.post(url=url, headers=headers, data=data).json()
    print(resp)
    return resp['msg']


# 更新签到记录
def updateSign(sessionId, data, signHeader):
    headers = getHeader(host)
    headers.update(signHeader)
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls['updateSign']
    resp = requests.post(url=url, headers=headers, data=data).json()
    print(resp)
    log(resp['msg'])
    return resp['msg']


# 获取签到状态
def getSignStatus(sessionId, trainId):
    headers = getHeader(host)
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls['status']
    data = {'traineeId': trainId}
    resp = requests.post(url=url, headers=headers, data=data).json()
    is_sign_in = bool(resp["data"]["clockInfo"]["inTime"])
    is_sign_out = bool(resp["data"]["clockInfo"]["outTime"])
    return is_sign_in, is_sign_out


def signHandler(userInfo, sence):
    sessionId, loginerId = login(user)
    if not sessionId or not loginerId:
        return
    train_id, moduleName = getTrainID(sessionId)
    if not train_id or not moduleName:
        return
    address, lng, lat = getPosition(sessionId, train_id)
    # if "集中" in moduleName:
    #     lng = userInfo['location']['lng']
    #     lat = userInfo['location']['lat']
    #     address = userInfo['location']['address']
    signFormData = {
        'traineeId': train_id,
        'adcode': userInfo['location']['adcode'],
        'lat': lat,
        'lng': lng,
        'address': address,
        'deviceName': 'microsoft',
        'punchInStatus': '1',
        'clockStatus': sence,
        'imgUrl': '',
        'reason': userInfo['reason'],
    }
    # print(signFormData)
    is_sign_in, is_sign_out = getSignStatus(sessionId, train_id)
    if sence == 2:
        if is_sign_in:
            log_msg = updateSign(sessionId, signFormData, sign_header(signFormData))
            log("已经进行过签到，本次操作将更新打卡时间...")
            pushMessge(userInfo['pushPlusToken'], f'已经进行过签到，本次操作将更新打卡时间...\n{log_msg}')
            msg.append(f'账号 {userInfo["username"]} 已经进行过签到，本次操作将更新打卡时间...\n{log_msg}')
        elif is_sign_out:
            log('已签退，无法进行签到!')
            pushMessge(userInfo['pushPlusToken'], '已签退，无法进行签到! ')
            msg.append(f'账号 {userInfo["username"]} 已签退，无法进行签到!')
        else:
            log("签到完成！...")
            log_msg = newSign(sessionId, signFormData, sign_header(signFormData))
            pushMessge(userInfo['pushPlusToken'], f'签到完成！！\n{log_msg}')
            msg.append(f'账号 {userInfo["username"]} 签到完成 \n{log_msg}')
    else:
        if is_sign_in:
            if is_sign_out:
                log("已经进行过签退，本次操作未进行...")
                pushMessge(userInfo['pushPlusToken'], "已经进行过签退，本次操作未进行...")
                msg.append(f'账号 {userInfo["username"]} 已经进行过签退，本次操作未进行...')
            else:
                log_msg = newSign(sessionId, signFormData, sign_header(signFormData))
                log("签退完成！！")
                pushMessge(userInfo['pushPlusToken'], f'签退完成！！\n{log_msg}')
                msg.append(f'账号 {userInfo["username"]} 签退完成 \n{log_msg}')
        else:
            log("无法进行签退，必须先进行签到操作")
            pushMessge(userInfo['pushPlusToken'], '无法进行签退，必须先进行签到操作')
            msg.append(f'账号 {userInfo["username"]} 无法进行签退，必须先进行签到操作')


# 推送消息
def pushMessge(token, message):
    hea = {
        "Content-Type": "application/json; charset=UTF-8",
    }
    url = "http://www.pushplus.plus/send"
    requestData = {
        "token": token,
        "title": "校友邦通知",
        "content": message
    }
    result = requests.post(url, headers=hea, data=json.dumps(requestData)).json()
    log(result)


# 读取user.json
def readJsonInfo():
    with open('user.json', 'r', encoding='utf8') as fp:
        users = json.load(fp)
    fp.close()
    return users


# 腾讯云函数使用
def main_handler(event, context):
    sence = 2 if event['Message'] == 'sign_in' else 1
    users = readJsonInfo()
    for user in users['user']:
        log(f"执行 {user['username']} 签到/签退任务")
        now = str(datetime.today().date())
        start = user['startDate']
        end = user['endDate']
        if start >= now >= end:
            log(f"账号 {user['username']} 未到签到开始时间或服务已到期")
            pushMessge(user['pushPlusToken'], '未到签到开始时间或服务已到期！！')
            msg.append(f"账号 {user['username']} 未到签到开始时间或服务已到期")
            continue
        signHandler(user, sence)
        time.sleep(1.5)
    pushMessge(users['pushPlusToken'], str(msg))
    log("执行结束")


if __name__ == '__main__':
    users = readJsonInfo()
    # 创建解析器对象
    parser = argparse.ArgumentParser()
    # 添加命令行参数
    parser.add_argument("--sign_in", action="store_true", help="执行签到函数")
    parser.add_argument("--sign_out", action="store_true", help="执行签退函数")
    # 解析命令行参数
    args = parser.parse_args()
    if args.sign_in:
        sence = 2
    elif args.sign_out:
        sence = 1
    else:
        sence = 2
        log("输入命令有误！")
        # exit(-1)
    for user in users['user']:
        log(f"执行 {user['username']} 签到/签退任务")
        now = str(datetime.today().date())
        start = user['startDate']
        end = user['endDate']
        if start >= now >= end:
            log(f"账号 {user['username']} 未到签到开始时间或服务已到期")
            pushMessge(user['pushPlusToken'], '未到签到开始时间或服务已到期！！')
            msg.append(f"账号 {user['username']} 未到签到开始时间或服务已到期")
            continue
        signHandler(user, sence)
        time.sleep(1.5)
    pushMessge(users['pushPlusToken'], str(msg))
    log("执行结束")
