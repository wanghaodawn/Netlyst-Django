from django import forms

from django.contrib.auth.models import User

from models import *


class InfoForm(forms.ModelForm):
		class Meta:
				model = Info
				exclude = ('owner', 'followers', 'followees',' email', 'joins', 'spam', 'age', 'gender', 'smile', 'race', 'lat', 'lng')
				widgets = {'picture':forms.FileInput()}

class PasswordResetForm(forms.Form):
		password1 = forms.CharField(max_length = 200, label = 'Password', widget = forms.PasswordInput())
		password2 = forms.CharField(max_length = 200, label = 'Confirm password', widget = forms.PasswordInput())

		def clean(self):
				cleaned_data = super(PasswordResetForm,self).clean()
				password1 = cleaned_data.get('password1')
				password2 = cleaned_data.get('password2')
				if password1 and password2 and password1 != password2:
						raise forms.ValidationError("Password did not match.")
				return cleaned_data

class PasswordResetForm(forms.Form):
		password1 = forms.CharField(max_length = 200, label = 'Password', widget = forms.PasswordInput())
		password2 = forms.CharField(max_length = 200, label = 'Confirm password', widget = forms.PasswordInput())

		def clean(self):
				cleaned_data = super(PasswordResetForm,self).clean()
				password1 = cleaned_data.get('password1')
				password2 = cleaned_data.get('password2')
				if password1 and password2 and password1 != password2:
						raise forms.ValidationError("Password did not match.")
				return cleaned_data

class PostForm(forms.ModelForm):
		class Meta:
				model = Post

				exclude = ('user','date','lat','lng','liker','likenum')
				widgets = {'picture':forms.FileInput()}


class GroupForm(forms.ModelForm):
		class Meta:
				model = Group
				exclude = {'creater','members','setTime'}
				widgets ={'picture': forms.FileInput()}


class CommentForm(forms.ModelForm):
	class Meta:
			model = Comment
			fields = ('text',)








