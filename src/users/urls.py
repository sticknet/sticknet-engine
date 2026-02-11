from django.urls import include, re_path
from rest_framework import routers

from .views import UserSearch, RefreshUser, UserViewSet, \
    ProfilePictureViewSet, \
    CheckUsername, \
    DeactivateAccount, DeleteAccount, PhoneVerified, Register, \
    UpdateContacts, ProfileCoverViewSet, UploadCategories, BackupChats, CreateE2EUser, BlockUser, \
    UnblockUser, \
    FetchBlockedAccounts, ToggleHideImage, FetchSingleUser, FetchDevices, \
    UploadPasswordKey, \
    VerifyPassword, CodeConfirmedDeleteAccount, RecreateUser, FetchPreferences, FetchUserCategories, \
    FetchUserChatBackup, FetchUserDevices, UpdateChatDevice, DeleteChatBackup, UpdateBackupFreq, \
    HighlightImage, UpdateDonationReminder, GetAppSettings, SetPhotoBackupSetting, RequestEmailCode, VerifyEmailCode, \
    CheckUserPhoneExists, SetFolderIcon, SetPlatform, \
    PingServer, EmailReminder, TestIP, SetWebKey, GetWebKey

router = routers.SimpleRouter()
router.register('users', UserViewSet, basename='users')
router.register('profile-picture', ProfilePictureViewSet, basename='profile_picture')
router.register('profile-cover', ProfileCoverViewSet, basename='profile_cover')

app_name = 'users'
urlpatterns = [
    re_path('^', include(router.urls)),
    re_path(r'^get-app-settings/$', GetAppSettings.as_view(), name='get_app_settings'),
    re_path('^refresh-user/$', RefreshUser.as_view()),
    re_path(r'^check-username/$', CheckUsername.as_view(), name='check_username'),
    re_path(r'^search/$', UserSearch.as_view(), name='search'),
    re_path(r'^phone-verified/$', PhoneVerified.as_view(), name='phone_verified'),
    re_path(r'^register/$', Register.as_view(), name='register'),
    re_path(r'^update-contacts/$', UpdateContacts.as_view(), name='update_contacts'),
    re_path(r'^upload-categories/$', UploadCategories.as_view(), name='upload_categories'),
    re_path(r'^backup-chats/$', BackupChats.as_view(), name='backup_chats'),
    re_path(r'^delete-chat-backup/$', DeleteChatBackup.as_view(), name='delete_chat_backup'),
    re_path(r'^update-backup-freq/$', UpdateBackupFreq.as_view(), name='update_backup_freq'),
    re_path(r'^block/$', BlockUser.as_view(), name='block'),
    re_path(r'^unblock/$', UnblockUser.as_view(), name='unblock'),
    re_path(r'^fetch-blocked/$', FetchBlockedAccounts.as_view(), name='fetch_blocked'),
    re_path(r'^fetch-single-user/$', FetchSingleUser.as_view(), name='fetch_single_user'),
    re_path(r'^fetch-devices/$', FetchDevices.as_view(), name='fetch_devices'),
    re_path(r'^fetch-user-devices/$', FetchUserDevices.as_view(), name='fetch_user_devices'),
    re_path(r'^upload-pk/$', UploadPasswordKey.as_view(), name='upload_pk'),
    re_path(r'^verify-password/$', VerifyPassword.as_view(), name='verify_password'),
    re_path(r'^fetch-preferences/$', FetchPreferences.as_view(), name='fetch_preferences'),
    re_path(r'^fetch-user-categories/$', FetchUserCategories.as_view(), name='fetch_user_categories'),
    re_path(r'^fetch-user-chat-backup/$', FetchUserChatBackup.as_view(), name='fetch_user_chat_backup'),
    re_path(r'^update-chat-device/$', UpdateChatDevice.as_view(), name='update_chat_device'),
    re_path(r'^update-donation-reminder/$', UpdateDonationReminder.as_view(), name='update_donation_reminder'),
    re_path(r'^deactivate/$', DeactivateAccount.as_view(), name='deactivate_account'),
    re_path(r'^code-confirmed-delete-account/$', CodeConfirmedDeleteAccount.as_view(),
        name='code_confirmed_delete_account'),
    re_path(r'^delete-account/$', DeleteAccount.as_view(), name='delete_account'),
    re_path(r'^recreate-user/$', RecreateUser.as_view(), name='recreate_user'),
    re_path(r'^highlight-image/$', HighlightImage.as_view(), name='highlight_image'),
    re_path(r'^toggle-hide-image/$', ToggleHideImage.as_view(), name='toggle-hide_image'),
    re_path(r'^set-photo-backup-setting/$', SetPhotoBackupSetting.as_view(), name='set_photo_backup_setting'),
    re_path(r'^request-email-code/$', RequestEmailCode.as_view(), name='request_email_code'),
    re_path(r'^verify-email-code/$', VerifyEmailCode.as_view(), name='verify_email_code'),
    re_path(r'^check-user-phone-exists/$', CheckUserPhoneExists.as_view(), name='check_user_phone_exists'),
    re_path(r'^set-folder-icon/$', SetFolderIcon.as_view(), name='set_folder_icon'),
    re_path(r'^set-platform/$', SetPlatform.as_view(), name='set_platform'),
    re_path(r'^ping-server/$', PingServer.as_view(), name='ping_server'),
    re_path(r'^email-reminder/$', EmailReminder.as_view(), name='email_reminder'),
    re_path(r'^set-web-key/$', SetWebKey.as_view(), name='set_web_key'),
    re_path(r'^get-web-key/$', GetWebKey.as_view(), name='get_web_key'),
    re_path(r'^create-e2e-user/$', CreateE2EUser.as_view(), name='create_e2e_user'),
    re_path(r'^test-ip/$', TestIP.as_view(), name='test_ip'),
]
