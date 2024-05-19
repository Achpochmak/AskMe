from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.db.models import Count
from django.shortcuts import get_object_or_404


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    avatar = models.ImageField(null=True, blank=True, default="Cat03.jpg", upload_to="avatar/%Y/%m/%d")
    nickname = models.CharField(max_length=255)

    def __str__(self):
        return self.nickname


class Group(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    can_create_tests = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group, related_name='teachers')  # добавляем связь с группами

    def __str__(self):
        return self.user.username


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    group = models.OneToOneField(Group, on_delete=models.PROTECT)

    def __str__(self):
        return self.user.username


class Test(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    accessible_groups = models.ManyToManyField(Group)
    max_attempts = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title


class Question(models.Model):
    question_text = models.TextField(verbose_name='Question Text')
    question_type = models.CharField(max_length=20, choices=[
        ('text', 'Text'),
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice')
    ], verbose_name='Question Type')
    test = models.ForeignKey('Test', on_delete=models.CASCADE, related_name='questions')

    def __str__(self):
        return self.question_text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=255, verbose_name='Answer Text', null=True, blank=True, )
    is_correct = models.BooleanField(default=False, verbose_name='Is Correct')

    def __str__(self):
        return self.answer_text


class TestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    correct_answers_count = models.IntegerField(default=0)
    incorrect_answers_count = models.IntegerField(default=0)


class QuestionResult(models.Model):
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='question_results')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.ManyToManyField(Answer)

    def __str__(self):
        return f"{self.test_result.user.username}'s answer to {self.question.question_text}"


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    room_name = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender} to {self.receiver}: {self.content}'

class ChatRoom(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User, related_name='chatrooms')

class Problem(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    difficulty = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    test_cases = models.TextField()  # JSON-формат для хранения тестов и ожидаемых результатов

    def __str__(self):
        return self.title

class Contest(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    problems = models.ManyToManyField(Problem, related_name='contests')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    code = models.TextField()
    result = models.CharField(max_length=50)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.problem}"

class ContestParticipant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    finished = models.BooleanField(default=False)
    best_score = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.user} - {self.contest}"

class SubmissionAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    attempt_number = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    memory_usage = models.FloatField(null=True, blank=True)
    compile_time = models.FloatField(null=True, blank=True)
    result = models.CharField(max_length=20, null=True, blank=True)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"Attempt {self.attempt_number} by {self.user.username} on {self.problem.title}"