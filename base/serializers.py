from rest_framework import serializers
from .models import MediaInfo
from PIL import Image


class MediaInfoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True)  # Adjust based on your file type, e.g., FileField

    class Meta:
        model = MediaInfo
        fields = ['user', 'uuid', 'hash_value', 'image']
        read_only_fields = ['uuid', 'hash_value', 'user', 'timestamp']

    def validate_image(self, value):
        try:
            img = Image.open(value)
            img.verify()  # Verifies that the file is not corrupted
        except Exception as e:
            raise serializers.ValidationError(f"Invalid image file: {str(e)}")
        return value

    def create(self, validated_data):
        # Remove the file from validated_data since it's write-only and not part of the model
        validated_data.pop('image', None)
        return super().create(validated_data)