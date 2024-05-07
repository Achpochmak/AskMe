from django.conf.urls.static import static
from django.urls import path

from app import views
from askme_pupkin import settings

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('settings/', views.settings, name='settings'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('ask/', views.ask, name='ask'),
    path('logout/', views.logout, name='logout'),
    path('question/<int:question_id>', views.question, name='question'),
    path('tag/<str:tag_name>', views.tag, name='tag'),
    path('like', views.like, name='like'),
    path('correct_answer', views.correct_answer, name='correct_answer'),
    path('member/<int:user_id>', views.member, name='member'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)
