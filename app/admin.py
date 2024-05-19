from django.contrib import admin

# Register your models here.
from app import models
from app.models import Group, Teacher, Student, Test, Answer, Question, QuestionResult, TestResult, Message, Submission, \
    Problem, SubmissionAttempt, Contest, ContestParticipant, ChatRoom

# Register your models here.

admin.site.register(models.Profile)
admin.site.register(Teacher)
admin.site.register(Group)
admin.site.register(Test)
admin.site.register(Student)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(QuestionResult)
admin.site.register(TestResult)
admin.site.register(Message)
admin.site.register(Problem)
admin.site.register(Submission)
admin.site.register(SubmissionAttempt)
admin.site.register(Contest)
admin.site.register(ContestParticipant)
admin.site.register(ChatRoom)


