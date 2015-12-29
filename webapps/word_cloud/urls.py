from django.conf.urls import patterns,include, url

urlpatterns = [
		url(r'^$','word_cloud.views.index'),
		url(r'about_en_us^$','word_cloud.views.about_en_us'),
		url(r'about_zh_tw^$','word_cloud.views.about_zh_tw'),
]
