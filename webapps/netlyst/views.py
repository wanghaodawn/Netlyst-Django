from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse 

# Decorator to use built-in authentication system
from django.contrib.auth.decorators import login_required

#Needed to manually create HttpResponses or raise an Http404 exception
from django.http import HttpResponse,Http404

# Used to create and manually log in a user
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate

#Helper function to guess a MIME type from a file name
from mimetypes import guess_type

# Used to send mail from within Django
from django.core.mail import send_mail

from django.contrib.auth.tokens import default_token_generator

from netlyst.models import *
from netlyst.forms import *

from time import strftime
from django.utils import timezone

import time
import json

import csv


from django.db.models import Count


#############################################################
# Face++
#############################################################
SERVER = 'http://api.us.faceplusplus.com/'
API_KEY = 'e8856d7e4db7b53bab5f36f0c0db403c'
API_SECRET = '1eiN-FmBJubicaXqVn-Ce6Uygg-WooBb'

from facepp import *

from pprint import pformat
def print_result(hint, result):
  def encode(obj):
    if type(obj) is unicode:
      return obj.encode('utf-8')
    if type(obj) is dict:
      return {encode(k): encode(v) for (k, v) in obj.iteritems()}
    if type(obj) is list:
      return [encode(i) for i in obj]
    return obj
  print hint
  result = encode(result)
  print '\n'.join(['  ' + i for i in pformat(result, width = 75).split('\n')])

@login_required
def album(request,id):
	user = get_object_or_404(User,id = id)
	posts = Post.objects.filter(user = user).order_by('-date')
	postnum = len(posts)
	login_user = request.user
	login_info = Info.objects.get(owner=request.user)
	current_info = Info.objects.get(owner=user)
	followers = current_info.followers.all()
	followees = current_info.followees.all()
	f_er_num = len(followers)
	f_ee_num = len(followees)
	if (len(login_info.followees.filter(id=id))>0):
		is_following=True
	else:
		is_following=False
	visitorinfo = visitorInfo(owner = user,visitor = request.user)
	visitorinfo.save()
	visitorinfos = visitorInfo.objects.filter(owner = user).order_by('-date') 

	info = get_object_or_404(Info,owner = user) #other user's info
	count = 0

	context = {'count':count, 'curr_user_lat':info.lat,'curr_user_lng':info.lng,'posts':posts,'is_following':is_following,'posts':posts,'current_user':user,'login_user':request.user,'info':info,'postnum':postnum,'visitorinfos':visitorinfos,'f_er_num':f_er_num,'f_ee_num':f_ee_num}
	return render(request,'album_page.html',context,)




def home_page(request):
	context = {}
	return render(request, 'home_page.html', context)

@login_required
def view_position(request):
	context = {}
	return render(request, 'view_position.html', context)



@login_required
def global_page(request):
	context = {}
	posts = Post.objects.all().order_by('-date')
	context = {'posts':posts,'current_user':request.user}

	# User recommendation
	user_info = get_object_or_404(Info,owner=request.user)
	user_followees = user_info.followees.all()

	infos = Info.objects.annotate(num_follower = Count('followers')).order_by('-num_follower')
	infos = infos.exclude(owner = user_followees)

	print(infos)
	context['infos'] = infos
	return render(request, 'global_page.html',context)



@login_required
def groupstream(request):
  all_groups = Group.objects.all()
  context = {'all_groups' : all_groups,'current_user':request.user}
  return render(request, 'groupstream.html', context)

#############################################################
# Add post
#############################################################

