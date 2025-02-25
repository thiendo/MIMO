import os
import datetime
import gradio as gr
from oss_utils import ossService, get_random_string
from client import call_service, get_task_info, query_async_sim
from client_template import call_service_template, get_task_info_temp, query_async_sim_temp
import glob
import oss2
import time
import cv2

MOTION_TRIGGER_WORD = {
    'sports_basketball_gym': [],
    'sports_nba_pass': [],
    'sports_nba_dunk': [],
    'movie_BruceLee1': [],
    'shorts_kungfu_match1': [],
    'shorts_kungfu_desert1': [],
    'parkour_climbing': [],
    'dance_indoor_1': [],
}

css_style = "#fixed_size_img {height: 500px;}"

oss_service = ossService()


def load_css():
    with open('style.css', 'r') as file:
        css_content = file.read()
    return css_content

def refresh_video(uuid, request_id, task_id):
    print(f'[refresh_video] uuid: {uuid}, request_id: {request_id}, task_id: {task_id}')

    if uuid is None or uuid == '':
        # uuid = 'user-' + get_random_string()
        uuid = 'test_local_user'
        print(f'[refresh_video] generate a uuid {uuid}')

    if task_id is None or task_id == '':
        # notes = '请先点击生成按钮提交任务'
        notes = 'Please click the "Run" button to submit the task first'
        return notes, None, uuid, task_id

    if task_id.startswith('example_res'):
        output = task_id.split('-')[1]
        notes = f"This video has been generated before, return the result directly"
        return notes, output, uuid, task_id

    print(f'[refresh_video] uuid: {uuid}')
    print(f'[refresh_video] request_id: {request_id}')

    # notes, process_status = query_async(task_id, request_id)
    notes, res_url = get_task_info(task_id, request_id)
    print('Output generated video:', res_url)

    if res_url is not None and res_url != '':
        try:
            save_dir = 'output'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            outpath = f"{save_dir}/output.mp4"
            res = oss_service.downloadFile(res_url, outpath)
            if res == True and os.path.exists(outpath):
                print('saved to %s' % outpath)
                return notes, outpath, uuid, task_id
            else:
                print('Download video failed')
                raise gr.Error("Download video failed, please try again later.")
        except Exception as e:
            print('Download video failed')
            raise gr.Error("Download video failed, please try again later.")
    else:
        return notes, res_url, uuid, task_id

def refresh_template(uuid, request_id, task_id):
    print(f'[refresh_template] uuid: {uuid}, request_id: {request_id}, task_id: {task_id}')

    if uuid is None or uuid == '':
        # uuid = 'user-' + get_random_string()
        uuid = 'test_local_user'
        print(f'[refresh_video] generate a uuid {uuid}')

    if task_id is None or task_id == '':
        # notes = '请先点击生成按钮提交任务'
        notes = 'Please click the "Run" button to submit the task first'
        return None, None, notes, uuid, task_id

    if task_id.startswith('example_res'):
        output = task_id.split('-')[1]
        notes = f"This video has been generated before, return the result directly"
        return None, output, notes, uuid, task_id

    print(f'[refresh_template] uuid: {uuid}, request_id: {request_id}')

    # notes, process_status = query_async(task_id, request_id)
    notes, res_url, template_id = get_task_info_temp(task_id, request_id)
    print(f'[refresh_template] Output video: {res_url}, template_id: {template_id}')

    if template_id is not None and template_id != '':
        try:
            save_dir = 'output_template'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            outpath = f"{save_dir}/output.mp4"
            res = oss_service.downloadFile(res_url, outpath)
            if res == True and os.path.exists(outpath):
                print('saved to %s' % outpath)
                return template_id, outpath, notes, uuid, task_id
            else:
                print('Download output video failed')
                raise gr.Error("Download video failed, please try again later.")
        except Exception as e:
            print('Download video failed')
            raise gr.Error("Download video failed, please try again later.")
    else:
        return template_id, res_url, notes, uuid, task_id

