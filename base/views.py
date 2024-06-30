from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from .models import MediaInfo  # Assuming the model is named MediaInfo
from .serializers import MediaInfoSerializer  # Make sure the serializer is named correctly
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

@csrf_exempt
@api_view(['POST'])
def post_media_info(request: Request):
    """
    View to create a new MediaInfo entry in the database.
    """
    if request.method == 'POST':
        serializer = MediaInfoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@csrf_exempt
@api_view(['POST'])
def get_media_info(request: Request):

    uuid = request.data['imageName']
    hash_value = request.data['hash']
    """
    View to retrieve a MediaInfo entry from the database by primary key.
    """
    if request.method == 'POST':
        media_info = get_object_or_404(MediaInfo, pk=uuid)

        if media_info:
            serializer = MediaInfoSerializer(media_info)

            if hash_value == serializer.data['hash_value']:

                return Response('verified', status=status.HTTP_302_FOUND)
            else:
                return Response('file modified', status=status.HTTP_412_PRECONDITION_FAILED)
        else:
            return Response('files does\'t exist', status=status.HTTP_404_NOT_FOUND)