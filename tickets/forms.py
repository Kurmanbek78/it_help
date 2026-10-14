from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Comment, Ticket, User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ("title", "description", "room", "priority")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        widgets = {"text": forms.Textarea(attrs={"rows": 3})}