from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from .models import Report, Feedback, Question, Error, UserReport, PostReport, PublicFile
from users.models import User
from photos.models import Image
from django.http import HttpResponse



class SendSupportMessage(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if request.data['report']:
            Report.objects.create(user=user, text=request.data['text'])
        else:
            Feedback.objects.create(user=user, text=request.data['text'])
        return Response({'sent': True})


class AskQuestion(APIView):

    def post(self, request):
        question = Question.objects.create(text=request.data['text'])
        if 'anonymous' in request.data:
            question.email = request.data['email'].lower()
            identifier = request.data['email'].lower()
        else:
            question.user = request.user
            identifier = request.user.email
        question.save()
        html_content = render_to_string('question.html', {'identifier': identifier, 'question': request.data['text']})
        text_content = strip_tags(html_content)
        mail = EmailMultiAlternatives('Question', text_content, 'founder@sticknet.org', ['founder@sticknet.org'])
        mail.attach_alternative(html_content, "text/html")
        mail.send()
        return Response({'sent': True})


class ErrorReport(APIView):

    def post(self, request):
        data = request.data
        screen = ''
        if 'screen' in data:
            screen = data['screen']
        error = Error.objects.create(string=data['string'], native=data['native'], is_fatal=data['is_fatal'], platform=data['platform'],
                             model=data['model'],
                             system_version=data['system_version'], app_version=data['app_version'],
                             screen=screen)
        username = ''
        if 'user_id' in data:
            user = User.objects.get(id=data['user_id'])
            error.user = user
            error.save()
            username = user.username
        html_content = render_to_string('error.html', {'string': data['string'], 'native': data['native'], 'is_fatal': data['is_fatal'],
                                                       'platform': data['platform'], 'model': data['model'],
                                                       'system_version': data['system_version'],
                                                       'app_version': data['app_version'], 'username': username,
                                                       'screen': screen})
        text_content = strip_tags(html_content)
        mail = EmailMultiAlternatives('Application Error', text_content, 'founder@sticknet.org', ['stiiick.app.errors@gmail.com'])
        mail.attach_alternative(html_content, "text/html")
        mail.send()
        return Response(status=status.HTTP_200_OK)

class ReportUser(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        to_user = User.objects.get(id=request.data['to_user_id'])
        UserReport.objects.create(from_user=request.user, to_user=to_user, reason=request.data['reason'])
        return Response(status=status.HTTP_200_OK)

class ReportPost(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        to_user = User.objects.get(id=request.data['to_user_id'])
        post = Image.objects.get(id=request.data['image_id'])
        PostReport.objects.create(from_user=request.user, to_user=to_user, reason=request.data['reason'], post=post)
        return Response(status=status.HTTP_200_OK)


def stick_protocol_paper(request):
    file = PublicFile.objects.get(name='Stick Protocol Paper')
    response = HttpResponse(file.uri, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="stick-protocol.pdf"'
    return response


