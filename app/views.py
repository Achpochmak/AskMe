import logging
import os
import subprocess
import time
from datetime import timezone
from venv import logger
import datetime

import docker
import psutil
from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Sum
from django.forms.models import model_to_dict, inlineformset_factory, modelformset_factory
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from app import models
from app.forms import LoginForm, SignUpForm, SettingsForm, TestForm, QuestionForm, QuestionFormSet, AnswerFormSet, \
    TestPassingForm, AnswerForm, SubmissionForm, ContestForm, ProblemForm, JoinContestForm
from app.models import Profile, Test, Answer, Question, TestResult, QuestionResult, Message, Problem, \
    ContestParticipant, Contest, SubmissionAttempt, Teacher, Submission
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings as conf_settings
import json
import jwt
from cent import Client, PublishRequest
from datetime import *
from django.utils import timezone
from utils import run_code_in_docker

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
    if Teacher.objects.filter(user=request.user).exists():
        page_obj = pagination(request, Test.objects.filter(teacher__user=request.user, end_time__gte=timezone.now()))
    else:
        page_obj = pagination(request, Test.objects.filter(end_time__gte=timezone.now()))

    # Найти преподавателей, ведущих у ученика
    student_groups = request.user.student.group
    teachers = Teacher.objects.all()
    print(teachers, student_groups)
    return render(request, "index.html", {"tests": page_obj, "teachers": teachers})


@login_required(login_url="login")
def archive(request):
    archived_tests = Test.objects.filter(end_time__lt=timezone.now())
    page_obj = pagination(request, archived_tests)

    tests_data = []

    for test in page_obj:
        question_statistics = []
        question_texts = []
        correct_answers_counts = []
        incorrect_answers_counts = []

        for question in test.questions.all():
            question_results = QuestionResult.objects.filter(question=question)
            total_answers = question_results.count()

            correct_answers = question_results.filter(selected_answers__is_correct=True).count()
            incorrect_answers = total_answers - correct_answers

            question_statistics.append({
                'question_text': question.question_text,
                'total_answers': total_answers,
                'correct_answers': correct_answers,
                'incorrect_answers': incorrect_answers,
            })
            question_texts.append(question.question_text)
            correct_answers_counts.append(correct_answers)
            incorrect_answers_counts.append(incorrect_answers)

        # Plot the statistics for each test
        plt.figure(figsize=(10, 6))
        bar_width = 0.35
        index = range(len(question_texts))

        plt.bar(index, correct_answers_counts, bar_width, label='Correct Answers')
        plt.bar(index, incorrect_answers_counts, bar_width, bottom=correct_answers_counts, label='Incorrect Answers')

        plt.xlabel('Questions')
        plt.ylabel('Number of Answers')
        plt.title(f'Question Statistics for Test: {test.title}')
        plt.xticks(index, question_texts, rotation=45, ha='right')
        plt.legend()

        # Save the plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()

        tests_data.append({
            'test': test,
            'question_statistics': question_statistics,
            'graph': image_base64,
        })

    context = {
        'tests': page_obj,
        'tests_data': tests_data,
    }
    return render(request, "archive.html", context)


@login_required(login_url="login")
def student_search(request):
    query = request.GET.get('q')
    if query:
        students = User.objects.filter(first_name__icontains=query).distinct()
    else:
        students = []
    print(students)
    return render(request, "student_search.html", {"students": students, "query": query})


from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Test, Question, Answer, TestResult, QuestionResult, Teacher
from .forms import TestPassingForm


def test(request, test_id):
    test = Test.objects.get(pk=test_id)
    user = request.user
    current_time = timezone.now()
    if request.method == 'POST':
        form = TestPassingForm(request.POST, test=test)
        if form.is_valid():
            test_result = form.save(commit=False)
            test_result.user = request.user
            test_result.test = test
            test_result.save()

            correct_answers_count = 0
            incorrect_answers_count = 0

            for question in test.questions.all():
                selected_answers = form.cleaned_data.get(f'question_{question.id}', None)
                if selected_answers is not None:
                    question_result = QuestionResult.objects.create(test_result=test_result, question=question)
                    question_result.selected_answers.set(selected_answers)

                    for answer in selected_answers:
                        if answer.is_correct:
                            correct_answers_count += 1
                        else:
                            incorrect_answers_count += 1
                else:
                    # Если на вопрос не был дан ответ, считаем его как неправильный
                    incorrect_answers_count += 1

            test_result.correct_answers_count = correct_answers_count
            test_result.incorrect_answers_count = incorrect_answers_count
            test_result.save()

            return redirect('test_result', test_result_id=test_result.id)
    else:
        if Teacher.objects.all().filter(user=request.user):
            print('teacher')
            return redirect('edit_test', test_id=test.id)
            # Проверка количества попыток
        attempts = TestResult.objects.filter(test=test, user=user).count()
        if attempts >= test.max_attempts:
            return render(request, 'test_access_denied.html', {'reason': 'attempts_exceeded'})

        # Проверка времени начала и окончания теста
        if current_time < test.start_time:
            return render(request, 'test_access_denied.html', {'reason': 'test_not_started'})
        elif current_time > test.end_time:
            return render(request, 'test_access_denied.html', {'reason': 'test_ended'})
        form = TestPassingForm(test=test)
    return render(request, 'test.html', {'form': form, "test": test})


