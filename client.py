import os
import numpy
from PIL import Image
import requests
import urllib.request
from http import HTTPStatus
from datetime import datetime
import json
from log import logger
import time
import gradio as gr
from oss_utils import ossService
import threading

API_KEY = os.getenv("API_KEY_MIMO")
URL_SERVICE = os.getenv("API_MIMO_URL")
MODEL_NAME = os.getenv("API_MIMO_MODEL_NAME")

oss_service = ossService()

def call_service(input_image_url, template_name, uuid, request_id, mode='fast'):
    # task_id = '5a12afdc-327e-4f0f-9766-eadf4f245ce5'
    # task_id = 'c023cdae-5e67-4d7f-86f6-fab3db208a2a'
    # task_id = '3d29560d-7aed-45e5-9e3e-0dba95d6356a'
    # return task_id

    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-DataInspection": "enable",
    }
    data = {
        "model": MODEL_NAME,
        "input": {
            "image_url": input_image_url,
        },
        "parameters": {
            "template_name": template_name,
            "user_id": uuid,
            "log_path": request_id,
            "mode": mode,
        }
    }
    url_create_task = URL_SERVICE
    print('url_create_task:', url_create_task)
    print('request data:', data)
    try:
        res_ = requests.post(url_create_task, data=json.dumps(data), headers=headers, timeout=60)
    except requests.Timeout:
        # back off and retry
        raise gr.Error("网络波动，请求失败，请再次尝试")

    respose_code = res_.status_code
    if 200 == respose_code:
        res = json.loads(res_.content.decode())
        request_id = res['request_id']
        task_id = res['output']['task_id']
        print(f"task_id: {task_id}: Create MIMO request success. Params: {data}")
        logger.info(f"task_id: {task_id}: Create MIMO request success. Params: {data}")
        return task_id
    else:
        logger.error(f'Fail to create MIMO task: {res_.content}')
        raise gr.Error(f"Fail to create MIMO task: {res_.content}")


def query_async(task_id, request_id):
    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-DataInspection": "enable",
    }
    url_query = f'https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}'
    logger.info(f"task_id: {task_id}: Querying.")
    try:
        res_ = requests.post(url_query, headers=headers, timeout=20)
    except requests.Timeout:
        # back off and retry
        raise gr.Error("网络波动，请求失败，请再次尝试")
    respose_code = res_.status_code
    res = json.loads(res_.content.decode())
    if 200 == respose_code:
        if "SUCCEEDED" == res['output']['task_status']:
            print(
                f"request_id: {request_id}, task_id: {task_id}, query success, result: {res}")
            logger.info(
                f"request_id: {request_id}, task_id: {task_id}, query success, result: {res}")
            return "SUCCESS", res
        elif "RUNNING" == res['output']['task_status']:
            # print(
            #     f"request_id: {request_id}, task_id: {task_id}, query success, result: running...")
            logger.info(
                f"request_id: {request_id}, task_id: {task_id}, query success, result: running..., {res}")

            return "RUNNING", res
        elif "PENDING" == res['output']['task_status']:
            logger.info(
                f"request_id: {request_id}, task_id: {task_id}, query success, result: pending..., {res}")
            return "PENDING", res
        elif "FAILED" == res['output']['task_status']:
            print(
                f"request_id: {request_id}, task_id: {task_id}, query success, result: failed...")
            logger.info(
                f"request_id: {request_id}, task_id: {task_id}, query success, result: failed...")
            return "FAILED", res
        elif "UNKNOWN" == res['output']['task_status']:
            print(
                f"request_id: {request_id}, task_id: {task_id}, query success, result: unknown task...")
            logger.info(
                f"request_id: {request_id}, task_id: {task_id}, query success, result: unknown task...")
            return "UNKNOWN", res
        else:
            print(
                f"request_id: {request_id}, task_id: {task_id}, query failed, result: {res}")
            logger.info(
                f"request_id: {request_id}, task_id: {task_id}, query failed, result: {res}")
            return "FAILED", res
    else:
        print(f'request_id: {request_id}, task_id: {task_id}: Fail to query task result: {res_.content}')
        logger.info(f'request_id: {request_id}, task_id: {task_id}: Fail to query task result: {res_.content}')
        return "FAILED", res

def query_async_sim(task_id):
    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-DataInspection": "enable",
    }
    url_query = f'https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}'
    logger.info(f"task_id: {task_id}: Querying.")
    try:
        res_ = requests.post(url_query, headers=headers, timeout=20)
    except requests.Timeout:
        # back off and retry
        raise gr.Error("网络波动，请求失败，请再次尝试")
    respose_code = res_.status_code
    res = json.loads(res_.content.decode())
    if 200 == respose_code:
        return res['output']['task_status']
    else:
        return "FAILED"