@login_required
def add_post(request):
	context = {}
	posts = Post.objects.all().order_by('-date')
	context['posts'] = posts
	context['current_user'] = request.user

	if request.method == "GET":
		context['form'] = PostForm()
		return render(request,'global_page.html',context)

	new_post = Post(user = request.user)
	form = PostForm(request.POST,request.FILES,instance=new_post)
	if not form.is_valid():
		context['form'] = form
		return render(request,'global_page.html',context)
	form.save()

	if request.POST['post_lat'] and request.POST['post_lng']:
		print("entered")
		new_post.lat = request.POST['post_lat']
		new_post.lng = request.POST['post_lng']

		new_post.save()

	# User recommendation
	user_info = get_object_or_404(Info,owner=request.user)
	user_followers = user_info.followers.all()
	
	infos = Info.objects.annotate(num_follower = Count('followers')).order_by('-num_follower')
	infos = infos.exclude(owner = user_followers)

	print(infos)
	context['infos'] = infos

	return redirect(reverse('global'))


#############################################################
# post in Group Stream
#############################################################
@login_required
def group_post(request, id):
    errors = []
    group=Group.objects.get(id=id)
    if not 'post' in request.POST or not request.POST['post']:
        errors.append('You must write something to post')
    else:
        current_time = time.strftime("%a, %d %b %Y %I:%M:%S %p %Z", time.localtime())
        new_post = GroupPost(post=request.POST['post'], user=request.user, created=current_time, \
            group=group)        
        new_post.save()

    posts = GroupPost.objects.filter(group=group).order_by('-created')
    #context = {'posts' : posts, 'errors' : errors}
    #return render(request, 'grumblr/group.html', context)
    path="/netlyst/get_group/"+str(id)
    return redirect(path)


#############################################################
# Create a new group in GroupStream
#############################################################
@login_required
def create_group(request):
    errors = []
    if not 'new_group' in request.POST or not request.POST['new_group']:
        errors.append('You must write something to post')
    else:
        new_group = Group(group=request.POST['new_group'],creater=request.user)
        new_group.save()
        info = get_object_or_404(Info,owner = request.user)  
        new_group.members.add(info)      
        new_group.save()

    all_groups = Group.objects.all()
    context = {'all_groups' : all_groups, 'errors' : errors,'current_user':request.user}
    return render(request, 'groupstream.html', context)


#############################################################
# Go to specified group page
#############################################################
@login_required
def get_group(request, id):
    group = Group.objects.get(id=id)
    all_posts = GroupPost.objects.filter(group=group).order_by('-created')
    login_user = Info.objects.get(owner=request.user)
    members = group.members.all();
    memlen = len(members)

    if (len(login_user.joins.filter(id=id))>0):
        is_joining=True
    else:
        is_joining=False
    return render(request, 'group.html',{'posts' : all_posts,\
            'group':group, 'login_user':login_user, 'members':members,\
            'is_joining':is_joining,'curr_user':request.user,'memlen':memlen})


#############################################################
# Join a group
#############################################################
@login_required
def join(request,id):
    group = Group.objects.get(id=id)
    login_user = Info.objects.get(owner=request.user)
    group.members.add(login_user)
    group.save()

    path="/netlyst/get_group/"+str(id)
    return redirect(path)


#############################################################
# quit a group
#############################################################
@login_required
def quit(request, id):
    login_user = Info.objects.get(owner=request.user)
    group = Group.objects.get(id=id)
    group.members.remove(login_user)
    group.save()

    path="/netlyst/get_group/"+str(id)
    return redirect(path)

#############################################################
# Follow a user
#############################################################
@login_required
def follow(request, id):
	print("XXXXXXXXXXXXX")
	current_user = User.objects.get(id=id)
	login_user = request.user
	login_info = Info.objects.get(owner=request.user)
	current_info = Info.objects.get(owner=current_user)
	login_info.followees.add(current_user)
	current_info.followers.add(login_user)
	login_info.save()
	current_info.save()
	path="/netlyst/profile/"+str(id)
	return redirect(path)