def create_test(request):
    if request.method == 'POST':
        test_form = TestForm(request.POST)
        if test_form.is_valid():
            test = test_form.save(commit=False)
            test.save()

            keys = request.POST.keys()

            num_questions = 0

            question_indices = set()

            for key in keys:
                if key.startswith('questions-'):
                    index = key.split('-')[1]
                    question_indices.add(index)

            num_questions = len(question_indices)
            for i in range(num_questions):
                question_text = request.POST.getlist(f'questions-{i}-question_text')[0]
                question_type = request.POST.getlist(f'questions-{i}-question_type')[0]

                question = Question.objects.create(
                    question_text=question_text,
                    question_type=question_type,

                    test=test
                )
                if question_type == 'text':
                    num_answers = 1
                else:
                    num_answers = int(request.POST.getlist(f'questions-{i}-num_answers')[0])

                for j in range(num_answers):
                    answer_text = request.POST.getlist(f'questions-{i}-answer_{j}')[0]
                    print(request.POST.get(f'questions-{i}-answers_{j}'))
                    if question_type == 'text':
                        is_correct = True
                    else:
                        is_correct = request.POST.get(f'questions-{i}-answers_{j}') == 'on'
                    Answer.objects.create(
                        question=question,
                        answer_text=answer_text,
                        is_correct=is_correct
                    )

            messages.success(request, 'Test created successfully.')
            return redirect('index')
        else:
            messages.error(request, 'Form submission failed. Please check the provided data.')
    else:
        test_form = TestForm()

    context = {
        'test_form': test_form,
    }

    return render(request, 'create_test.html', context)


def view_test_result(request, test_result_id):
    test_result = get_object_or_404(TestResult, pk=test_result_id)
    return render(request, 'test_result.html', {'test_result': test_result})


def generate_room_name(user1, user2):
    # Сортируем идентификаторы пользователей, чтобы порядок не имел значения
    user_ids = sorted([user1.id, user2.id])
    return f'room_{user_ids[0]}_{user_ids[1]}'


def get_room_name(user1_id, user2_id):
    return f'room_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}'


def room(request, user_id):
    current_user_id = request.user.id  # Предполагается, что текущий пользователь аутентифицирован
    room_name = get_room_name(current_user_id, user_id)
    messages = Message.objects.filter(room_name=room_name).order_by('timestamp')
    token = jwt.encode({"sub": "42"}, "my_secret")

    return render(request, 'chat_room.html', {
        'room_name': room_name,
        'messages': messages,
        'token': token,
        'user_id': user_id
    })


@csrf_exempt
def connect(request):
    # In connect handler we must authenticate connection.
    # Here we return a fake user ID to Centrifugo to keep tutorial short.
    # More details about connect result format can be found in proxy docs:
    # https://centrifugal.dev/docs/server/proxy#connect-proxy
    logger.debug(request.body)
    response = {
        'result': {
            'user': 'tutorial-user'
        }
    }
    return JsonResponse(response)


@csrf_exempt
def publish(request):
    # In publish handler we can validate publication request initialted by a user.
    # Here we return an empty object – thus allowing publication.
    # More details about publish result format can be found in proxy docs:
    # https://centrifugal.dev/docs/server/proxy#publish-proxy
    response = {
        'result': {}
    }
    return JsonResponse(response)


@csrf_exempt
def subscribe(request):
    # In subscribe handler we can validate user subscription request to a channel.
    # Here we return an empty object – thus allowing subscription.
    # More details about subscribe result format can be found in proxy docs:
    # https://centrifugal.dev/docs/server/proxy#subscribe-proxy
    response = {
        'result': {}
    }
    return JsonResponse(response)


