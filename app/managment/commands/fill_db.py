from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from app.models import Question, Answer, Profile, AnswerLike, QuestionLike
import random
import string

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int)

    def generate_random_string(self, length=10):
        return ''.join(random.choices(string.ascii_letters, k=length))
def create_users():
    def handle(self, *args, **options):
        ratio = options['ratio']

        users_count = ratio
        questions_count = ratio * 10
        answers_count = ratio * 100
        tags_count = ratio
        likes_count = ratio * 200

        self.create_users_and_profiles(users_count)
        self.create_tags(tags_count)
        self.create_questions(questions_count)
        self.create_answers(answers_count)
        self.create_likes(likes_count)