def get_user_history(uuid):
    if uuid is None or uuid == '':
        uuid = 'test_local_user'
        print(f'[get_user_templates] generate a uuid {uuid}')
    print(f'[get_user_history] uuid: {uuid}')
    video_dict = {}
    # get before 30 days
    save_days = 30
    for i in range(save_days):
        date_string = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        # print(f"date_string: {date_string}")
        directory = 'service_dashscope/Mimo/' + date_string + '/' + uuid + '/'
        for obj in oss2.ObjectIterator(oss_service.bucket, prefix=directory, delimiter='/'):
            # print(f"folder is existed {directory}")
            break
        else:
            # print(f"folder is not existed: {directory}")
            continue

        for obj in oss2.ObjectIterator(oss_service.bucket, prefix=directory, delimiter='/'):
            # print(f"obj: {obj}")
            # print(f"obj.key: {obj.key}")
            if obj.is_prefix():  # folder
                file_full_path = obj.key + 'result.mp4'
                exist = oss_service.bucket.object_exists(file_full_path)

                if not exist:
                    print(f'{file_full_path} is not existed')
                    tmp_directory = obj.key
                    # print(f'tmp_directory = {tmp_directory}')
                    for obj_xxx in oss2.ObjectIterator(oss_service.bucket, prefix=tmp_directory, delimiter='/'):
                        # print(f'obj_xxx.key = {obj_xxx.key}')
                        if obj_xxx.is_prefix():  # folder
                            pass
                        else:
                            import re
                            pattern = r"result-.*\.mp4"
                            # Extract the MP4 file name
                            file_name_xxx = os.path.basename(obj_xxx.key)
                            match = re.search(pattern, obj_xxx.key)
                            if match and len(match.group()) == len(file_name_xxx):
                                file_full_path = obj_xxx.key
                                print(f'successfully match file_full_path: {file_full_path}')
                                time = file_full_path.split('/')[-2]
                                video_dict[time] = file_full_path
                                exist = True
                                break
                else:
                    pass

            else:  # file
                print(f'not a file: {obj.key}')

    print(f'video_dict: {video_dict}')
    # sort the video_dict by time
    video_dict = dict(sorted(video_dict.items(), key=lambda item: item[0]))
    # get the values of video_dict
    video_list = list(video_dict.values())

    video_list_sign = []
    for file_full_path in video_list:
        oss_video_path = oss_service.Prefix + "/" + file_full_path
        _, video_url = oss_service.sign(oss_video_path, timeout=3600 * 100)
        # download to local
        save_dir = 'output'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        local_path = f"{save_dir}/{os.path.basename(file_full_path)}"
        oss_service.downloadFile(video_url, local_path)
        # video_list_sign.append(video_url)
        video_list_sign.append(local_path)

    video_list_sign = video_list_sign[::-1]
    if len(video_list_sign) < 8:
        video_list_sign = video_list_sign + [None] * (8 - len(video_list_sign))
    else:
        video_list_sign = video_list_sign[:8]

    # video_list_sign = video_list_sign[:1]
    return video_list_sign

