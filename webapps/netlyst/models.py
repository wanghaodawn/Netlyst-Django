from django.db import models

# User class for built-in authentication module
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Max


class Post(models.Model):
		text = models.CharField(max_length=200)
		user = models.ForeignKey(User)
		date = models.DateTimeField(auto_now_add=True, blank=True)
		picture = models.ImageField(upload_to="postphoto",blank=True)
		lat = models.CharField(max_length=20,blank = True)
		lng = models.CharField(max_length=20,blank = True)
		liker = models.ManyToManyField(User,related_name = 'like')
		likenum = models.IntegerField(default = 0)


		def __unicode__(self):
				return self.text

		# Returns all recent additions and deletions to the to-do list.
		@staticmethod
		def get_changes(logentry_id = -1):
			return Post.objects.filter(logentry__gt = logentry_id).distinct()

		# Returns all recent additions to the to-do list.
		@staticmethod
		def get_posts(logentry_id = -1):
			return Post.objects.filter(logentry__gt = logentry_id).distinct()

		# Generates the HTML-representation of a post
		@property
		def html(self):
			result  = "<a href='profile/%d'> %s </a>" % (self.user.id, self.user.username)
			result += "<img src='photo/%d' height='100px'> </a>" % (self.user.id)
			result += "<div class='p2'>%s %s</div><br />" % (self.text, self.date.strftime('%m/%d/%y %H:%M:%S'))
			result += "<img src='postphoto/%d' height='100px'> </a>" % (self.id)
			result += "<ol id = 'comment_list_%d' ></ol>" % (self.id)
			result += "<div class = 'p2'><input id='comment_field_%d' type='text'>" % (self.id)
			result += "<button id ='add_comment_button' btn-id= %d >add comment</button></div>" % (self.id)
			result += "<br /><br />"
			return result
			
		@property
		def get_comments(self):
			return Comment.objects.filter(post_owner = self.user)

class Info(models.Model):
		owner = models.OneToOneField(User)
		first_name = models.CharField(max_length = 200, blank=True)
		last_name = models.CharField(max_length = 200, blank=True)
		bio = models.CharField(max_length = 420, blank=True)
		email = models.EmailField()
		picture = models.ImageField(upload_to="photo",blank=True, null=True)
		followers = models.ManyToManyField(User,related_name = "followers")
		followees = models.ManyToManyField(User,related_name = "followees")

		lat = models.CharField(max_length=20, blank = True)
		lng = models.CharField(max_length=20, blank = True)

		spam = models.IntegerField(default = 0)

		age = models.IntegerField(default = 0, blank = True)
		gender = models.CharField(max_length = 10, blank = True)
		smile = models.IntegerField(default = 0, blank = True)
		race = models.CharField(max_length = 10, blank = True)

		def __unicode__(self):
			return self.owner.username

		@staticmethod
		def get_infos(user):
				return Info.objects.get(user=user)
				
class Group(models.Model):
	creater = models.ForeignKey(User,null=True)
	group = models.CharField(max_length=20, default='',blank=True)
	picture = models.ImageField(upload_to="groupphoto",blank=True,null=True)
	setTime = models.DateTimeField(auto_now_add=True, blank=True,null=True)
	description = models.CharField(max_length = 420,blank=True)
	members = models.ManyToManyField(Info, related_name="joins")
	def __unicode__(self):
		return self.group

class GroupPost(models.Model):
	post = models.CharField(max_length=200)
   	user = models.ForeignKey(User)
	group = models.ForeignKey(Group)
	created = models.CharField(max_length=25) 
	def __unicode__(self):
		return self.post

class visitorInfo(models.Model): 
		owner = models.ForeignKey(User) 
		visitor = models.ForeignKey(User,related_name = "visitor") 
		date = models.DateTimeField(auto_now_add=True, blank=True)


class loginRecord(models.Model):
		user = models.ForeignKey(User)
		date = models.DateTimeField(auto_now_add=True, blank=True)

# A LogEntry implicitly records when a psot is added and deleted, though its auto-increment id.
class LogEntry(models.Model):
	post = models.ForeignKey(Post)
	
	def __unicode__(self):
		return "LogEntry (%d, %s)" % (self.id, self.post)
	def __str__(self):
		return self.__unicode__()

	# Gets the id of the most recent LogEntry
	@staticmethod
	def get_max_id():
		return LogEntry.objects.all().aggregate(Max('id'))['id__max'] or 0



class Comment(models.Model):
	text = models.CharField(max_length = 100)
	post_owner = models.ForeignKey(Post)
	comment_owner = models.ForeignKey(User)
	date = models.DateTimeField(auto_now_add = True, blank = True)

	def __unicode__(self):
		return self.text

	# Generates the HTML-representation of a post
	@property
	def html(self):
		result  = "<a href='profile/%d'>" % (self.comment_owner.id)
		result += "<img src='photo/%d' height='100px'> </a>" % (self.comment_owner.id)
		result += "<div class='p2'>%s %s %s</div><br />" \
		  % (self.text, self.date.strftime('%m/%d/%y %H:%M:%S'), self.comment_owner)
		return result












