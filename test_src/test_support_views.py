from knox.models import AuthToken
from users.models import User
from rest_framework.test import APITestCase
from support.models import Feedback, Report, Question, Error, UserReport, PostReport
from photos.models import Image


def set_up_user(self):
    self.user = User.objects.create(username='alice123', phone='+16501119999', phone_hash='AX(*$',
                                    finished_registration=True, one_time_id='zzzzz')
    self.auth_token = AuthToken.objects.create(self.user)
    self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.auth_token[1])


class TestSendSupportMessage(APITestCase):
    def setUp(self):
        set_up_user(self)

    def test_send_support_message(self):
        response = self.client.post('/api/support-message/', {'report': True, 'text': 'some text'})
        self.assertEqual(response.data['sent'], True)
        self.assertEqual(Report.objects.filter(user=self.user, text='some text').exists(), True)

        response = self.client.post('/api/support-message/', {'report': False, 'text': 'some text'})
        self.assertEqual(response.data['sent'], True)
        self.assertEqual(Feedback.objects.filter(user=self.user, text='some text').exists(), True)

class TestAskQuestion(APITestCase):
    def setUp(self):
        set_up_user(self)

    def test_ask_question(self):
        response = self.client.post('/api/ask-question/', {'text': 'question?'})
        self.assertEqual(response.data['sent'], True)
        self.assertEqual(Question.objects.filter(user=self.user, text='question?').exists(), True)

        response = self.client.post('/api/ask-question/', {'text': 'question?', 'anonymous': True, 'email': 'myemail@gmail.com'})
        self.assertEqual(response.data['sent'], True)
        self.assertEqual(Question.objects.filter(email='myemail@gmail.com', text='question?').exists(), True)


class TestErrorReport(APITestCase):
    def setUp(self):
        set_up_user(self)

    def test_error_report(self):
        response = self.client.post('/api/error-report/', {'string': 'some error', 'native': True, 'is_fatal': True, 'platform': 'I',
                                                           'model': 'model', 'system_version': 'system_version', 'app_version': 'app_version',
                                                           'user_id': self.user.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Error.objects.filter(user=self.user, string='some error').exists(), True)



class TestReportUser(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)

    def test_report_user(self):
        response = self.client.post('/api/report-user/', {'to_user_id': '1', 'reason': 'A'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserReport.objects.filter(from_user=self.user, to_user=self.user_1, reason='A').exists(), True)


class TestReportPost(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        Image.objects.create(id=55, user=self.user_1)

    def test_report_user(self):
        response = self.client.post('/api/report-post/', {'to_user_id': '1', 'image_id': 55, 'reason': 'Z'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PostReport.objects.filter(from_user=self.user, to_user=self.user_1, reason='Z').exists(), True)