def get_user_templates(uuid):
    if uuid is None or uuid == '':
        uuid = 'test_local_user'
        print(f'[get_user_templates] generate a uuid {uuid}')
    print(f'[get_user_templates] uuid: {uuid}')
    video_dict = {}
    # get before 30 days
    save_days = 30
    for i in range(save_days):
        date_string = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        # print(f"date_string: {date_string}")
        directory = 'service_dashscope/Mimo_template/' + date_string + '/' + uuid + '/'
        for obj in oss2.ObjectIterator(oss_service.bucket, prefix=directory, delimiter='/'):
            # print(f"folder is existed {directory}")
            break
        else:
            # print(f"folder is not existed: {directory}")
            continue

        for obj in oss2.ObjectIterator(oss_service.bucket, prefix=directory, delimiter='/'):
            # print(f"obj: {obj}")
            # print(f"obj.key: {obj.key}")
            if obj.is_prefix():  # folder
                file_full_path = obj.key + 'result.mp4'
                exist = oss_service.bucket.object_exists(file_full_path)

                if not exist:
                    print(f'{file_full_path} is not existed')
                    tmp_directory = obj.key
                    # print(f'tmp_directory = {tmp_directory}')
                    for obj_xxx in oss2.ObjectIterator(oss_service.bucket, prefix=tmp_directory, delimiter='/'):
                        # print(f'obj_xxx.key = {obj_xxx.key}')
                        if obj_xxx.is_prefix():  # folder
                            pass
                        else:
                            import re
                            pattern = r"result-.*\.mp4"
                            # Extract the MP4 file name
                            file_name_xxx = os.path.basename(obj_xxx.key)
                            match = re.search(pattern, obj_xxx.key)
                            if match and len(match.group()) == len(file_name_xxx):
                                file_full_path = obj_xxx.key
                                print(f'successfully match file_full_path: {file_full_path}')
                                time = file_full_path.split('/')[-2]
                                video_dict[time] = file_full_path
                                exist = True
                                break
                else:
                    pass

            else:  # file
                print(f'not a file: {obj.key}')

    print(f'video_dict: {video_dict}')
    # sort the video_dict by time
    video_dict = dict(sorted(video_dict.items(), key=lambda item: item[0]))
    # get the values of video_dict
    video_list = list(video_dict.values())

    video_list_sign = []
    for file_full_path in video_list:
        oss_video_path = oss_service.Prefix + "/" + file_full_path
        _, video_url = oss_service.sign(oss_video_path, timeout=3600 * 100)
        # download to local
        save_dir = 'output'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        local_path = f"{save_dir}/{os.path.basename(file_full_path)}"
        oss_service.downloadFile(video_url, local_path)
        # video_list_sign.append(video_url)
        video_list_sign.append(local_path)

    video_list_sign = video_list_sign[::-1]
    if len(video_list_sign) < 8:
        video_list_sign = video_list_sign + [None] * (8 - len(video_list_sign))
    else:
        video_list_sign = video_list_sign[:8]

    # video_list_sign = video_list_sign[:1]
    tempale_id_list = []
    # tempale_id_list = [None] * (8)
    for x in video_list_sign:
        if x is None:
            tempale_id_list.append(None)
        else:
            tempale_id_list.append('ID: '+os.path.basename(x).replace('result-','').replace('.mp4',''))

    return tempale_id_list+video_list_sign




def record_request(uuid, task_id):
    # save the request to 'oss://vigen-invi/service_dashscope/Mimo/request_record/2024-12-03/uuid/task_id'
    date_string = datetime.datetime.now().strftime('%Y-%m-%d')
    directory = 'service_dashscope/Mimo/request_record/' + date_string + '/' + uuid + '/'
    if not oss_service.bucket.object_exists(directory):
        oss_service.bucket.put_object(directory, '')
    file_full_path = directory + task_id
    if not oss_service.bucket.object_exists(file_full_path):
        oss_service.bucket.put_object(file_full_path, '')
    print(f'[record_request] uuid: {uuid}, task_id: {task_id} has been recorded')

def record_request_template(uuid, task_id):
    # save the request to 'oss://vigen-invi/service_dashscope/Mimo/request_record/2024-12-03/uuid/task_id'
    date_string = datetime.datetime.now().strftime('%Y-%m-%d')
    directory = 'service_dashscope/Mimo_template/request_record/' + date_string + '/' + uuid + '/'
    if not oss_service.bucket.object_exists(directory):
        oss_service.bucket.put_object(directory, '')
    file_full_path = directory + task_id
    if not oss_service.bucket.object_exists(file_full_path):
        oss_service.bucket.put_object(file_full_path, '')
    print(f'[record_request_template] uuid: {uuid}, task_id: {task_id} has been recorded')

def check_request_valid(uuid):
    # get all the task_id in 'oss://vigen-invi/service_dashscope/Mimo/request_record/2024-12-03/uuid/'
    date_string = datetime.datetime.now().strftime('%Y-%m-%d')
    directory = 'service_dashscope/Mimo/request_record/' + date_string + '/' + uuid + '/'
    if not oss_service.bucket.object_exists(directory):
        return True
    run_task_num = 0
    running_task_id = []
    for obj in oss2.ObjectIterator(oss_service.bucket, prefix=directory, delimiter='/'):
        # print('obj:', obj.key)
        task_id = os.path.basename(obj.key)
        if task_id=='' or task_id is None:
            continue
        # print('task_id:', task_id)
        status = query_async_sim(task_id)
        if status == 'RUNNING' or status == 'PENDING':
            run_task_num += 1
            running_task_id.append(task_id)

    if run_task_num >= 2:
        print(f'[check_request_valid] Invalid request, uuid: {uuid}, run_task_num:{run_task_num}')
        print('running_task_id:', running_task_id)
        return False

    return True