#############################################################
# Unfollow a user
#############################################################
@login_required
def unfollow(request,id):
	print("YYYYYYYYYYYYYY")
	current_user = User.objects.get(id=id)
	login_user = request.user
	login_info = Info.objects.get(owner=request.user)
	current_info = Info.objects.get(owner=current_user)
	login_info.followees.remove(current_user)
	current_info.followers.remove(login_user)
	login_info.save()
	current_info.save()
	path="/netlyst/profile/"+str(id)
	return redirect(path)


#############################################################
# Like a post
#############################################################
@login_required
def like(request,id):
		context = {}
		user = request.user
		curr_post = get_object_or_404(Post,id = id)
		posts = Post.objects.all().order_by('-date')
		curr_post.liker.add(request.user)

		likers = curr_post.liker.all()
		curr_post.likenum = len(likers)
		curr_post.save()
		context['post'] = curr_post
		

		if(len(user.like.filter(id=id))>0):
			is_like = True
		else:
			is_like = False

		context['is_like'] = is_like
		context['posts'] = posts
		context['curr_post'] = curr_post
		context['current_user'] = request.user
		return render(request,'global_page.html',context)

@login_required
def unlike(request,id):
		context = {}
		user = request.user
		curr_post = get_object_or_404(Post,id = id)
		posts = Post.objects.all().order_by('-date')
		curr_post.liker.remove(request.user)

		likers = curr_post.liker.all()
		curr_post.likenum = len(likers)
		curr_post.save()
		context['post'] = curr_post
		
		if(len(user.like.filter(id=id))>0):
			is_like = True
		else:
			is_like = False

		context['is_like'] = is_like
		context['posts'] = posts
		context['curr_post'] = curr_post
		context['current_user'] = request.user
		return render(request,'global_page.html',context)


#############################################################
# Implemented the signup_page
#############################################################
def signup_page(request):
	context = {}

	# GET is not safe enough now
	if request.method == "GET":
		return render(request,'signup_page.html',context)

	errors = []
	context['errors'] = errors

	# Username
	if not 'username' in request.POST or not request.POST['username']:
		errors.append('Username is required.')
	else:
		context['username'] = request.POST['username']
  # Email
	if not 'email' in request.POST or not request.POST['email']:
			errors.append('Email is required')
	else:
			context['email'] = request.POST['email']
	# Password
	if not 'password1' in request.POST or not request.POST['password1']:
		errors.append('Password is required.')
	if not 'password2' in request.POST or not request.POST['password2']:
		errors.append('Confirm password is required.')
	if 'password1' in request.POST and 'password2' in request.POST \
		and request.POST['password1'] and request.POST['password2'] \
		and request.POST['password1'] != request.POST['password2']:

		errors.append('Passwords does not match.')
	else:
		context['password'] = request.POST['password1']

	# Whether the username has already been taken
	if len(User.objects.filter(email = request.POST['email']))>0:
		errors.append('Email is already taken.')

	# Whether there are errors
	if errors:
		return render(request,'signup_page.html', context)

	# Create a new user
	new_user = User.objects.create_user(username = request.POST['username'],\
																			email = request.POST['email'], \
																			password = request.POST['password1'])
	new_user.save()

	login_record = loginRecord(user=new_user)
	login_record.save()

	info = Info(owner = new_user)
	info.save()

	# Let the new user log in
	new_user = authenticate(username = request.POST['username'],\
													password = request.POST['password1'])

	login(request, new_user)
	return redirect(reverse('global'))


#############################################################
# Implemented the profile_page
#############################################################
@login_required
def profile(request):
	posts = Post.objects.filter(user= request.user).order_by('-date')
	info = get_object_or_404(Info,owner = request.user)
	followers = info.followers.all()
	followees = info.followees.all()
	postnum = len(posts)
	f_er_num = len(followers)
	f_ee_num = len(followees)

	context = {'curr_user_lat':info.lat,'curr_user_lng':info.lng,'posts':posts,'current_user':request.user,'login_user':request.user,'info':info,'postnum':postnum,'f_er_num':f_er_num,'f_ee_num':f_ee_num}		

	# Save the lat and lng of posts to be shown in the map
	i = 0
	while i < postnum:
		context['post' + str(i) + '_lat'] = posts[i].lat
		context['post' + str(i) + '_lng'] = posts[i].lng
		i = i + 1

	return render(request,'profile_page.html',context)


