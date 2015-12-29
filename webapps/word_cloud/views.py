from django.db import models
from django.shortcuts import render
from django.template import loader, Context # Make sure you import these!

# Create your views here.
def index(request):
	context = {}
	return render(request, 'index.html', context)

def about_en_us(request):
	context = {}
	return render(request, 'about.en-US.html', context)

def about_zh_tw(request):
	context = {}
	return render(request, 'about.zh-TW.html', context)

