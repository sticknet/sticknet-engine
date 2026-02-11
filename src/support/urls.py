from django.urls import re_path

from .views import SendSupportMessage, AskQuestion, ErrorReport, ReportUser, ReportPost

app_name = 'support'
urlpatterns = [
    re_path(r'^support-message/$', SendSupportMessage.as_view(), name='support_message'),
    re_path(r'^ask-question/$', AskQuestion.as_view(), name='ask_question'),
    re_path(r'^error-report/$', ErrorReport.as_view(), name='error_report'),
    re_path(r'^report-user/$', ReportUser.as_view(), name='report_user'),
    re_path(r'^report-post/$', ReportPost.as_view(), name='report_post')
]
