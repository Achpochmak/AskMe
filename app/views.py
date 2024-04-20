from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from app import models
from django.contrib.auth.models import User
from app.forms import LoginForm, SignUpForm, AskForm, SettingsForm, AnswerForm
from app.models import Question, Answer, Tag, Profile
from django.shortcuts import render, redirect
from django.urls import reverse


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
    answers = Answer.objects.annotate(answer_likes_count=models.Count('answerlike')).filter(question_id=question_id).order_by('created_at')
    page_obj = pagination(request, answers)
    if request.method == 'POST':
        content = request.POST['content']
        print(content)
        user = request.user
        question = item
        Answer.objects.create(question=question, content=content, user=user)
        last_page_url = request.get_full_path()
        last_page_url += f"?page={page_obj.paginator.num_pages}"
        return redirect(last_page_url)
    return render(request, "question.html",
                  {"question": item, "answers": page_obj, "tags": Question.objects.get_hot_tags()[:5],
                   "users": Question.objects.get_hot_users()[:5]})


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
                return redirect(reverse('index'))
        login_form.add_error(None, "User not found")
    return render(request, "login.html", context={"form": login_form})


def logout(request):
    auth.logout(request)
    return redirect(reverse("login"))


def signup(request):
    if request.method == 'GET':
        signup_form = SignUpForm()
    if request.method == 'POST':
        signup_form = SignUpForm(data=request.POST)
        if signup_form.is_valid():
            user = signup_form.save()
            if user:
                auth.login(request, user)
                return redirect(reverse('index'))
        print('fail')
    return render(request, "signup.html", context={"form": signup_form})


@login_required(login_url="login")
def ask(request):
    if request.method == 'GET':
        ask_form = AskForm()
    if request.method == 'POST':
        ask_form = AskForm(data=request.POST)
        if ask_form.is_valid():
            title = ask_form.cleaned_data['title']
            content = ask_form.cleaned_data['content']
            tags = ask_form.cleaned_data['tags']
            user = request.user
            question = Question.objects.create(title=title, content=content, user=user)
            if question:
                for tag_input in tags.split(','):
                    if tag_input != '':
                        tag, created = Tag.objects.get_or_create(name=tag_input)
                        question.tags.add(tag)
                return redirect(reverse('question', args=[question.id]))
    return render(request, "ask.html", context={"form": ask_form})


@login_required(login_url="login")
def settings(request):
    user = request.user
    profile = Profile.objects.get(user=user.id)
    if request.method == 'GET':
        return render(request, "settings.html", context={"profile": profile})
    if request.method == 'POST':
        settings_form = SettingsForm(data=request.POST)
        if settings_form.is_valid():
            settings_form.save(user.pk)
            messages.success(request, "Profile details updated.")
    user = User.objects.get(pk=user.id)
    profile = Profile.objects.get(user=user.id)
    return render(request, "settings.html", context={"form": settings_form, "profile": profile, "user": user})


@login_required(login_url="login")
def tag(request, tag_name):
    questions = Question.objects.get_by_tag(tag_name)
    page_obj = pagination(request, questions)
    return render(request, "tag.html",
                  {"tag_name": tag_name, "questions": page_obj, "tags": Question.objects.get_hot_tags()[:5],
                   "users": Question.objects.get_hot_users()[:5]})
