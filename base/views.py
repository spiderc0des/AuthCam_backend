from rest_framework.views import APIView
from rest_framework.response import Response
from django.http.response import HttpResponse
from rest_framework import status
from .serializers import MediaInfoSerializer
import uuid
import piexif
from PIL import Image as PILImage
import hashlib
import io
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user
import os
from .models import MediaInfo
from authcam.settings import BASE_DIR
from django.conf import settings



class PostMediaInfoView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def add_uuid(image_path):
        unique_id = str(uuid.uuid4())
        image = PILImage.open(image_path)
        exif_dict = {'Exif': {piexif.ExifIFD.UserComment: unique_id.encode('utf-8')}}
        exif_bytes = piexif.dump(exif_dict)
        modified_image_path = f"{os.path.splitext(image_path)[0]}_{unique_id}.png"
        image.save(modified_image_path, "png", exif=exif_bytes)
        return unique_id, modified_image_path

    @staticmethod
    def hash_image(image_path):
        with PILImage.open(image_path) as img:
            byte_arr = io.BytesIO()
            img.save(byte_arr, format='PNG')
            image_bytes = byte_arr.getvalue()
        hash_obj = hashlib.sha256()
        hash_obj.update(image_bytes)
        image_hash = hash_obj.hexdigest()
        return image_hash

    def post(self, request):
        serializer = MediaInfoSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            image_file = request.FILES.get('image')
            image_path = self.handle_uploaded_file(image_file)
            unique_id, modified_image_path = self.add_uuid(image_path)  # Get both unique ID and the path of the modified image
            image_hash = self.hash_image(modified_image_path)  # Make sure to hash the modified image

            instance.uuid = unique_id
            instance.hash_value = image_hash
            instance.user = request.user.username
            instance.save()

            image_url = request.build_absolute_uri(f'{settings.MEDIA_URL}processed_images/{os.path.basename(modified_image_path)}')

            # Clean up the temporary file if needed
            # os.remove(modified_image_path)

            return Response({'url': image_url}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def handle_uploaded_file(self, f):
        temp_path = os.path.join(settings.MEDIA_ROOT, f'processed_images/{uuid.uuid4()}.png')
        with open(temp_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        return temp_path



class VerifyMediaInfoView(APIView):
    permission_classes = [IsAuthenticated]  # Assuming you want the endpoint to be protected

    def post(self, request):
        # Get the uploaded image
        image_file = request.FILES.get('image')
        if not image_file:
            return Response("No image provided.", status=status.HTTP_400_BAD_REQUEST)

        image_path = self.handle_uploaded_file(image_file)
        retrieved_uuid = self.retrieve_uuid(image_path)
        rehashed_value = self.hash_image(image_path)

        # Attempt to retrieve the corresponding MediaInfo object from the database
        try:
            media_info = MediaInfo.objects.get(uuid=retrieved_uuid)
        except MediaInfo.DoesNotExist:
            return Response("Media file not found in the database.", status=status.HTTP_404_NOT_FOUND)

        # Verify hash
        if rehashed_value == media_info.hash_value:
            return Response("Media file is authentic", status=status.HTTP_200_OK)
        else:
            return Response("Media file has been modified", status=status.HTTP_412_PRECONDITION_FAILED)

    @staticmethod
    def handle_uploaded_file(f):
        temp_path = f'tmp_{uuid.uuid4()}.png'
        with open(temp_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        return temp_path

    @staticmethod
    def retrieve_uuid(image_path):
        img = PILImage.open(image_path)
        if 'exif' in img.info:
            exif_data = piexif.load(img.info['exif'])
            if piexif.ExifIFD.UserComment in exif_data['Exif']:
                user_comment = exif_data['Exif'][piexif.ExifIFD.UserComment]
                unique_id = user_comment.decode('utf-8')
                img.close()
                return unique_id
            img.close()
        return None

    @staticmethod
    def hash_image(image_path):
        with PILImage.open(image_path) as img:
            byte_arr = io.BytesIO()
            img.save(byte_arr, format='PNG')
            image_bytes = byte_arr.getvalue()

        hash_obj = hashlib.sha256()
        hash_obj.update(image_bytes)
        return hash_obj.hexdigest()