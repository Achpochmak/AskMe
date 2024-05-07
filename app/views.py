import time

from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from app import models
from app.forms import LoginForm, SignUpForm, AskForm, SettingsForm, AnswerForm, MemberForm
from app.models import Question, Answer, Tag, Profile, QuestionLike, AnswerLike
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings as conf_settings
import json
import jwt
from cent import Client, PublishRequest

client = Client(api_url=conf_settings.CENTRIFUGO_API_URL, api_key=conf_settings.CENTRIFUGO_API_KEY)


def get_centrifugo_data(user_id, channel):
    return {
        "centrifugo": {
            "token": jwt.encode(
                {"sub": str(user_id), "exp": int(time.time()) + 10 * 60},
                conf_settings.CENTRIFUGO_TOKEN_HMAC_SECRET_KEY,
                algorithm="HS256",
            ),
            "ws_url": conf_settings.CENTRIFUGO_WS_URL,
            "channel": channel
        }
    }


def pagination(request, data):
    page_num = request.GET.get('page', 1)
    paginator = Paginator(data, 5)
    try:
        if int(page_num) > paginator.num_pages or int(page_num) < 0:
            page_num = paginator.num_pages
    except:
        page_num = paginator.num_pages
    return paginator.page(page_num)


@login_required(login_url="login")
def index(request):
    page_obj = pagination(request, Question.objects.get_new())
    return render(request, "index.html", {"questions": page_obj, "tags": Question.objects.get_hot_tags()[:5],
                                          "users": Question.objects.get_hot_users()[:5]})


@login_required(login_url="login")
def hot(request):
    page_obj = pagination(request, Question.objects.get_hot())
    return render(request, "hot.html", {"questions": page_obj, "tags": Question.objects.get_hot_tags()[:5],
                                        "users": Question.objects.get_hot_users()[:5]})


@login_required(login_url="login")
def question(request, question_id):
    item = Question.objects.annotate(question_likes_count=models.Count('questionlike')).get(pk=question_id)
    answers = Answer.objects.annotate(answer_likes_count=models.Count('answerlike')).filter(
        question_id=question_id).order_by('created_at')
    page_obj = pagination(request, answers)
    if request.method == 'POST':
        answer = Answer.objects.create(question=item, content=request.POST['content'], user=request.user)
        answer.save()
        publish_request = PublishRequest(channel=f'question{question_id}', data=model_to_dict(answer))
        client.publish(publish_request)
        page_obj = pagination(request, answers)
        last_page_url = request.get_full_path() + f"?page={page_obj.paginator.num_pages}"
        return redirect(last_page_url)
    return render(request, "question.html",
                  {"question": item, "answers": page_obj, "tags": Question.objects.get_hot_tags()[:5],
                   "users": Question.objects.get_hot_users()[:5], **get_centrifugo_data(request.user.id, f'question{question_id}')})


@require_http_methods(['GET', 'POST'])
def login(request):
    if request.method == 'GET':
        login_form = LoginForm()
    if request.method == 'POST':
        login_form = LoginForm(data=request.POST)
        if login_form.is_valid():
            user = authenticate(request, **login_form.cleaned_data)
            if user:
                auth.login(request, user)
                next_url = request.POST.get('next')
                return redirect(next_url)
        login_form.add_error(None, "User not found")
    return render(request, "login.html", context={"form": login_form})


def logout(request):
    auth.logout(request)
    return redirect(reverse("login"))


def signup(request):
    if request.method == 'GET':
        signup_form = SignUpForm()
    if request.method == 'POST':
        signup_form = SignUpForm(data=request.POST, files=request.FILES)
        if signup_form.is_valid():
            user = signup_form.save()
            if user:
                auth.login(request, user)
                return redirect(reverse('index'))
    return render(request, "signup.html", context={"form": signup_form})


@login_required(login_url="login")
def ask(request):
    if request.method == 'GET':
        ask_form = AskForm()
    if request.method == 'POST':
        ask_form = AskForm(data=request.POST)
        if ask_form.is_valid():
            ask_form.save(request)
            question = Question.objects.filter(user=request.user).latest('created_at')
            return redirect(reverse('question', args=[question.id]))
    return render(request, "ask.html", context={"form": ask_form})


@login_required(login_url="login")
def settings(request):
    user = request.user
    profile = Profile.objects.get(user=user.id)
    dict = model_to_dict(user)
    dict['avatar'] = profile.avatar
    dict['nickname'] = profile.nickname
    if request.method == 'GET':
        settings_form = SettingsForm(initial=dict)
    if request.method == 'POST':
        settings_form = SettingsForm(request.POST, request.FILES, instance=user)
        if settings_form.is_valid():
            settings_form.save()
    return render(request, "settings.html", context={"form": settings_form})
@login_required(login_url="login")
def member(request, user_id):
    profile = Profile.objects.get(user=user_id)
    user=profile.user
    dict = model_to_dict(user)
    dict['avatar'] = profile.avatar
    dict['nickname'] = profile.nickname
    if request.method == 'GET':
        member_form = MemberForm(initial=dict)
    if request.method == 'POST':
        settings_form = SettingsForm(request.POST, request.FILES, instance=user)
        if settings_form.is_valid():
            settings_form.save()
    return render(request, "member.html", context={"form": member_form})


@login_required(login_url="login")
def tag(request, tag_name):
    questions = Question.objects.get_by_tag(tag_name)
    page_obj = pagination(request, questions)
    return render(request, "tag.html",
                  {"tag_name": tag_name, "questions": page_obj, "tags": Question.objects.get_hot_tags()[:5],
                   "users": Question.objects.get_hot_users()[:5]})


@login_required(login_url="login")
def like(request):
    data = json.loads(request.body.decode("utf-8"))
    if data['type'] == 'question':
        count = QuestionLike.objects.toggle_like(user=request.user, id=data['id'])
    elif data['type'] == 'answer':
        count = AnswerLike.objects.toggle_like(user=request.user, id=data['id'])
    return JsonResponse({'key': count})


@login_required(login_url="login")
def correct_answer(request):
    data = json.loads(request.body.decode("utf-8"))
    answer = get_object_or_404(Answer, id=data['id'])
    if answer.question.user == request.user:
        answer.correct = not answer.correct
        answer.save()
        if answer.correct:
            return JsonResponse({'key': "True"})
    return JsonResponse({'key': "false"})
