from django.contrib.admin import site
from django.contrib import admin
from accounts.models import *
from forms import UserProfileForm

site.register(Brand)

class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm

site.register(UserProfile,UserProfileAdmin)
