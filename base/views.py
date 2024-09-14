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

class PostMediaInfoView(APIView):

    permission_classes = [IsAuthenticated]
    @staticmethod
    def add_uuid(image_path):
        unique_id = str(uuid.uuid4())
        image = PILImage.open(image_path)
        exif_dict = {'Exif': {piexif.ExifIFD.UserComment: unique_id.encode('utf-8')}}
        exif_bytes = piexif.dump(exif_dict)
        image.save(image_path, "png", exif=exif_bytes)
        print(f"Image saved with UUID: {unique_id}")
        return unique_id

    @staticmethod
    def hash_image(image_path):
        with PILImage.open(image_path) as img:
            byte_arr = io.BytesIO()
            img.save(byte_arr, format='PNG')
            image_bytes = byte_arr.getvalue()

        hash_obj = hashlib.sha256()
        hash_obj.update(image_bytes)
        image_hash = hash_obj.hexdigest()
        print(f"{image_path}")
        print(f"Hash of the captured image: {image_hash}")
        return image_hash

    def post(self, request):
            print(request.user)
            serializer = MediaInfoSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                instance = serializer.save()

                image_file = request.FILES.get('image')
                image_path = self.handle_uploaded_file(image_file)
                unique_id = self.add_uuid(image_path)
                image_hash = self.hash_image(image_path)

                instance.uuid = unique_id
                instance.hash_value = image_hash
                instance.user = request.user.username
                instance.save()

                # Open the modified image to send it in the response
                with open(image_path, 'rb') as img:
                    response = HttpResponse(img.read(), content_type="image/png")
                    response['Content-Disposition'] = f'attachment; filename="{unique_id}.png"'

                print(BASE_DIR/image_path)
                # Clean up the temporary file
                os.remove(BASE_DIR/image_path)

                return response

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def handle_uploaded_file(self, f):
        temp_path = f'tmp_{uuid.uuid4()}.png'
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