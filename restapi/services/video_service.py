import uuid

import boto3
import requests
import logging
from moviepy.editor import VideoFileClip, concatenate_videoclips

logger = logging.getLogger("Rest")

# FIXME: App Secrets
ACCESS_KEY = 'AKIAUOQYXSVUUFZPIGXH'
SECRET_KEY = '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'
TOKEN = 'CJ-Video-Test-{}'


def upload_to_aws(local_file, bucket, s3_file):
    '''
        Method to upload to AWS
    '''
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)

    try:
        s3.upload_file(local_file, bucket, s3_file)
        logger.info("Upload Successful")
        return True
    except FileNotFoundError:
        logger.info("The file was not found")
        return False


class VideoService(object):
    '''
        Actual Service to process the videos and store them
    '''

    base_url = "https://cj-video-test.s3.amazonaws.com/{}"
    processed_file = "video-proces-{}.mp4"

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
            new_name = VideoService.processed_file.format(i)
            clip = VideoFileClip('/tmp/' + name)
            start = i*interval_time
            end = min((i+1)*interval_time, clip.duration)
            clip.subclip(start, end).write_videofile("/tmp/"+new_name)
            fname = "/tmp/" + new_name
            s3_name = VideoService.get_s3_name(new_name)
            upload_to_aws(fname, "cj-video-test", s3_name)
            video_url = VideoService.base_url.format(new_name)
            result.append({"video_url": video_url})

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
            new_name = VideoService.processed_file.format(i)
            start, end = part.get("start"), part.get("end")
            clip.subclip(start, end).write_videofile("/tmp/"+new_name)
            s3_name = VideoService.get_s3_name(new_name)
            upload_to_aws("/tmp/" + new_name, "cj-video-test", s3_name)
            result.append({"video_url": VideoService.base_url.format(s3_name)})
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
            new_name = VideoService.processed_file.format(i)
            start = i * interval_time
            end = min((i + 1) * interval_time, clip.duration)
            clip.subclip(start, end).write_videofile("/tmp/" + new_name)
            s3_name = VideoService.get_s3_name(new_name)
            upload_to_aws("/tmp/" + new_name, "cj-video-test", s3_name)
            result.append({"video_url": VideoService.base_url.format(s3_name)})

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
        name = VideoService.processed_file.format("f")
        final_clip.resize((height, width)).write_videofile("/tmp/" + name)
        s3_name = VideoService.get_s3_name(name)
        upload_to_aws("/tmp/" + name, "cj-video-test", s3_name)
        result = {"video_url": VideoService.base_url.format(s3_name)}
        return result