@login_required
def viewprofile(request,id):
	context = {}
	user = get_object_or_404(User,id = id)
	posts = Post.objects.filter(user = user).order_by('-date')
	postnum = len(posts)
	login_user = request.user
	login_info = Info.objects.get(owner=request.user)
	current_info = Info.objects.get(owner=user)
	followers = current_info.followers.all()
	followees = current_info.followees.all()
	f_er_num = len(followers)
	f_ee_num = len(followees)

	if (len(login_info.followees.filter(id=id))>0):
		is_following=True
	else:
		is_following=False

	visitorinfo = visitorInfo(owner = user,visitor = request.user)
	visitorinfo.save()
	visitorinfos = visitorInfo.objects.filter(owner = user).order_by('-date') 

	info = get_object_or_404(Info,owner = user) #other user's info

	context = {'curr_user_lat':info.lat,'curr_user_lng':info.lng,'posts':posts,'is_following':is_following,'posts':posts,'current_user':user,'login_user':request.user,'info':info,'postnum':postnum,'visitorinfos':visitorinfos,'f_er_num':f_er_num,'f_ee_num':f_ee_num}
	
	# Save the lat and lng of posts to be shown in the map
	i = 0
	while i < postnum:
		context['post' + str(i) + '_lat'] = posts[i].lat
		context['post' + str(i) + '_lng'] = posts[i].lng
		i = i + 1

	return render(request,'profile_page.html',context)


@login_required
def follow_page(request,id):
	user = get_object_or_404(User,id = id)
	posts = Post.objects.filter(user = user).order_by('-date')
	login_user = request.user
	login_info = Info.objects.get(owner=request.user)
	current_info = Info.objects.get(owner=user)
	followers = current_info.followers.all()
	followees = current_info.followees.all()
	f_er_num = len(followers)
	f_ee_num = len(followees) 

	context = {'current_user':user,'login_user':request.user,'f_er_num':f_er_num,'f_ee_num':f_ee_num,\
	'followers':followers,'followees':followees}
	return render(request,'follow_page.html',context)


#############################################################
# Implemented the edit info
#############################################################
@login_required
def edit_info(request):
	context = {}
	info = get_object_or_404(Info, owner = request.user)

	if request.method == "GET":
		form = InfoForm(instance = info)
		context = {'form':form, 'curr_user': request.user.id,'info':info}
		return render(request,'editprofile.html',context)

	form = InfoForm(request.POST,request._files,instance = info)
	
	if not form.is_valid():
		context = {'form':form, 'curr_user': request.user.id,'info':info}
		return render(request,'editprofile.html',context)

	form.save()

	if info.picture:
		print("")
		print("face++ here")
		pic_url = info.picture.url
		print("pic_url_0: " + pic_url)

		# Correct the path of the avatar
		if "photo" not in pic_url:
			begin = pic_url.index("media") + 5
			pic_url = pic_url[:begin] + "/photo" + pic_url[begin:]
			print("pic_url_1: " + pic_url)

		api = API(API_KEY, API_SECRET)
		detect = api.detection.detect(url = pic_url)

		if detect['face']:
			# if the image has faces
			info.age = int(detect['face'][0]['attribute']['age']['value'])
			info.gender = detect['face'][0]['attribute']['gender']['value']
			info.race = detect['face'][0]['attribute']['race']['value']
			info.smile = int(detect['face'][0]['attribute']['smiling']['value'])
			print(detect['face'][0]['attribute'])
		else:
			# if the image has no faces
			info.age = 0
			info.gender = ""
			info.race = ""
			info.smile = 0

		info.save()
		print("face++ end")
		print("")

	return redirect(reverse('profile'), context)


