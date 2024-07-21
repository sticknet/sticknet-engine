from django.conf.urls import url

from .views import UploadPreKeyBundle, FetchPreKeyBundle, UploadSenderKey, FetchSenderKey, FetchStandardSenderKeys, \
    Login, WebLogin, FetchOneTimeId, \
    FetchUploadedSenderKeys, FetchPreKeyBundles, UploadSenderKeys, UploadStandardSenderKeys, UploadPreKeys, \
    GetActiveStickId, UpdateActiveSPK, UpdateActiveIK, ChangePassword, FetchPendingKeys

app_name = 'keys'
urlpatterns = [
    url(r'^upload-pkb/$', UploadPreKeyBundle.as_view(), name='upload_pkb'),
    url(r'^upload-pre-keys/$', UploadPreKeys.as_view(), name='upload_pre_keys'),
    url(r'^fetch-pkb/$', FetchPreKeyBundle.as_view(), name='fetch_pkb'),
    url(r'^fetch-pkbs/$', FetchPreKeyBundles.as_view(), name='fetch_pkbs'),
    url(r'^fetch-uploaded-sks/$', FetchUploadedSenderKeys.as_view(), name='fetch_uploaded_sks'),
    url(r'^fetch-sk/$', FetchSenderKey.as_view(), name='fetch_sk'),
    url(r'^fetch-standard-sks/$', FetchStandardSenderKeys.as_view(), name='fetch_standard_sks'),
    url(r'^upload-sk/$', UploadSenderKey.as_view(), name='upload_sk'),
    url(r'^upload-sks/$', UploadSenderKeys.as_view(), name='upload_sks'),
    url(r'^upload-standard-sks/$', UploadStandardSenderKeys.as_view(), name='upload_standard_sks'),
    url(r'^login/$', Login.as_view(), name='login'),
    url(r'^web-login/$', WebLogin.as_view(), name='web_login'),
    url(r'^fetch-otid/$', FetchOneTimeId.as_view(), name='fetch_otid'),
    url(r'^get-active-stick-id/$', GetActiveStickId.as_view(), name='get_active_stick_id'),
    url(r'^update-active-spk/$', UpdateActiveSPK.as_view(), name='update_active_spk'),
    url(r'^update-active-ik/$', UpdateActiveIK.as_view(), name='update_active_ik'),
    url(r'^change-password/$', ChangePassword.as_view(), name='change_password'),
    url(r'^fetch-pending-keys/$', FetchPendingKeys.as_view(), name='fetch_pending_keys'),
]
