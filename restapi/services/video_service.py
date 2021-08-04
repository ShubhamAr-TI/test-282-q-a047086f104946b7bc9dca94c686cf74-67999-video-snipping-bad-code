import uuid

import boto3
import requests
from moviepy.editor import *

ACCESS_KEY = 'AKIAUOQYXSVUUFZPIGXH'
SECRET_KEY = '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'
TOKEN = 'CJ-Video-Test-{}'


def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False


class VideoService():

    BASE_URL = "https://cj-video-test.s3.amazonaws.com/{}"
    ProcessedFile = "video-proces-{}.mp4"

    @staticmethod
    def get_s3_name(name):
        return TOKEN.format(str(uuid.uuid1())) + name

    @staticmethod
    def validate_video_no_of_segments(video_url, no_of_segments):
        name = video_url.rsplit('/', 1)[1]
        r = requests.get(video_url, allow_redirects=True)
        open('/tmp/' + name, 'wb').write(r.content)
        clip = VideoFileClip('/tmp/' + name)
        if clip.duration < no_of_segments:
            return False
        return True

    @staticmethod
    def validate_video_range(video_url, ranges):
        name = video_url.rsplit('/', 1)[1]
        r = requests.get(video_url, allow_redirects=True)
        open('/tmp/' + name, 'wb').write(r.content)
        clip = VideoFileClip('/tmp/' + name)
        for part in ranges:
            if part.get("start") > clip.duration:
                return False
            if part.get("end") > clip.duration:
                return False
        return True

    @staticmethod
    def validate_combine(video_urls):
        for video in video_urls:
            video_url = video.get('video_url')
            name = video_url.rsplit('/', 1)[1]
            r = requests.get(video_url, allow_redirects=True)
            open('/tmp/' + name, 'wb').write(r.content)
            clip = VideoFileClip('/tmp/' + name)
            if video.get("start") > clip.duration:
                return False
            if video.get("end") > clip.duration:
                return False
        return True

    @staticmethod
    def process_interval(video_url, interval_time):
        result = []
        name = video_url.rsplit('/', 1)[1]
        r = requests.get(video_url, allow_redirects=True)
        open('/tmp/'+name, 'wb').write(r.content)
        clip = VideoFileClip('/tmp/' + name)
        no_of_file = int(int(clip.duration) / interval_time) + 1
        for i in range(0, no_of_file):
            new_name = VideoService.ProcessedFile.format(i)
            clip = VideoFileClip('/tmp/' + name)
            start = i*interval_time
            end = min((i+1)*interval_time, clip.duration)
            clip.subclip(start, end).write_videofile("/tmp/"+new_name)
            upload_to_aws("/tmp/" + new_name, "cj-video-test", VideoService.get_s3_name(new_name))
            result.append({"video_url": VideoService.BASE_URL.format(new_name)})

        return {"interval_videos": result}

    @staticmethod
    def process_ranges(video_url, ranges):
        result = []
        name = video_url.rsplit('/', 1)[1]
        r = requests.get(video_url, allow_redirects=True)
        open('/tmp/'+name, 'wb').write(r.content)
        i = 0
        for part in ranges:
            clip = VideoFileClip('/tmp/' + name)
            new_name = VideoService.ProcessedFile.format(i)
            clip.subclip(part.get("start"), part.get("end")).write_videofile("/tmp/"+new_name)
            s3_name = VideoService.get_s3_name(new_name)
            upload_to_aws("/tmp/" + new_name, "cj-video-test", s3_name)
            result.append({"video_url": VideoService.BASE_URL.format(s3_name)})
            i += 1

        return {"interval_videos": result}

    @staticmethod
    def process_segments(video_url, no_of_file):
        result = []
        name = video_url.rsplit('/', 1)[1]
        r = requests.get(video_url, allow_redirects=True)
        open('/tmp/' + name, 'wb').write(r.content)
        clip = VideoFileClip('/tmp/' + name)
        if clip.duration < no_of_file:
            return None
        interval_time = int(clip.duration) / no_of_file
        for i in range(0, no_of_file):
            clip = VideoFileClip('/tmp/' + name)
            new_name = VideoService.ProcessedFile.format(i)
            start = i * interval_time
            end = min((i + 1) * interval_time, clip.duration)
            clip.subclip(start, end).write_videofile("/tmp/" + new_name)
            s3_name = VideoService.get_s3_name(new_name)
            upload_to_aws("/tmp/" + new_name, "cj-video-test", s3_name)
            result.append({"video_url": VideoService.BASE_URL.format(s3_name)})

        return {"interval_videos": result}

    @staticmethod
    def combine_video(video_urls, width, height):
        clips = []
        for video in video_urls:
            video_url = video.get('video_url')
            name = video_url.rsplit('/', 1)[1]
            r = requests.get(video_url, allow_redirects=True)
            open('/tmp/' + name, 'wb').write(r.content)
            clip = VideoFileClip('/tmp/' + name)
            clips.append(clip.subclip(video.get("start"), video.get("end")))

        final_clip = concatenate_videoclips(clips)
        name = VideoService.ProcessedFile.format("f")
        final_clip.resize((height, width)).write_videofile("/tmp/" + name)
        s3_name = VideoService.get_s3_name(name)
        upload_to_aws("/tmp/" + name, "cj-video-test", s3_name)
        result = {"video_url": VideoService.BASE_URL.format(s3_name)}

        return result