@login_required
def save_user_position(request, id):
	context = {}
	info = get_object_or_404(Info, owner = request.user)

	if 'lat' in request.GET and 'lng' in request.GET:
		info.lat = request.GET['lat']
		info.lng = request.GET['lng']
		
		info.save()
		context = {'lat': info.lat, 'lng': info.lng}

	return redirect(reverse('profile'), context)


@login_required
def get_photo(request,id):
		user = get_object_or_404(User, id = id)
		info = get_object_or_404(Info, owner= user)
		if not info.picture:
				raise Http404

		content_type = guess_type(info.picture.name)
		return HttpResponse(info.picture, content_type = content_type)

@login_required
def get_postphoto(request,id):
		post = get_object_or_404(Post,id = id)
		if not post.picture:
				raise Http404

		content_type = guess_type(post.picture.name)
		return HttpResponse(post.picture, content_type = content_type)

@login_required
def visitor(request,id):
		context = {}
		user = get_object_or_404(User, id = id)

		visitorinfos = visitorInfo.objects.filter(owner = user).order_by('-date')

		context = {'visitorinfos':visitorinfos}
		return render(request,'visitorInfo.html',context)


def passwordchangeconfirm(request):
		context = {}

		if request.method == "GET":
				return render(request,'reset_password_page.html',context)

		errors = []
		context['errors'] = errors

		if not 'username' in request.POST or not request.POST['username']:
				errors.append('Username is required.')
		else:
				context['username'] = request.POST['username']

		if len(User.objects.filter(username = request.POST['username']))== 0:
				errors.append('user does not exit')
		if errors:
				return render(request,'reset_password_page.html',context)

		username = request.POST['username']
		user = User.objects.get(username = username)
		token = default_token_generator.make_token(user)
		email_body = """
		This email is comfirmation for your password change.
		http://%s%s
		"""%(request.get_host(),reverse('confirm',args=(token,username)))

		send_mail(subject = 'Password change',
							message = email_body,
							from_email = 'netlyst@gmail.com',
							recipient_list = [user.email])

		return render (request, 'password_changed_page.html',context)



def confirm (request,username,token):
		user = get_object_or_404(User,username = username)
		if not default_token_generator.check_token(user,token):
				raise Http404

		if request.method == "GET":
				form = PasswordResetForm()
				return render(request,'change_password_page.html',{'token':token,'username':username,'form':form})

		form = PasswordResetForm(request.POST)

		if not form.is_valid():
				return render(request,'change_password_page.html',{'token':token,'username':username,'form':form})

		password = form.cleaned_data['password1']
		user.set_password(password)
		user.save()
		
		return redirect(reverse('profile'))
		
		# form = PasswordResetForm(request.POST)


		# if not form.is_valid():
		# 		return render(request,'grumblr/resetpassword.html',{'token':token,'username':username,'form':form})

		# password = form.cleaned_data['password1']
		# user.set_password(password)
		# user.save()
		
		# return redirect(reverse('profile'))


#############################################################
# Implemented the login_page
#############################################################
def login_page(request):

	context = {}

	# if 'signup' in request.POST:
	# 	return render(request,'signup_page.html',context)

	# GET is not safe enough now
	if request.method == "GET":
		return render(request,'login_page.html',context)

	errors = []
	context['errors'] = errors

	# Username
	if not 'username' in request.POST or not request.POST['username']:
		errors.append('Username is required.')
	else:
		context['username'] = request.POST['username']

	# Password
	if not 'password' in request.POST or not request.POST['password']:
		errors.append('Password is required')
	else:
		context['password'] = request.POST['password']

	# Whether there are errors
	if errors:
		return render(request,'login_page.html', context)

	user = authenticate(username = request.POST['username'],\
											password = request.POST['password'])

	info = get_object_or_404(Info, owner = user)


	login_record = loginRecord(user=user)
	login_record.save()


	if info.spam > 5:
		errors.append('This account has been blocked')
		return redirect('logout')
	
	if user:
		if user.is_active:
			login(request, user)
			return redirect('global')
	else:
		errors.append('This account does not exist')
	
	return render(request, 'login_page.html', context)


