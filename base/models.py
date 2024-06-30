from django.db import models


class MediaInfo(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True)
    hash_value = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uuid
    