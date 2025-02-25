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
URL_SERVICE_TEM = os.getenv("API_MIMO_TEM_URL")
MODEL_NAME_TEM = os.getenv("API_MIMO_TEM_MODEL_NAME")

oss_service = ossService()

def call_service_template(input_video_url, uuid, request_id):
    # task_id = '5a12afdc-327e-4f0f-9766-eadf4f245ce5'
    # return task_id

    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-DataInspection": "enable",
    }
    data = {
        "model": MODEL_NAME_TEM,
        "input": {
            "video_url": input_video_url,
        },
        "parameters": {
            "user_id": uuid,
            "log_path": request_id,
        }
    }
    url_create_task = URL_SERVICE_TEM
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
        print(f"task_id: {task_id}: Create MIMO-template request success. Params: {data}")
        logger.info(f"task_id: {task_id}: Create MIMO-template request success. Params: {data}")
        return task_id
    else:
        logger.error(f'Fail to create MIMO-template task: {res_.content}')
        raise gr.Error(f"Fail to create MIMO-template task: {res_.content}")


def query_async(task_id, request_id):
    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-DataInspection": "enable",
    }
    url_query = f'https://poc-dashscope.aliyuncs.com/api/v1/tasks/{task_id}'
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

def query_async_sim_temp(task_id):
    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-DataInspection": "enable",
    }
    url_query = f'https://poc-dashscope.aliyuncs.com/api/v1/tasks/{task_id}'
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
    average_process_time = 3

    retain_time = average_process_time - process_time
    return retain_time

def get_task_info_temp(task_id, request_id):
    # task_id = 'ff09fd94-598e-449c-b7ad-49c0b7cae443'
    # task_id = 'a5449e50-5064-48ca-9247-663894e17380'
    status, res = query_async(task_id, request_id)
    if status == "SUCCESS":
        res_url = res['output']['output_video_url']
        oss_path = convert_oss_url_to_oss_path(res_url)
        is_success, res_url = oss_service.sign(oss_path, timeout=3600)

        template_url = res['output']['output_template_url']
        template_id = template_url.split('/')[-1].split('?')[0]
        template_id = template_id.replace('.zip', '').replace('user_', '')

        return 'Your template processing is finished! Now you can copy your returned "Template-ID" to Tab1 for video generation.', res_url, template_id

    elif status == "RUNNING":
        # process_time = get_remaining_time(res['output']['submit_time'], task_id_tem)
        process_time = get_remaining_time(res['output']['scheduled_time'])
        # return f'您的视频任务处理中，需等待{process_time:.1f}分钟左右，点击刷新获取最新生成进度', None
        if process_time>0:
            return f'Your template is processing, please wait for about {process_time:.1f} minutes, click "Refresh" to get the latest progress', None, None
        else:
            # return f'您的视频已生成，审核中，请稍候', None
            return f'Your template processing is finished and under review, please wait. You can lick "Refresh" to get the latest progress', None, None
    elif status == "PENDING":
        # return '当前使用人数较多，正在排队等待处理，点击刷新获取最新生成进度', None
        return 'Your template task has been submitted. Do not submit repeatedly. The current number of users is large, waiting in queue for processing, click "Refresh" to get the latest progress.', None, None

    elif status == "UNKNOWN":
        return 'Your task id is not found, find results in history if you have refreshed the website', None, None
    else:
        notes = 'Failed, '+res['output']['message']
        return notes, None, None





