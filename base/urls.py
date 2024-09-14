from django.urls import include, path
from .views import *

urlpatterns = [
    path('upload/', view=PostMediaInfoView.as_view()),
    path('verify/', view=VerifyMediaInfoView.as_view()),

]