def send_message(request):
    print(request.POST)
    if request.method == 'POST':
        sender = request.user
        receiver_username = request.POST.get('receiver')
        receiver = get_object_or_404(User, pk=receiver_username)
        room_name = request.POST.get('room_name')
        content = request.POST.get('content')
        print(sender, receiver, room_name, content)
        Message.objects.create(sender=sender, receiver=receiver, room_name=room_name, content=content)
        return JsonResponse({'status': 'success'})
    else:
        print(request)
    return JsonResponse({'status': 'failed'}, status=400)


def edit_test(request, test_id):
    test = get_object_or_404(Test, pk=test_id)
    QuestionFormSet = inlineformset_factory(Test, Question, form=QuestionForm, extra=0, can_delete=True)
    AnswerFormSet = inlineformset_factory(Question, Answer, form=AnswerForm, extra=0, can_delete=True)

    if request.method == 'POST':
        test_form = TestForm(request.POST, instance=test)
        question_formset = QuestionFormSet(request.POST, instance=test)

        if test_form.is_valid() and question_formset.is_valid():
            test_form.save()
            question_formset.save()

            for form in question_formset:
                if form.is_bound and form.has_changed():
                    question = form.instance
                    answer_formset = AnswerFormSet(request.POST, instance=question)
                    if answer_formset.is_valid():
                        answer_formset.save()

            return redirect('index')
    else:
        test_form = TestForm(instance=test)
        question_formset = QuestionFormSet(instance=test)

    answer_formsets = []
    for question in test.questions.all():
        answer_formset = AnswerFormSet(instance=question, prefix=f'answers_{question.id}')
        answer_formsets.append((question.id, answer_formset))

    context = {
        'test_form': test_form,
        'question_formset': question_formset,
        'answer_formsets': answer_formsets,
    }
    return render(request, 'edit_test.html', context)


@login_required
def problem_list(request):
    problems = Problem.objects.all()
    return render(request, 'problems/problem_list.html', {'problems': problems})


