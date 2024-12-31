from django.conf.urls import url

from .views import GenerateNonce, VerifySiwe, GetSession, FlushSession, SetAccountSecret

app_name = 'wallet'
urlpatterns = [
    url(r'^generate-nonce/$', GenerateNonce.as_view(), name='generate_nonce'),
    url(r'^verify-siwe/$', VerifySiwe.as_view(), name='verify_siwe'),
    url(r'^get-session/$', GetSession.as_view(), name='get_session'),
    url(r'^flush-session/$', FlushSession.as_view(), name='flush_session'),
    url(r'^set-account-secret/$', SetAccountSecret.as_view(), name='set_account_secret'),
]
