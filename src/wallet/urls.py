from django.urls import re_path

from .views import GenerateNonce, VerifySiwe, GetSession, FlushSession, SetAccountSecret

app_name = 'wallet'
urlpatterns = [
    re_path(r'^generate-nonce/$', GenerateNonce.as_view(), name='generate_nonce'),
    re_path(r'^verify-siwe/$', VerifySiwe.as_view(), name='verify_siwe'),
    re_path(r'^get-session/$', GetSession.as_view(), name='get_session'),
    re_path(r'^flush-session/$', FlushSession.as_view(), name='flush_session'),
    re_path(r'^set-account-secret/$', SetAccountSecret.as_view(), name='set_account_secret'),
]
