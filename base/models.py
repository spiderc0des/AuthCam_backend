from django.db import models


class MediaInfo(models.Model):
    user = models.CharField(max_length=10, null=False)
    uuid = models.CharField(max_length=100, null=False)
    hash_value = models.CharField(max_length=64)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'{self.uuid} {self.timestamp}'