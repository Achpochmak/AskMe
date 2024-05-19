from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory, formset_factory
from django.utils.translation import gettext_lazy as _

from app.models import Profile, User, Test, Question, Answer, TestResult, Submission, Contest, Problem

class LoginForm(forms.Form):
    username = forms.CharField(label=_('Имя пользователя'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('Пароль'))

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label=_('Пароль'))
    confirm_password = forms.CharField(widget=forms.PasswordInput, label=_('Подтвердите пароль'))
    nickname = forms.CharField(required=False, label=_('Никнейм'))
    avatar = forms.ImageField(required=False, label=_('Аватар'))

    def clean(self):
        super().clean()
        if self.cleaned_data["password"] != self.cleaned_data['confirm_password']:
            raise ValidationError(_('Пароли не совпадают'))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        labels = {
            'username': _('Имя пользователя'),
            'first_name': _('Имя'),
            'last_name': _('Фамилия'),
            'email': _('Электронная почта'),
            'password': _('Пароль')
        }

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
    nickname = forms.CharField(required=False, label=_('Никнейм'))
    avatar = forms.ImageField(required=False, label=_('Аватар'))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': _('Имя пользователя'),
            'first_name': _('Имя'),
            'last_name': _('Фамилия'),
            'email': _('Электронная почта')
        }

    def clean(self):
        super().clean()
        if not self.cleaned_data['email']:
            raise ValidationError(_("Электронная почта не может быть пустой"))

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

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'start_time', 'end_time', 'duration_minutes', 'accessible_groups', 'max_attempts']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'title': _('Название'),
            'description': _('Описание'),
            'start_time': _('Время начала'),
            'end_time': _('Время окончания'),
            'duration_minutes': _('Продолжительность (минуты)'),
            'accessible_groups': _('Доступные группы'),
            'max_attempts': _('Максимальное количество попыток')
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_type']
        labels = {
            'question_text': _('Текст вопроса'),
            'question_type': _('Тип вопроса')
        }

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text', 'is_correct']
        labels = {
            'answer_text': _('Текст ответа'),
            'is_correct': _('Правильный ответ')
        }

AnswerFormSet = inlineformset_factory(
    Question, Answer,
    form=AnswerForm, extra=1, can_delete=True
)

QuestionFormSet = inlineformset_factory(
    Question, Answer,
    form=AnswerForm, extra=1, can_delete=True
)

QuestionWithAnswersFormSet = formset_factory(
    QuestionForm, formset=AnswerFormSet, extra=1, can_delete=True
)

class TestPassingForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = []

    def __init__(self, *args, **kwargs):
        test = kwargs.pop('test')
        print
        super(TestPassingForm, self).__init__(*args, **kwargs)
        for question in test.questions.all():
            print(question)
            if question.question_type == 'text':
                self.fields[f'question_{question.id}'] = forms.CharField(
                    label=question.question_text,
                    required=False,
                    widget=forms.TextInput(attrs={'placeholder': ''})
                )
            elif question.question_type == 'single_choice':
                self.fields[f'question_{question.id}'] = forms.ModelChoiceField(
                    queryset=Answer.objects.filter(question=question),
                    widget=forms.RadioSelect,
                    label=question.question_text,
                    required=False
                )
            elif question.question_type == 'multiple_choice':
                self.fields[f'question_{question.id}'] = forms.ModelMultipleChoiceField(
                    queryset=Answer.objects.filter(question=question),
                    widget=forms.CheckboxSelectMultiple,
                    label=question.question_text,
                    required=False
                )

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['code']
        labels = {
            'code': _('Код')
        }

class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['name', 'description', 'start_time', 'end_time', 'problems']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'name': _('Название'),
            'description': _('Описание'),
            'start_time': _('Время начала'),
            'end_time': _('Время окончания'),
            'problems': _('Задачи')
        }

class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['title', 'description', 'difficulty', 'test_cases']
        labels = {
            'title': _('Название'),
            'description': _('Описание'),
            'difficulty': _('Сложность'),
            'test_cases': _('Тестовые случаи')
        }



class JoinContestForm(forms.Form):
    contest_id = forms.IntegerField(widget=forms.HiddenInput)