@login_required
def report_spam(request, id):
	print("Begin report_spam")
	context = {};
	user = get_object_or_404(User,id = id)
	info = get_object_or_404(Info, owner = user)

	spam = info.spam
	info.spam = spam + 1
	info.save()

	print("End report_spam")
	return redirect('global')


@login_required
def post_pos_val(request, id):
	print("begin post_pos_val")
	post = get_object_or_404(Post, id = id)

	print(id)
	print(request.GET)

	print(post)
	user = request.user
	context = {}
	context['post'] = post
	context['current_user'] = user

	print(post.lat)
	print(post.lng)

	print("end post_pos_val")
	return render(request, 'post_pos_val.html', context)


def word_cloud(request):
	context = {}
	return render(request, 'word_cloud.html', context)

@login_required
def get_group_info(request,id):
	group = get_object_or_404(Group,id = id)
	members = group.members.all()
	context = {'group_id':id,'members':members}
	return render(request,'club.json',context,content_type='application/json')

@login_required
def get_group_info_all(request):
	users = User.objects.all()
	infos = Info.objects.all()
	groups = Group.objects.all()
	context = {'users':users,'infos':infos,'groups':groups}
	return render(request,'club_all.json',context,content_type='application/json')

@login_required
def test(request):
	context = {}
	return render(request,'club_info.html', context)


@login_required
def search_user(request):
	context = {}
	errors = []
	context['errors'] = errors
	username = request.POST['search']
	if len(User.objects.filter(username = username)) < 0:
		errors.append('There is no such user')
		return render(request, 'search_user.html', context)

	user = get_object_or_404(User, username = username)
	posts = Post.objects.filter(user = user).order_by("-date")
	postnum = len(posts)
	info = get_object_or_404(Info, owner = user)
	context['user'] = user
	context['posts'] = posts
	context['info'] = info
	context['postnum'] = postnum
	return render(request,'search_user.html',context)



#############################################################
# Edit a group's infomation
#############################################################
@login_required
def edit_group(request, id):
	context = {}
	group = get_object_or_404(Group,id = id)
	if request.method == "GET":
		form = GroupForm(instance = group)
		context = {'form':form}
		context['group'] = group
		return render(request,'edit_group.html',context)
	form = GroupForm(request.POST, request._files, instance = group)
	if not form.is_valid():
		context = {'form':form}
		return render(request, 'edit_group.html', context)
	form.save()
	return redirect(reverse('get_group',args=[str(group.id)]))


#############################################################
# get group photo
#############################################################
@login_required
def get_group_photo(request,id):
	group = get_object_or_404(Group,id = id)
	if not group.picture:
		raise Http404
	content_type = guess_type(group.picture.name)
	return HttpResponse(group.picture, content_type = content_type)




@login_required
def some_view(request):
		info_1 = Info.objects.filter(age__range=["0", "20"])
		info_2 = Info.objects.filter(age__range=["21","30"])
		info_3 = Info.objects.filter(age__range=["31","40"])
		info_4 = Info.objects.filter(age__range=["41","50"])
		# Create the HttpResponse object with the appropriate CSV header.
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="data.csv"'

		num_1 = len(info_1)
		num_2 = len(info_2)
		num_3 = len(info_3)
		num_4 = len(info_4)

		writer = csv.writer(response)
		writer.writerow(['age', 'population'])
		writer.writerow(['0-20', num_1])
		writer.writerow(['21-30', num_2])
		writer.writerow(['31-40', num_3])
		writer.writerow(['41-50', num_4])

		return response