def convert_oss_url_to_oss_path(oss_url):
    # oss_url: eg: 'https://vigen-invi.oss-cn-shanghai.aliyuncs.com/service_dashscope/Mimo/2024-11-29/test_local_user/20241129-150204-154590-IPGQPZ/result-3b3c754e-85d0-4997-8dc0-09e30227c18b.mp4?OSSAccessKeyId=LTAI5t7aiMEUzu1F2xPMCdFj&Expires=1732868743&Signature=tVrs0%2BthUPcxhy3FdBuDUYh%2FmTg%3D'
    # oss_path: eg: 'service_dashscope/Mimo/2024-11-29/test_local_user/20241129-150204-154590-IPGQPZ/result-3b3c754e-85d0-4997-8dc0-09e30227c18b.mp4'
    oss_path = oss_url.replace('http://', 'https://')
    oss_path = oss_path.replace('https://vigen-invi.oss-cn-shanghai.aliyuncs.com/', '')
    oss_path = oss_path.split('?')[0]
    oss_path = 'oss://' + oss_service.BucketName + '/' + oss_path
    # print('oss_path:', oss_path)
    return oss_path

template_timer_dict = {
        'sports_basketball_gym': 16,
        'sports_nba_pass': 18,
        'sports_nba_dunk': 19,
        'movie_BruceLee1': 13,
        'shorts_kungfu_match1': 18,
        'shorts_kungfu_desert1': 18,
        'parkour_climbing': 12,
        'dance_indoor_1': 14,
}
template_timer_dict_fast = {
        'sports_basketball_gym': 8,
        'sports_nba_pass': 10,
        'sports_nba_dunk': 10,
        'movie_BruceLee1': 7,
        'shorts_kungfu_match1': 11,
        'shorts_kungfu_desert1': 10,
        'parkour_climbing': 6,
        'dance_indoor_1': 7,
}

def get_remaining_time(submit_time, task_id_tem=None, mode='fast'):
    # input format: "2024-11-28 10:52:58.238"
    # output format: 0.0
    submit_time = datetime.strptime(submit_time, "%Y-%m-%d %H:%M:%S.%f")
    current_time = datetime.now()
    process_time = (current_time - submit_time).seconds / 60
    # average_process_time = 15
    if mode == 'fast':
        if task_id_tem is not None and task_id_tem in template_timer_dict_fast.keys():
            average_process_time = template_timer_dict_fast[task_id_tem]
        else:
            average_process_time = 8
    else:
        if task_id_tem is not None and task_id_tem in template_timer_dict.keys():
            average_process_time = template_timer_dict[task_id_tem]
        else:
            average_process_time = 15

    retain_time = average_process_time - process_time
    return retain_time

def get_task_info(task_id, request_id):
    # task_id: fb87085b-5c37-4eb7-be63-1c80b9a9d771_dance_indoor_1_fast
    # task_id_req: fb87085b-5c37-4eb7-be63-1c80b9a9d771
    # task_id_tem: dance_indoor_1
    # mode: fast
    task_id_req = task_id.split('_')[0]
    task_id_tem_list = task_id.split('_')[1:-1]
    task_id_tem = '_'.join(task_id_tem_list)
    mode = task_id.split('_')[-1]
    print('task_id_req:', task_id_req)
    print('task_id_tem:', task_id_tem)
    print('task_id_mode:', mode)
    status, res = query_async(task_id_req, request_id)
    if status == "SUCCESS":
        res_url = res['output']['output_video_url']
        oss_path = convert_oss_url_to_oss_path(res_url)
        is_success, res_url = oss_service.sign(oss_path, timeout=3600)
        # return '您的视频已生成完毕', res_url
        return 'Your video processing is finished!', res_url

    elif status == "RUNNING":
        # process_time = get_remaining_time(res['output']['submit_time'], task_id_tem)
        process_time = get_remaining_time(res['output']['scheduled_time'], task_id_tem, mode)
        # return f'您的视频任务处理中，需等待{process_time:.1f}分钟左右，点击刷新获取最新生成进度', None
        if process_time>0:
            return f'Your video is processing, please wait for about {process_time:.1f} minutes, click Refresh to get the latest progress', None
        else:
            # return f'您的视频已生成，审核中，请稍候', None
            return f'Your video is generated and under review, please wait. You can lick Refresh to get the latest progress', None
    elif status == "PENDING":
        # return '当前使用人数较多，正在排队等待处理，点击刷新获取最新生成进度', None
        return 'Your task has been submitted. Do not submit repeatedly. The current number of users is large, waiting in queue for processing, click Refresh to get the latest progress.', None

    elif status == "UNKNOWN":
        return 'Your task id is not found, find results in history if you have refreshed the website', None
    else:
        # return "您的视频生成失败", None
        notes = 'Failed, '+res['output']['message']
        return notes, None





