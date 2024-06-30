from rest_framework.serializers import ModelSerializer
from .models import MediaInfo


class MediaInfoSerializer(ModelSerializer):


    class Meta:

        model = MediaInfo
        fields = ['uuid', 'hash_value', 'timestamp']