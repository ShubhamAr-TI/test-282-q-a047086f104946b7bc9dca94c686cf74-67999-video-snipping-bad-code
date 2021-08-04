import logging
import os
from shutil import copyfile, rmtree

from django.http import HttpResponse
# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from leadsapi.settings import BASE_DIR
from restapi.services.video_service import VideoService

logger = logging.getLogger("Rest")


def index(request):
    """
    Index view for the video API
    """
    return HttpResponse("Hello, world. You're at Video API.")


def check_request_params(request, params):
    """
    validates params for a request
    """
    for param in params:
        if request.data.get(param, None) is None:
            return True
    return False


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def process_interval(request):
    """
    Store the Result for User Url
    """
    try:
        # Validation Service
        request_params = ['video_link', 'video_link', 'interval_duration']
        if check_request_params(request, request_params):
            resp = {"reason": "invalid parameters"}
            return Response(resp, status=status.HTTP_400_BAD_REQUEST)
        video_link = request.data.get('video_link', None)
        interval_duration = request.data.get('interval_duration', None)
        result = VideoService.process_interval(video_link, interval_duration)
    except RuntimeError as ex:
        logging.error("Error : %s", ex)
        resp = {"reason": "Could not process" + str(ex)}
        return Response(resp, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return Response(result)


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def process_range(request):
    """
    Store the Result for User Url
    """
    try:
        request_params = ['video_link', 'video_link', 'interval_range']
        if check_request_params(request, request_params):
            resp = {"reason": "invalid parameters"}
            return Response(resp, status=status.HTTP_400_BAD_REQUEST)
        video_link = request.data.get('video_link', None)
        interval_range = request.data.get('interval_range', None)
        result = VideoService.process_ranges(video_link, interval_range)
    except RuntimeError as ex:
        logging.error("Error : %s", ex)
        err_resp = {"reason": "Could not process" + str(ex)}
        return Response(err_resp, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return Response(result)


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def process_segments(request):
    """
    Store the Result for User Url
    """
    try:
        request_params = ['video_link', 'video_link', 'no_of_segments']
        if check_request_params(request, request_params):
            resp = {"reason": "invalid parameters"}
            return Response(resp, status=status.HTTP_400_BAD_REQUEST)
        vl = request.data.get('video_link', None)
        nos = request.data.get('no_of_segments', None)
        result = VideoService.process_segments(vl, nos)
        if result is None:
            raise ValueError("No of Segments is greater than video length ")
    except RuntimeError as ex:
        logging.error("Error : %s", ex)
        resp = {"reason": "Could not process" + str(ex)}
        return Response(resp, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return Response(result)


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def combine_video(request):
    """
    Store the Result for User Url
    """
    try:
        if request.data.get('segments', None) is None or \
                not VideoService.validate_combine(
                    request.data.get('segments', None)):
            return Response({"reason": "invalid parameters"},
                            status=status.HTTP_400_BAD_REQUEST)
        result = VideoService.combine_video(request.data.get('segments', None),
                                            request.data.get('width', None),
                                            request.data.get('height', None))
    except RuntimeError as ex:
        logging.error("Error : %s", ex)
        return Response({"reason": "Could not process" + str(ex)},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return Response(result)


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def reset_db():
    """
    View to reset the database
    """
    logger.info('Clearing directories..')
    clear_dir('/tmp')
    logger.info('Reinitializing the database..')
    DB_FILE = os.path.join(BASE_DIR, 'db.sqlite3')
    DB_RESTORE_FILE = os.path.join(BASE_DIR, 'db.sqlite3.restore')
    if os.path.exists(DB_FILE) and os.path.exists(DB_RESTORE_FILE):
        os.remove(DB_FILE)
        copyfile(DB_RESTORE_FILE, DB_FILE)
    else:
        logger.info('No reinitialization required!')
    return Response({"status": "Success"}, status=status.HTTP_202_ACCEPTED)


def clear_dir(folder):
    """
    Delete given folder
    """
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                rmtree(file_path)
        except RuntimeError as e:
            logging.error("Error : %s", e)
            raise e
