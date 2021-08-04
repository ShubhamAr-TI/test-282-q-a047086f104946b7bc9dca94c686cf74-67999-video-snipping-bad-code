import logging
import os
from shutil import copyfile, rmtree

from django.http import HttpResponse
# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

import restapi.serializers
from leadsapi.settings import BASE_DIR
from restapi.services.video_service import VideoService

logger = logging.getLogger("Rest")


def index():
    return HttpResponse("Hello, world. You're at Video API.")


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def process_interval(request):
    """
    Store the Result for User Url
    """
    # Validation Service

    try:
        if request.data.get('video_link', None) is None or not VideoService.validate_video_no_of_segments(request.data.get('video_link', None),
                                                          request.data.get('interval_duration', None)):
            return Response({"reason": "invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
        result = VideoService.process_interval(request.data.get('video_link', None),  request.data.get('interval_duration', None))
    except Exception as ex:
        logging.error("Error : %s", ex)
        return Response({"reason": "Could not process" + str(ex)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return Response(result)


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def process_range(request):
    """
    Store the Result for User Url
    """

    try:
        if request.data.get('video_link', None) is None or not VideoService.validate_video_range(request.data.get('video_link', None),
                                                 request.data.get('interval_range', None)):
            return Response({"reason": "invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
        result = VideoService.process_ranges(request.data.get('video_link', None),  request.data.get('interval_range', None))
    except Exception as ex:
        logging.error("Error : %s", ex)
        return Response({"reason": "Could not process" + str(ex)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return Response(result)


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def process_segments(request):
    """
    Store the Result for User Url
    """

    try:
        if request.data.get('video_link', None) is None or not VideoService.validate_video_no_of_segments(request.data.get('video_link', None),
                                                          request.data.get('no_of_segments', None)):
            return Response({"reason": "invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
        result = VideoService.process_segments(request.data.get('video_link', None),
                                               request.data.get('no_of_segments', None))
        if result is None:
            raise ValueError("No of Segments is greater than video length ")
    except Exception as ex:
        logging.error("Error : %s", ex)
        return Response({"reason": "Could not process" + str(ex)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return Response(result)


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def combineVideo(request):
    """
    Store the Result for User Url
    """

    try:
        if request.data.get('segments', None) is None or \
                not VideoService.validate_combine(request.data.get('segments', None)):
            return Response({"reason": "invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
        result = VideoService.combine_video(request.data.get('segments', None),  request.data.get('width', None), request.data.get('height', None))
    except Exception as ex:
        logging.error("Error : %s", ex)
        return Response({"reason": "Could not process" + str(ex)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return Response(result)


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def reset_db():
    print('Clearing directories..')
    clear_dir('/tmp')
    print('Reinitializing the database..')
    DB_FILE = os.path.join(BASE_DIR, 'db.sqlite3')
    DB_RESTORE_FILE = os.path.join(BASE_DIR, 'db.sqlite3.restore')
    if os.path.exists(DB_FILE) and os.path.exists(DB_RESTORE_FILE):
        os.remove(DB_FILE)
        copyfile(DB_RESTORE_FILE, DB_FILE)
    else:
        print('No reinitialization required!')
    return Response({"status": "Success"}, status=status.HTTP_202_ACCEPTED)


def clear_dir(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                rmtree(file_path)
        except Exception as e:
            raise