@login_required
def age_distribution(request):
		return render(request,'age_distribution.html')
@login_required
def gender_distribution(request):
		return render(request,'gender_distribution.html')

@login_required
def gender(request):
		# Create the HttpResponse object with the appropriate CSV header.
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="gender.csv"'
		info_f = Info.objects.filter(gender="Female")
		info_m = Info.objects.filter(gender="Male")
		num_f = len(info_f)
		num_m = len(info_m)
		writer = csv.writer(response)
		writer.writerow(['age', 'population'])
		writer.writerow(['Female', num_f])
		writer.writerow(['Male', num_m])

		return response

@login_required
def global_distribution(request):
	context = {}
	current_user = request.user
	context['current_user'] = current_user
	return render(request,'global_distribution.html',context)


@login_required
def calender(request,id):

		user = get_object_or_404(User,id=id)
		login_records = loginRecord.objects.filter(user=user)\
																.extra({'date':"date(date)"})\
																.values('date')\
																.annotate(created_count=Count('id'))
		
		# Create the HttpResponse object with the appropriate CSV header.
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="calender.csv"'

		writer = csv.writer(response)
		writer.writerow(['Date', 'Open'])
		writer.writerow(['2015-04-26', '1'])
		writer.writerow(['2015-05-03', '5'])
		writer.writerow(['2015-05-10', '10'])
		writer.writerow(['2015-05-17', '20'])
		writer.writerow(['2015-05-24', '30'])
		writer.writerow(['2015-05-31', '40'])
		writer.writerow(['2015-06-07', '50'])
		for i in range(0,len(login_records)):
			writer.writerow([login_records[i]['date'], login_records[i]['created_count']])

		return response


@login_required
def get_follower_graph(request,id):
	context = {}
	user = get_object_or_404(User,id=id)
	info = get_object_or_404(Info,owner=user)
	followers = info.followers.all()

	context['user'] = user
	context['followers'] = followers
	context['len'] = len(followers)

	return render(request,'follower.json',context,content_type='application/json')


@login_required
def get_followee_graph(request,id):
	context = {}
	user = get_object_or_404(User,id=id)
	info = get_object_or_404(Info,owner=user)
	followees = info.followees.all()

	context['user'] = user
	context['followees'] = followees
	context['len'] = len(followees)

	return render(request,'followee.json',context,content_type='application/json')

@login_required
def follower_visual(request,id):
	context = {}
	current_user = get_object_or_404(User,id=id)
	context['current_user'] = current_user
	return render(request,'follower_visual.html',context)

@login_required
def followee_visual(request,id):
	context = {}
	current_user = get_object_or_404(User,id=id)
	context['current_user'] = current_user
	return render(request,'followee_visual.html',context)




@login_required
def post_record(request):
		print("endterd post_record")
		posts = Post.objects.all()\
																.annotate(created_count=Count('id'))
		# Create the HttpResponse object with the appropriate CSV header.
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="post_record.tsv"'

		writer = csv.writer(response)
		writer.writerow(['day' '	' 'hour' '	' 'value'])

		day = []
		hour = []
		for post in posts:
			post_date = str(post.date)
			day.append(post_date[8:10])
			hour.append(post_date[11:13])
		print(day)
		print(hour)

		# Set day and hour array
		i = 0
		count = 1
		for post in posts:
			if i > 0:
				if day[i] == day[i-1] and hour[i] == hour[i-1]:
					count = count + 1
				else:
					writer.writerow([str(day[i-1]) +'	'+ str(hour[i-1]) +'	'+ str(count)])
					count = 1
			i = i + 1

		# Write to the file and update the count
		if i > 1:
			if day[i-1] == day[i-2] and hour[i-1] == hour[i-2]:
				count = count + 1
			else:
				writer.writerow([str(day[i-1]) +'	'+ str(hour[i-1]) +'	'+ str(count)])
				count = 1

		return response






