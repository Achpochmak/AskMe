from django.core.paginator import Paginator
from django.shortcuts import render
from app import models
from app.models import Question, Answer, Tag


# Create your views here.


def pagination(request, data):
    page_num = request.GET.get('page', 1)
    paginator = Paginator(data, 5)
    try:
        if int(page_num) > paginator.num_pages or int(page_num) < 0:
            page_num = paginator.num_pages
    except:
        page_num = paginator.num_pages
    return paginator.page(page_num)


def index(request):
    page_obj = pagination(request, Question.objects.get_new())
    return render(request, "index.html", {"questions": page_obj})


def hot(request):
    page_obj = pagination(request, Question.objects.get_hot())
    return render(request, "hot.html", {"questions": page_obj})


def question(request, question_id):
    item = Question.objects.get(pk=question_id)
    answers = Answer.objects.annotate(answer_likes_count=models.Count('answerlike')).filter(question_id=question_id)
    page_obj = pagination(request, answers)
    return render(request, "question.html", {"question": item, "answers": page_obj})


def login(request):
    return render(request, "login.html")


def signup(request):
    return render(request, "signup.html")


def ask(request):
    return render(request, "ask.html")


def settings(request):
    return render(request, "settings.html")


def tag(request, tag_name):
    questions = Question.objects.get_by_tag(tag_name)
    page_obj = pagination(request, questions)
    return render(request, "tag.html", {"tag_name": tag_name, "questions": page_obj})