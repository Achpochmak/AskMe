from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.db.models import Count


class QuestionManager(models.Manager):
    def get_hot(self):
        return self.annotate(answers_count=models.Count('answer', distinct=True),
                             question_likes_count=models.Count('questionlike', distinct=True)).order_by(
            '-question_likes_count')

    def get_hot_tags(self):
        return Tag.objects.annotate(usage_count=models.Count('question')).order_by('-usage_count')

    def get_hot_users(self):
        print(User.objects.annotate(usage_count=models.Count('question') + models.Count('answer')).order_by(
            '-usage_count'))
        return User.objects.annotate(usage_count=models.Count('question') + models.Count('answer')).order_by(
            '-usage_count')

    def get_new(self):
        return self.annotate(answers_count=models.Count('answer', distinct=True),
                             question_likes_count=models.Count('questionlike', distinct=True)).order_by('-created_at')

    def get_by_tag(self, tag_name):
        self = self.answers_count()
        return self.filter(tags__name=tag_name).annotate(
            question_likes_count=models.Count('questionlike', distinct=True)).order_by(
            'created_at')

    def get_question(self, question_id):
        return self.annotate(answers_count=models.Count('answer', distinct=True),
                                                     question_likes_count=models.Count('questionlike', distinct=True))

    def answers_count(self):
        return self.get_queryset().annotate(answers_count=models.Count('answer', distinct=True))

    def question_likes_count(self):
        return self.get_queryset().annotate(question_likes_count=models.Count('questionlike'))

    def answer_likes_count(self):
        return self.get_queryset().annotate(answer_likes_count=models.Count('answerlike'))


class Tag(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    avatar = models.ImageField(null=True, blank=True)
    nickname = models.CharField(max_length=255)

    def __str__(self):
        return self.nickname


class Question(models.Model):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    tags = models.ManyToManyField(Tag, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = QuestionManager()

    def __str__(self):
        return self.title


class Answer(models.Model):
    content = models.TextField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content


class QuestionLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'question')


class AnswerLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'answer')
