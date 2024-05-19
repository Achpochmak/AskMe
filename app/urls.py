from django.conf.urls.static import static
from django.urls import path

from app import views
from askme_pupkin import settings

urlpatterns = [
    path('', views.index, name='index'),
    path('settings/', views.settings, name='settings'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('create_test/', views.create_test, name='create_test'),
    path('test/<int:test_id>', views.test, name='test'),
    path('test_result/<int:test_result_id>/', views.view_test_result, name='view_test_result'),
    path('room/<int:user_id>/>', views.room, name='room'),
    path('centrifugo/connect/', views.connect, name='connect'),
    path('centrifugo/subscribe/', views.subscribe, name='subscribe'),
    path('centrifugo/publish/', views.publish, name='publish'),
    path('send_message/', views.send_message, name='send_message'),
    path('edit_test/<int:test_id>', views.edit_test, name='edit_test'),
    path('problem_list/', views.problem_list, name='problem_list'),
    path('problems/<int:pk>/', views.problem_detail, name='problem_detail'),
    path('problems/<int:problem_id>/submit/', views.submit_solution, name='submit_solution'),
    path('contest_list/', views.contest_list, name='contest_list'),
    path('create_contest/', views.create_contest, name='create_contest'),
    path('create_problem/', views.create_problem, name='create_problem'),
    path('test-result/<int:test_result_id>/', views.test_result_view, name='test_result'),
    path('submit_test/<int:test_id>/', views.submit_test, name='submit_test'),
    path('test-info/<int:test_id>/', views.test_info_view, name='test_info'),
    path('contest/<int:contest_id>/', views.contest_detail, name='contest_detail'),
    path('problem/<int:problem_id>/submit/', views.submit_solution, name='submit_solution'),
    path('contest/<int:contest_id>/results/', views.contest_results, name='contest_results'),
    path('contest/<int:contest_id>/join_contest/', views.join_contest, name='join_contest'),
    path('archive/', views.archive, name='archive'),
    path('student_search/', views.student_search, name='student_search'),
    path('student_test_results/<int:student_id>/', views.student_test_results, name='student_test_results'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)
