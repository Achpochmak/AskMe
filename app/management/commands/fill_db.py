from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from app.models import Question, Answer, Profile, AnswerLike, QuestionLike, Tag
import random
from faker import Faker


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int)

    def handle(self, *args, **options):
        ratio = options['ratio']

        users_count = ratio
        questions_count = ratio * 10
        tags_count = ratio

        tags = []
        fake = Faker()
        for _ in range(tags_count):
            tag = Tag.objects.create(name=fake.word())
            tags.append(tag)
        users = []
        print('users')

        for _ in range(users_count):
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='password'
            )
            Profile.objects.create(user=user)
            users.append(user)
        print('questions')

        for _ in range(questions_count):
            question = Question.objects.create(
                title=fake.sentence(),
                content=fake.paragraph(),
                user=random.choice(users)
            )
            question.tags.add(*random.choices(tags, k=random.randint(1, 3)))

        for question in Question.objects.all():
            for _ in range(random.randint(1, 30)):
                Answer.objects.create(
                    content=fake.paragraph(),
                    question=question,
                    user=random.choice(users)
                )
        for answer in Answer.objects.all():
            for user in users:
                if random.choice([True, False]) and not AnswerLike.objects.filter(user=user, answer=answer).exists():
                    AnswerLike.objects.create(user=user, answer=answer)
        print('questionlike')

        for question in Question.objects.all():
            for user in users:
                if random.choice([True, False]) and not QuestionLike.objects.filter(user=user,
                                                                                    question=question).exists():
                    QuestionLike.objects.create(user=user, question=question)
        print('answerlike')
