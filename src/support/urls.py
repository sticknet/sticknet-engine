from django.conf.urls import url

from .views import SendSupportMessage, AskQuestion, ErrorReport, ReportUser, ReportPost

app_name = 'support'
urlpatterns = [
    url(r'^support-message/$', SendSupportMessage.as_view(), name='support_message'),
    url(r'^ask-question/$', AskQuestion.as_view(), name='ask_question'),
    url(r'^error-report/$', ErrorReport.as_view(), name='error_report'),
    url(r'^report-user/$', ReportUser.as_view(), name='report_user'),
    url(r'^report-post/$', ReportPost.as_view(), name='report_post')
]
