from django.urls import re_path

from .views import UploadPreKeyBundle, FetchPreKeyBundle, UploadSenderKey, FetchSenderKey, FetchStandardSenderKeys, \
    Login, WebLogin, FetchOneTimeId, \
    FetchUploadedSenderKeys, FetchPreKeyBundles, UploadSenderKeys, UploadStandardSenderKeys, UploadPreKeys, \
    GetActiveStickId, UpdateActiveSPK, UpdateActiveIK, ChangePassword, FetchPendingKeys

app_name = 'keys'
urlpatterns = [
    re_path(r'^upload-pkb/$', UploadPreKeyBundle.as_view(), name='upload_pkb'),
    re_path(r'^upload-pre-keys/$', UploadPreKeys.as_view(), name='upload_pre_keys'),
    re_path(r'^fetch-pkb/$', FetchPreKeyBundle.as_view(), name='fetch_pkb'),
    re_path(r'^fetch-pkbs/$', FetchPreKeyBundles.as_view(), name='fetch_pkbs'),
    re_path(r'^fetch-uploaded-sks/$', FetchUploadedSenderKeys.as_view(), name='fetch_uploaded_sks'),
    re_path(r'^fetch-sk/$', FetchSenderKey.as_view(), name='fetch_sk'),
    re_path(r'^fetch-standard-sks/$', FetchStandardSenderKeys.as_view(), name='fetch_standard_sks'),
    re_path(r'^upload-sk/$', UploadSenderKey.as_view(), name='upload_sk'),
    re_path(r'^upload-sks/$', UploadSenderKeys.as_view(), name='upload_sks'),
    re_path(r'^upload-standard-sks/$', UploadStandardSenderKeys.as_view(), name='upload_standard_sks'),
    re_path(r'^login/$', Login.as_view(), name='login'),
    re_path(r'^web-login/$', WebLogin.as_view(), name='web_login'),
    re_path(r'^fetch-otid/$', FetchOneTimeId.as_view(), name='fetch_otid'),
    re_path(r'^get-active-stick-id/$', GetActiveStickId.as_view(), name='get_active_stick_id'),
    re_path(r'^update-active-spk/$', UpdateActiveSPK.as_view(), name='update_active_spk'),
    re_path(r'^update-active-ik/$', UpdateActiveIK.as_view(), name='update_active_ik'),
    re_path(r'^change-password/$', ChangePassword.as_view(), name='change_password'),
    re_path(r'^fetch-pending-keys/$', FetchPendingKeys.as_view(), name='fetch_pending_keys'),
]