def check_template_request_valid(uuid):
    # get all the task_id in 'oss://vigen-invi/service_dashscope/Mimo/request_record/2024-12-03/uuid/'
    date_string = datetime.datetime.now().strftime('%Y-%m-%d')
    directory = 'service_dashscope/Mimo_template/request_record/' + date_string + '/' + uuid + '/'
    if not oss_service.bucket.object_exists(directory):
        return True
    run_task_num=0
    running_task_id = []
    for obj in oss2.ObjectIterator(oss_service.bucket, prefix=directory, delimiter='/'):
        # print('obj:', obj.key)
        task_id = os.path.basename(obj.key)
        if task_id=='' or task_id is None:
            continue
        # print('task_id:', task_id)
        status = query_async_sim_temp(task_id)
        if status == 'RUNNING' or status == 'PENDING':
            run_task_num += 1
            running_task_id.append(task_id)

    if run_task_num >= 2:
        print(f'[check_template_request_valid] Invalid request, uuid: {uuid}, run_task_num:{run_task_num}')
        print('running_task_id:', running_task_id)
        return False

    return True




class WebApp():
    def __init__(self, debug_mode=False):
        self.args_base = {
            "device": "cuda",
            "output_dir": "output_demo",
            "img": None,
            "pos_prompt": '',
            "motion": "sports_basketball_gym",
            "motion_dir": "./assets/test_video_trunc",
        }

        self.args_input = {}  # for gr.components only
        self.gr_motion = list(MOTION_TRIGGER_WORD.keys())

        # fun fact: google analytics doesn't work in this space currently
        self.gtag = os.environ.get('GTag')

        self.ga_script = f"""
            <script async src="https://www.googletagmanager.com/gtag/js?id={self.gtag}"></script>
            """
        self.ga_load = f"""
            function() {{
                window.dataLayer = window.dataLayer || [];
                function gtag(){{dataLayer.push(arguments);}}
                gtag('js', new Date());

                gtag('config', '{self.gtag}');
            }}
            """

        self.preload_example_results()

    def preload_example_results(self):
        print('Pre-download example results')
        # download results from oss to local
        directory = 'service_dashscope/Mimo/example_results_cache/'
        for obj in oss2.ObjectIterator(oss_service.bucket, prefix=directory, delimiter='/'):
            # print('obj:', obj.key)
            oss_video_path = oss_service.Prefix + "/" + obj.key
            # download to local
            save_dir = 'output'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            local_path = f"{save_dir}/{os.path.basename(obj.key)}"
            if os.path.exists(local_path):
                continue
            _, video_url = oss_service.sign(oss_video_path, timeout=3600 * 100)
            status = oss_service.downloadFile(video_url, local_path)

            if status == 1:
                print(f"Successfully download {local_path}")

    def title(self):

        gr.HTML(
            """
            <div style="display: flex; justify-content: center; align-items: center; text-align: center;">
            <a href="https://menyifang.github.io/projects/En3D/index.html" style="margin-right: 20px; text-decoration: none; display: flex; align-items: center;">
            </a>
            <div>
                <h1 >\N{fire}MIMO: Controllable Character Video Synthesis</h1>
                <h4 >v1.5</h4>
                <h5 style="margin: 0;">
                The latest updates will be available at our repository, <a href="https://github.com/menyifang/MIMO" target="_blank">Github star it here</a>.
                </h5>
                <div style="display: flex; justify-content: center; align-items: center; text-align: center; margin: 20px; gap: 10px;">
                    <a class="flex-item" href="https://arxiv.org/abs/2409.16160" target="_blank">
                        <img src="https://img.shields.io/badge/Paper-arXiv-darkred.svg" alt="arXiv Paper">
                    </a>                      
                    <a class="flex-item" href="https://menyifang.github.io/projects/MIMO/index.html" target="_blank">
                        <img src="https://img.shields.io/badge/Project_Page-MIMO-green.svg" alt="Project Page">
                    </a>
                    <a class="flex-item" href="https://github.com/menyifang/MIMO" target="_blank">
                        <img src="https://img.shields.io/badge/Github-Code-blue.svg" alt="GitHub Code">
                    </a>

                </div>

            </div>
            </div>
            """
        )

    def get_template(self, num_cols=3):
        self.args_input['motion'] = gr.State('sports_basketball_gym')
        num_cols = 2
        lora_gallery = gr.Gallery(label='Gallery', columns=num_cols, height=360,
                                  value=[(os.path.join(self.args_base['motion_dir'], f"{motion}.mp4"), '') for
                                         motion in
                                         self.gr_motion],
                                  show_label=True,
                                  selected_index=0)

        lora_gallery.select(self._update_selection, inputs=[], outputs=[self.args_input['motion']])
        print(self.args_input['motion'])

    def _update_selection(self, selected_state: gr.SelectData):
        return self.gr_motion[selected_state.index]

    def run_process(self, *values):
        gr_args = self.args_base.copy()
        for k, v in zip(list(self.args_input.keys()), values[4:]):
            print('k:', k)
            print('v:', v)
            gr_args[k] = v

        ref_image_path = gr_args['img']
        template_name = gr_args['motion']
        uuid = values[0]
        request_id = values[1]
        mode = values[2]

        template_id_custom = values[3]
        if template_id_custom is not None and template_id_custom != '':
            template_name = 'user_' + template_id_custom

        if 'fast' in mode:
            mode = 'fast'
        else:
            mode = 'accurate'
        print('mode:', mode)
        if uuid is None or uuid == '':
            # uuid = 'user-' + get_random_string()
            uuid = 'test_local_user'
            print(f'[run_generation] generate a uuid {uuid}')
        if request_id is None or request_id == '':
            request_id = get_random_string()
            print(f'[run_generation] generate a request_id {request_id}')

        if not request_id.startswith('2025'):
            request_id = get_random_string()

        print(f'[run_generation] uuid: {uuid}, request_id: {request_id}, ref_image_path: {ref_image_path}, template_name: {template_name}')

        save_dir = 'output'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # check ref is not none
        if ref_image_path is None:
            raise gr.Error("Please upload an image or select an example first.")
        ref_name = os.path.basename(ref_image_path).split('.')[0]
        outpath = f"{save_dir}/{template_name}_{ref_name}.mp4"
        if os.path.exists(outpath):
            # notes = '该视频已生成过，直接展示结果'
            notes = f"This video has been generated before, return the result directly"
            task_id = 'example_res'+'-'+outpath
            return notes, outpath, uuid, task_id

        # judge the validity of request
        is_valid = check_request_valid(uuid)
        if is_valid is False:
            # notes = '您有未完成的任务，请等待完成后再提交新任务'
            notes = 'You have an unfinished task, please wait for completion before submitting a new task'
            return notes, None, uuid, None

        # resize ref_img is too large
        ref_img = cv2.imread(ref_image_path)
        # resize max size to 4096
        max_size = 4096
        if ref_img.shape[0] > max_size or ref_img.shape[1] > max_size:
            scale = max_size / max(ref_img.shape[0], ref_img.shape[1])
            ref_img = cv2.resize(ref_img, (int(ref_img.shape[1] * scale), int(ref_img.shape[0] * scale)), interpolation=cv2.INTER_AREA)
            cv2.imwrite(ref_image_path, ref_img)

        try:
            oss_path = os.path.join(oss_service.ObjectName, 'tmp_test_images', request_id + '.png')
            is_success, ref_img_url = oss_service.uploadOssFile(oss_path, ref_image_path, timeout=3600*100) # consider queue time
            print(f"request_id: {request_id}, is_success={is_success}, sign_img_oss_path={ref_img_url}")
        except Exception as e:
            raise gr.Error("Upload image failed, please try again later.")

        print('ref_img_url:', ref_img_url)
        print('template_name:', template_name)

        returned_task_id = call_service(ref_img_url, template_name, uuid, request_id, mode)

        # record the submitted request with task_id
        record_request(uuid, returned_task_id)



        # add template_name to task_id
        # returned_task_id = returned_task_id + '_' + template_name # fb87085b-5c37-4eb7-be63-1c80b9a9d771_dance_indoor_1_fast
        returned_task_id = returned_task_id + '_' + template_name
        returned_task_id = returned_task_id + '_' + mode # fb87085b-5c37-4eb7-be63-1c80b9a9d771_dance_indoor_1_fast

        time.sleep(1)

        return refresh_video(uuid, request_id, returned_task_id)

    def run_template_process(self, vid_input, uuid, task_id, request_id):
        if uuid is None or uuid == '':
            uuid = 'test_local_user'
            print(f'[run_template_process] generate a uuid {uuid}')
        if request_id is None or request_id == '':
            request_id = get_random_string()
            print(f'[run_template_process] generate a request_id {request_id}')
        if not request_id.startswith('2025'):
            request_id = get_random_string()

        print(f'[run_template_process] uuid: {uuid}, task_id: {task_id} vid_input: {vid_input}')

        template_id = 'xxxx-xxxx-xxxx-xxxx'
        vid_output = vid_input
        user_notes = 'This is a test'

        save_dir = 'output_template'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # check video is not none
        if vid_input is None:
            raise gr.Error("Please upload a video or select a video first.")
        outpath = f"{save_dir}/{request_id}.mp4"

        # judge the validity of request
        is_valid = check_template_request_valid(uuid)
        if is_valid is False:
            # notes = '您有未完成的任务，请等待完成后再提交新任务'
            # notes = 'You have an unfinished task, please wait for completion before submitting a new task'
            # notes = '您提交的任务数已达上限，请等待完成后再提交新任务'
            notes = 'You have reached the maximum number of tasks submitted, please wait for completion before submitting new tasks'
            return None, None, notes, uuid, None

        # check video size, <50M
        file_size = os.path.getsize(vid_input) / 1048576  # MB
        if file_size > 50:
            raise gr.Error("The size of input video should <50MB")

        # upload video to oss
        try:
            oss_path = os.path.join(oss_service.ObjectName, 'tmp_test_videos', request_id + '.mp4')
            is_success, video_url = oss_service.uploadOssFile(oss_path, vid_input,
                                                                timeout=3600 * 100)  # consider queue time
            print(f"request_id: {request_id}, is_success={is_success}, sign_video_oss_path={video_url}")
        except Exception as e:
            raise gr.Error("Upload video failed, please try again later.")

        print('video_url:', video_url)

        returned_task_id = call_service_template(video_url, uuid, request_id)

        # record the submitted request with task_id
        record_request_template(uuid, returned_task_id)
        #
        # # add template_name to task_id
        # # returned_task_id = returned_task_id + '_' + template_name # fb87085b-5c37-4eb7-be63-1c80b9a9d771_dance_indoor_1_fast
        # returned_task_id = returned_task_id + '_' + template_name
        # returned_task_id = returned_task_id + '_' + mode  # fb87085b-5c37-4eb7-be63-1c80b9a9d771_dance_indoor_1_fast
        #
        time.sleep(1)

        # template_id = returned_task_id
        # return template_id, vid_output, user_notes, uuid, task_id

        return refresh_template(uuid, request_id, returned_task_id)

    def show_guide(self):
        with gr.Accordion(label="🧭 操作指南 (Guide):", open=True, elem_id="accordion"):
            with gr.Row(equal_height=True):
                gr.Markdown("""
                - ⭐️ <b>步骤1：</b>在“输入图像”中上传角色图或选择示例中的一张图片   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;       &nbsp;&nbsp;&nbsp;&nbsp;          (<b>step1：</b> Upload a character image or select an example)
                - ⭐️ <b>步骤2：</b>在模版库中选择驱动视频或输入自定义模版ID    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;     (<b>step2：</b> Select a driving video in the gallery, or input your customed Template-ID)
                - ⭐️ <b>步骤3：</b>如使用自定义驱动模版，切换至Tab2-上传视频-视频解析-刷新，得到模版ID  (<b>step3：</b> If using custom template, switch to Tab2, Upload video-Run-Refresh, and get the Template-ID)
                - ⭐️ <b>步骤4：</b>选择生成模式(快速/精细)，点击“一键生成”提交任务    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    &nbsp;&nbsp;&nbsp;&nbsp;   (<b>step4：</b> Select the generation mode (fast or accurate), and click "Run" to submit the task)
                - ⭐️ <b>步骤5：</b>点击刷新查看任务状态，预计处理时长6-15分钟左右     &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    &nbsp;&nbsp;&nbsp;&nbsp;     (<b>step5：</b> Click "Refresh" to check the task status, the processing time is about 6-15 minutes)
                - <b>注意事项: </b>角色图要求为单人全身正面照、无遮挡、无手持物        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    (<b>Note: </b> The input image should be full-body, front-facing, no occlusion, no handheld objects)
                -   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;   驱动视频应包含连续人物动作，全身入镜，人物勿过大过小    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    (The input driving video should contain character with continuous, full-body motions in the frame)

                """)


    def preset_library(self):
        # with gr.Blocks() as demo:
            # with gr.Accordion(label="🧭 操作指南 (Guide):", open=True, elem_id="accordion"):
            #     with gr.Row(equal_height=True):
            #         gr.Markdown("""
            #         - ⭐️ <b>步骤1：</b>在“输入图像”中上传角色图或选择示例中的一张图片          &nbsp;&nbsp;&nbsp;&nbsp;          (<b>step1：</b> Upload a character image or select an example)
            #         - ⭐️ <b>步骤2：</b>在模版库中选择驱动视频    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;     (<b>step2：</b> Select a driving video in the gallery)
            #         - ⭐️ <b>步骤3：</b>选择生成模式(快速/精细)，点击“一键生成”提交任务        &nbsp;&nbsp;&nbsp;&nbsp;   (<b>step3：</b> Select the generation mode (fast or accurate), and click "Run" to submit the task)
            #         - ⭐️ <b>步骤4：</b>点击刷新查看任务状态，预计处理时长15分钟左右         &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;     (<b>step4：</b> Click "Refresh" to check the task status, the processing time is about 15 minutes)
            #         - <b>注意事项: </b>角色图要求为单人全身正面照、无遮挡、无手持物            &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    (<b>Note: </b> The input image should be full-body, front-facing, no occlusion, no handheld objects)
            #         """)

            with gr.Row():
                with gr.Column():
                    img_input = gr.Image(label='输入图像 (Input character)', type="filepath", elem_id="fixed_size_img")
                    mode_input = gr.Radio(label='生成设置（Generation setting)', show_label=False, choices=['快速生成 (fast)', '精细生成 (accurate)'], value='快速生成 (fast)')

                self.args_input['img'] = img_input

                with gr.Column():
                    with gr.Accordion(label="视频模版库", open=True, elem_id="accordion"):
                        self.get_template(num_cols=3)
                    template_id = gr.Textbox(label="自定义模版ID", show_label=True, text_align='left')
                    submit_btn_load3d = gr.Button("一键生成（Run)", variant='primary')
                with gr.Column(scale=1.2):
                    res_vid = gr.Video(format="mp4", label="生成结果 (Generated result)", autoplay=True, elem_id="fixed_size_img")

                    with gr.Row():
                        with gr.Column(scale=0.8, min_width=0.8):
                            user_notes = gr.Textbox(show_label=False, text_align='left')

                        with gr.Column(scale=0.2, min_width=0.2):
                            refresh_button = gr.Button(value="刷新(Refresh)", variant='primary')

            uuid = gr.Text(label="modelscope_uuid", visible=False)
            request_id = gr.Text(label="modelscope_request_id", visible=False)
            task_id = gr.Text(label="modelscope_task_id", visible=False)

            input_list = [uuid, request_id, mode_input, template_id] + list(self.args_input.values())
            submit_btn_load3d.click(self.run_process,
                                    inputs=input_list,
                                    outputs=[user_notes, res_vid, uuid, task_id],
                                    scroll_to_output=False,
                                    concurrency_limit=4
                                    )

            refresh_button.click(
                fn=refresh_video,
                queue=False,
                inputs=[uuid, request_id, task_id],
                outputs=[user_notes, res_vid, uuid, task_id]
            )

            gr.Examples(examples=[
                ['./assets/test_image/sugar.jpg'],
                ['./assets/test_image/ouwen1.png'],
                ['./assets/test_image/actorhq_A1S1.png'],
                ['./assets/test_image/actorhq_A7S1.png'],
                ['./assets/test_image/cartoon1.png'],
                ['./assets/test_image/cartoon2.png'],
                ['./assets/test_image/sakura.png'],
                ['./assets/test_image/kakashi.png'],
                ['./assets/test_image/sasuke.png'],
                ['./assets/test_image/avatar.jpg'],
            ], inputs=[img_input],
                examples_per_page=20, label="示例 (Example)", elem_id="examples",
            )

            # get the value from the gr.Textbox 'uuid'
            num_video = 8
            num_videos_per_row = 4
            history_button = gr.Button(value="查看历史记录 (History)", elem_id='button_param1', visible=True)

            gr_video_list = []
            with gr.Row(elem_id='show_box'):
                with gr.Column():
                    for i in range(int((num_video + num_videos_per_row - 1) / num_videos_per_row)):
                        with gr.Row():
                            for j in range(num_videos_per_row):
                                    # gr.Video(value=mp4_lists[i * num_videos_per_row + j], show_label=False,
                                    #          interactive=False, label='result')
                                # gr_video_list.append(gr.Video(format="mp4", autoplay=True,show_label=False, label='result'))
                                gr_video_list.append(gr.Video(format="mp4", autoplay=True, show_label=False, label='result',
                                                    interactive=False, elem_id="fixed_size_img"))

            history_button.click(
                fn=get_user_history,
                queue=False,
                inputs=[uuid],
                outputs=gr_video_list
            )

    def custom_video(self):
        with (gr.Blocks() as demo):
            with gr.Row():
                with gr.Column():
                    vid_input = gr.Video(format="mp4", label="输入视频 (Input video)", autoplay=True,
                                   elem_id="fixed_size_img")
                    submit_btn_parser = gr.Button("视频解析（Run)", variant='primary')

                with gr.Column():
                    template_id = gr.Textbox(label="模版ID (Template-ID)", show_label=True, text_align='left')
                    vid_output = gr.Video(format="mp4", label="主体追踪结果 (Tracking result)", autoplay=True, interactive=False, elem_id="fixed_size_vid_track")

                    with gr.Row():
                        with gr.Column(scale=0.8, min_width=0.8):
                            user_notes = gr.Textbox(show_label=False, text_align='left')
                        with gr.Column(scale=0.2, min_width=0.2):
                            refresh_button = gr.Button(value="刷新(Refresh)", variant='primary')

                uuid = gr.Text(label="modelscope_uuid", visible=False)
                task_id = gr.Text(label="modelscope_task_id", visible=False)
                request_id = gr.Text(label="modelscope_request_id", visible=False)

                submit_btn_parser.click(self.run_template_process,
                                        inputs=[vid_input, uuid, task_id, request_id],
                                        outputs=[template_id, vid_output, user_notes, uuid, task_id],
                                        scroll_to_output=False,
                                        )

                refresh_button.click(
                    fn=refresh_template,
                    queue=False,
                    inputs=[uuid, request_id, task_id],
                    outputs=[template_id, vid_output, user_notes, uuid, task_id]
                )

            # with gr.Accordion(label="【可选】交互式追踪工作区", open=True, elem_id="accordion"):
            #     gr.Markdown("## <center>To be added</center>")

            gr.Examples(examples=[
                ['./assets/test_video_trunc/sports_basketball_gym.mp4'],
                ['./assets/test_video_trunc/movie_BruceLee1.mp4'],
            ], inputs=[vid_input],
                examples_per_page=10, label="示例 (Example)", elem_id="examples",
            )

            num_video = 8
            num_videos_per_row = 4
            my_template_button = gr.Button(value="查看我的模版 (My Templates)", elem_id='button_param1', visible=True)

            gr_template_vid_list = []
            gr_template_id_list = []

            with gr.Row(elem_id='show_box'):
                with gr.Column():
                    for i in range(int((num_video + num_videos_per_row - 1) / num_videos_per_row)):
                        with gr.Row():
                            for j in range(num_videos_per_row):
                                gr_template_id_list.append(gr.Textbox(label="", show_label=False, text_align='left'))
                        with gr.Row():
                            for j in range(num_videos_per_row):
                                gr_template_vid_list.append(gr.Video(format="mp4", autoplay=True, show_label=False, label='', interactive=False, elem_id='fixed_size_vid_track'))

            my_template_button.click(
                fn=get_user_templates,
                queue=False,
                inputs=[uuid],
            # outputs=[gr_template_vid_list, gr_template_id_list]
                # outputs=gr_template_vid_list
            outputs = gr_template_id_list+gr_template_vid_list

            )

    def ui(self):
        with gr.Blocks(#css='style.css',
            css = load_css(),
            # theme=gr.themes.Soft()
        ) as demo:
        # with gr.Blocks(css=css_style) as demo:
            self.title()
            self.show_guide()
            with gr.Tabs():
                with gr.TabItem('【Tab 1】视频角色编辑'):
                    self.preset_library()
                with gr.TabItem('【Tab 2】自定义驱动视频'):
                    # gr.Markdown("## <center>Coming soon!</center>")
                    self.custom_video()

            demo.load(None, js=self.ga_load)

        return demo


app = WebApp(debug_mode=False)
demo = app.ui()

if __name__ == "__main__":
    demo.queue(max_size=100)
    demo.launch(share=False)