@login_required
def problem_detail(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    return render(request, 'problems/problem_detail.html', {'problem': problem})


@login_required
def contest_results(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    participants = ContestParticipant.objects.filter(contest=contest).annotate(total_score=Sum('best_score')).order_by(
        '-total_score')
    return render(request, 'contest_results.html', {'contest': contest, 'participants': participants})


from django.db.models import Max  # Correct import for Max aggregate function


@login_required
def submit_solution(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    contest = problem.contests.first()  # Assuming a problem belongs to only one contest
    participant = ContestParticipant.objects.filter(user=request.user, contest=contest).first()
    previous_attempts = SubmissionAttempt.objects.filter(user=request.user, problem=problem)
    print(previous_attempts)
    if not participant:
        return redirect('contest_detail', contest_id=contest.id)

    if timezone.now() > contest.end_time or participant.finished:
        return redirect('contest_results', contest_id=contest.id)

    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.problem = problem
            submission.save()

            last_attempt = SubmissionAttempt.objects.filter(submission=submission).order_by('-attempt_number').first()
            attempt_number = previous_attempts.count() + 1

            start_time = timezone.now()
            result = run_code_in_docker(submission.code, problem.test_cases)
            end_time = timezone.now()
            compile_time = (end_time - start_time).total_seconds()

            try:
                result_data = json.loads(result)
            except json.JSONDecodeError as e:
                return render(request, 'problems/submit_solution.html', {
                    'form': form, 'problem': problem, 'error_message': f"Failed to decode JSON: {e}"
                })

            passed = all(test['passed'] for test in result_data)
            score = sum(1 for test in result_data if test['passed'])
            result = "Passed" if passed else "Failed"

            memory_usage = calculate_memory_usage()  # Implement this function to get memory usage

            attempt = SubmissionAttempt.objects.create(
                user=request.user,
                submission=submission,
                problem=problem,
                attempt_number=attempt_number,
                compile_time=compile_time,
                memory_usage=memory_usage,
                result=result,
                score=1 if passed else 0,
            )

            successful_attempts = SubmissionAttempt.objects.filter(user=request.user, problem=problem,
                                                                   result="Passed").count()
            participant.best_score = successful_attempts
            participant.save()

            previous_attempts = SubmissionAttempt.objects.filter(submission=submission)

            return render(request, 'problems/submit_solution.html', {
                'form': form,
                'problem': problem,
                'result_data': result_data,
                'compile_time': compile_time,
                'previous_attempts': previous_attempts,
            })
    else:
        form = SubmissionForm(initial={'code': "def my_function():\n    # Ваш код здесь"})
        previous_attempts = SubmissionAttempt.objects.filter(user=request.user, problem=problem).order_by(
            'attempt_number')
        last_submission = Submission.objects.filter(user=request.user, problem=problem).order_by(
            '-submitted_at').first()
        initial_code = last_submission.code if last_submission else "def my_function():\n    # ваш код здесь"

        form = SubmissionForm(initial={'code': initial_code})
    return render(request, 'problems/submit_solution.html',
                  {'form': form, 'problem': problem, 'previous_attempts': previous_attempts})


@login_required
def contest_list(request):
    contests = Contest.objects.all()
    available_contests = []
    unavailable_contests = []

    for contest in contests:
        if timezone.now() < contest.start_time:
            unavailable_contests.append((contest, "Контест еще не начался"))
        elif timezone.now() > contest.end_time:
            unavailable_contests.append((contest, "Контест закончился"))
        elif not ContestParticipant.objects.filter(user=request.user, contest=contest).exists():
            unavailable_contests.append((contest, "Вы не зарегистрированы"))
        else:
            available_contests.append(contest)

    return render(request, 'contests/contest_list.html', {
        'available_contests': available_contests,
        'unavailable_contests': unavailable_contests
    })


@login_required
def contest_detail(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    participant = ContestParticipant.objects.filter(user=request.user, contest=contest).first()
    print(contest.start_time)
    if request.method == "GET":
        if not participant:
            return redirect('join_contest', contest_id=contest_id)
        if participant.finished:
            return redirect('contest_results', contest_id=contest_id)

        problems = contest.problems.all()
        current_time = timezone.now()
        if current_time < contest.start_time:
            return redirect('contest_list')
        elif current_time > contest.end_time:
            return redirect('contest_list')
        remaining_time_data = contest.end_time - current_time
        remaining_seconds = int(remaining_time_data.total_seconds())
        days, remaining_seconds = divmod(remaining_seconds, 86400)
        hours, remaining_seconds = divmod(remaining_seconds, 3600)
        minutes, seconds = divmod(remaining_seconds, 60)

        remaining_time = f'{days}д {hours}ч {minutes}м {seconds}с'
        print(remaining_time)
    else:
        print('finish')
        participant.finished = True
        participant.save()

        return redirect('contest_results', contest_id=contest_id)

    return render(request, 'contests/contest_detail.html',
                  {'contest': contest, 'problems': problems, 'remaining_time': remaining_time})


@login_required
def contest_results(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    participants = ContestParticipant.objects.filter(contest=contest)

    results = []
    for participant in participants:
        best_scores = []
        for problem in contest.problems.all():
            attempts = SubmissionAttempt.objects.filter(user=participant.user, problem=problem)
            if attempts.exists():
                best_score = max([attempt.score for attempt in attempts])
                best_scores.append(best_score)
        total_score = sum(best_scores)
        results.append({
            'user': participant.user,
            'total_score': total_score,
        })

    results = sorted(results, key=lambda x: x['total_score'], reverse=True)

    return render(request, 'contests/contest_result.html', {'contest': contest, 'results': results})


@login_required
def join_contest(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    if request.method == 'POST':
        form = JoinContestForm(request.POST)
        if form.is_valid():
            contest_participant, created = ContestParticipant.objects.get_or_create(user=request.user, contest=contest)
            if created:
                return redirect('contest_detail', contest_id=contest_id)
            else:
                return render(request, 'already_joined.html', {'contest': contest})
    else:
        form = JoinContestForm(initial={'contest_id': contest_id})
    return render(request, 'contests/join_contest.html', {'form': form, 'contest': contest})


@login_required
def create_contest(request):
    if request.method == 'POST':
        form = ContestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contest_list')
    else:
        form = ContestForm()
    return render(request, 'contests/create_contest.html', {'form': form})


@login_required
def create_problem(request):
    if request.method == 'POST':
        form = ProblemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('problem_list')
    else:
        form = ProblemForm()
    return render(request, 'problems/create_problem.html', {'form': form})


def check_test_results(test_result_id):
    try:
        test_result = TestResult.objects.get(id=test_result_id)
        total_score = 0
        questions = test_result.test.questions.all()

        for question in questions:
            question_result = QuestionResult.objects.get(test_result=test_result, question=question)
            correct_answers = set(question.answers.filter(is_correct=True))
            selected_answers = set(question_result.selected_answers.all())

            if correct_answers == selected_answers:
                total_score += 1

        test_result.score = total_score
        test_result.end_time = time.timezone.now()
        test_result.save()

        return test_result

    except TestResult.DoesNotExist:
        print(f"No TestResult found with id {test_result_id}")
        return None


def calculate_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    # Return memory usage in MB
    return memory_info.rss / (1024 * 1024)


def submit_test(request, test_id):
    test = get_object_or_404(Test, pk=test_id)

    if request.method == 'POST':
        form = TestPassingForm(request.POST, test=test)
        if form.is_valid():
            test_result = form.save(commit=False)
            test_result.user = request.user
            test_result.test = test
            test_result.save()

            correct_answers_count = 0
            incorrect_answers_count = 0

            for question in test.questions.all():
                selected_answers = form.cleaned_data.get(f'question_{question.id}', None)
                if selected_answers is not None:
                    question_result = QuestionResult.objects.create(test_result=test_result, question=question)
                    question_result.selected_answers.set(selected_answers)

                    for answer in selected_answers:
                        if answer.is_correct:
                            correct_answers_count += 1
                        else:
                            incorrect_answers_count += 1

            test_result.correct_answers_count = correct_answers_count
            test_result.incorrect_answers_count = incorrect_answers_count
            test_result.save()

            return redirect('test_result', test_result_id=test_result.id)

    else:
        form = TestPassingForm(test=test)

    return render(request, 'test.html', {'form': form, 'test': test})


import io
import base64
import matplotlib.pyplot as plt


def test_result_view(request, test_result_id):
    test_result = get_object_or_404(TestResult, pk=test_result_id)

    # Calculate statistics for all participants
    all_results = TestResult.objects.filter(test=test_result.test)
    total_participants = all_results.count()

    question_statistics = []
    question_texts = []
    correct_answers_counts = []
    incorrect_answers_counts = []

    for question in test_result.test.questions.all():
        question_results = QuestionResult.objects.filter(question=question)
        total_answers = question_results.count()

        correct_answers = question_results.filter(selected_answers__is_correct=True).count()
        incorrect_answers = total_answers - correct_answers

        question_statistics.append({
            'question_text': question.question_text,
            'total_answers': total_answers,
            'correct_answers': correct_answers,
            'incorrect_answers': incorrect_answers,
        })
        question_texts.append(question.question_text)
        correct_answers_counts.append(correct_answers)
        incorrect_answers_counts.append(incorrect_answers)

    # Plot the statistics
    plt.figure(figsize=(10, 6))
    bar_width = 0.35
    index = range(len(question_texts))

    plt.bar(index, correct_answers_counts, bar_width, label='Correct Answers')
    plt.bar(index, incorrect_answers_counts, bar_width, bottom=correct_answers_counts, label='Incorrect Answers')

    plt.xlabel('Questions')
    plt.ylabel('Number of Answers')
    plt.title('Question Statistics')
    plt.xticks(index, question_texts, rotation=45, ha='right')
    plt.legend()

    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    context = {
        'test_result': test_result,
        'total_participants': total_participants,
        'question_statistics': question_statistics,
        'graph': image_base64,
    }
    return render(request, 'test_result.html', context)


@login_required
def test_info_view(request, test_id):
    test = get_object_or_404(Test, pk=test_id)
    user = request.user
    current_time = timezone.now()

    # Проверка количества попыток
    attempts = TestResult.objects.filter(test=test, user=user).count()
    if attempts >= test.max_attempts:
        return render(request, 'test_access_denied.html', {'reason': 'attempts_exceeded'})

    # Проверка времени начала и окончания теста
    if current_time < test.start_time:
        return render(request, 'test_access_denied.html', {'reason': 'test_not_started'})
    elif current_time > test.end_time:
        return render(request, 'test_access_denied.html', {'reason': 'test_ended'})

    return render(request, 'test_info.html', {'test': test})


@login_required
def student_test_results(request, student_id):
    student = get_object_or_404(User, pk=student_id)
    test_results = TestResult.objects.filter(user=student)

    total_tests = test_results.count()
    total_correct_answers = sum(result.correct_answers_count for result in test_results)
    total_incorrect_answers = sum(result.incorrect_answers_count for result in test_results)
    print(test_results[0].correct_answers_count)
    # Check if there are no results to prevent division by zero
    if total_correct_answers == 0 and total_incorrect_answers == 0:
        total_correct_answers = 1  # to prevent zero division error
        total_incorrect_answers = 1

    # Plot the results
    labels = ['Правильные ответы', 'Неправильные ответы']
    sizes = [total_correct_answers, total_incorrect_answers]
    colors = ['#4CAF50', '#F44336']

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    context = {
        'student': student,
        'test_results': test_results,
        'total_tests': total_tests,
        'total_correct_answers': total_correct_answers,
        'total_incorrect_answers': total_incorrect_answers,
        'graph': image_base64,
    }
    return render(request, 'student_test_results.html', context)
