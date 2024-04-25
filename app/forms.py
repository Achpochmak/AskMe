from django import forms
from django.core.exceptions import ValidationError

from app.models import Profile, User, Question, Tag


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class AskForm(forms.Form):
    title = forms.CharField(error_messages={
        'required': 'Please enter your question'})
    content = forms.CharField(error_messages={
        'required': 'Please enter your content'})
    tags = forms.CharField(required=False)

    def clean(self):
        super().clean()

    def save(self, request):
        title = self.cleaned_data['title']
        content = self.cleaned_data['content']
        tags = self.cleaned_data['tags']
        user = request.user
        question = Question.objects.create(title=title, content=content, user=user)
        if question:
            for tag_input in tags.split(','):
                if tag_input != '':
                    tag, created = Tag.objects.get_or_create(name=tag_input)
                    question.tags.add(tag)
            question.save()


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    nickname = forms.CharField(required=False)
    avatar = forms.ImageField(required=False)

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
        received_avatar = self.cleaned_data["avatar"]
        received_nickname = self.cleaned_data.get('nickname')
        user.save()
        profile = Profile.objects.create(user=user, nickname=received_nickname)
        if received_avatar:
            profile.avatar = received_avatar
        profile.save()
        return user


class SettingsForm(forms.ModelForm):
    nickname = forms.CharField(required=False)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean(self):
        super().clean()
        if not self.cleaned_data['email']:
            raise ValidationError("email can't be empty")

    def save(self, **kwargs):
        user = super().save(**kwargs)
        profile = user.profile
        received_avatar = self.cleaned_data.get('avatar')
        if received_avatar:
            profile.avatar = self.cleaned_data.get('avatar')
        received_nickname = self.cleaned_data.get('nickname')
        if received_nickname:
            profile.nickname = self.cleaned_data.get('nickname')
        profile.save()
        return user


class AnswerForm(forms.Form):
    content = forms.CharField(required=True)

    def clean(self):
        super().clean()
