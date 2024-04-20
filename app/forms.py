from django import forms
from django.core.exceptions import ValidationError

from app.models import Profile, User


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class AskForm(forms.Form):
    title = forms.CharField(required=False)
    content = forms.CharField(required=False)
    tags = forms.CharField(required=False)

    def clean(self):
        super().clean()
        print(self.cleaned_data)
        if not self.cleaned_data['title']:
            raise ValidationError('Wrong data')


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        super().clean()
        if self.cleaned_data["password"] != self.cleaned_data['confirm_password']:
            raise ValidationError('Confirm password')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.save()
        return user


class SettingsForm(forms.Form):
    username = forms.CharField(required=False)
    email = forms.CharField(required=False)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    nickname = forms.CharField(required=False)
    avatar = forms.ImageField(required=False)

    def clean(self):
        super().clean()
        if not self.cleaned_data['username']:
            raise ValidationError('Wrong data')


    def save(self, user_id, commit=True):
        cleaned_data = self.cleaned_data
        user = User.objects.get(pk=user_id)
        for field in ['first_name', 'last_name', 'email', 'username']:
            setattr(user, field, cleaned_data.get(field))
        user.save()

        profile = Profile.objects.get(user=user)
        for field in ['nickname', 'avatar']:
            setattr(profile, field, cleaned_data.get(field))
        profile.save()


class AnswerForm(forms.Form):
    content = forms.CharField(required=False)

    def clean(self):
        super().clean()



