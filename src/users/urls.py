from django.conf.urls import url, include
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
    PingServer, EmailReminder

router = routers.SimpleRouter()
router.register('users', UserViewSet, basename='users')
router.register('profile-picture', ProfilePictureViewSet, basename='profile_picture')
router.register('profile-cover', ProfileCoverViewSet, basename='profile_cover')

app_name = 'users'
urlpatterns = [
    url('^', include(router.urls)),
    url(r'^get-app-settings/$', GetAppSettings.as_view(), name='get_app_settings'),
    url('^refresh-user/$', RefreshUser.as_view()),
    url(r'^check-username/$', CheckUsername.as_view(), name='check_username'),
    url(r'^search/$', UserSearch.as_view(), name='search'),
    url(r'^phone-verified/$', PhoneVerified.as_view(), name='phone_verified'),
    url(r'^register/$', Register.as_view(), name='register'),
    url(r'^update-contacts/$', UpdateContacts.as_view(), name='update_contacts'),
    url(r'^upload-categories/$', UploadCategories.as_view(), name='upload_categories'),
    url(r'^backup-chats/$', BackupChats.as_view(), name='backup_chats'),
    url(r'^delete-chat-backup/$', DeleteChatBackup.as_view(), name='delete_chat_backup'),
    url(r'^update-backup-freq/$', UpdateBackupFreq.as_view(), name='update_backup_freq'),
    url(r'^block/$', BlockUser.as_view(), name='block'),
    url(r'^unblock/$', UnblockUser.as_view(), name='unblock'),
    url(r'^fetch-blocked/$', FetchBlockedAccounts.as_view(), name='fetch_blocked'),
    url(r'^fetch-single-user/$', FetchSingleUser.as_view(), name='fetch_single_user'),
    url(r'^fetch-devices/$', FetchDevices.as_view(), name='fetch_devices'),
    url(r'^fetch-user-devices/$', FetchUserDevices.as_view(), name='fetch_user_devices'),
    url(r'^upload-pk/$', UploadPasswordKey.as_view(), name='upload_pk'),
    url(r'^verify-password/$', VerifyPassword.as_view(), name='verify_password'),
    url(r'^fetch-preferences/$', FetchPreferences.as_view(), name='fetch_preferences'),
    url(r'^fetch-user-categories/$', FetchUserCategories.as_view(), name='fetch_user_categories'),
    url(r'^fetch-user-chat-backup/$', FetchUserChatBackup.as_view(), name='fetch_user_chat_backup'),
    url(r'^update-chat-device/$', UpdateChatDevice.as_view(), name='update_chat_device'),
    url(r'^update-donation-reminder/$', UpdateDonationReminder.as_view(), name='update_donation_reminder'),
    url(r'^deactivate/$', DeactivateAccount.as_view(), name='deactivate_account'),
    url(r'^code-confirmed-delete-account/$', CodeConfirmedDeleteAccount.as_view(),
        name='code_confirmed_delete_account'),
    url(r'^delete-account/$', DeleteAccount.as_view(), name='delete_account'),
    url(r'^recreate-user/$', RecreateUser.as_view(), name='recreate_user'),
    url(r'^highlight-image/$', HighlightImage.as_view(), name='highlight_image'),
    url(r'^toggle-hide-image/$', ToggleHideImage.as_view(), name='toggle-hide_image'),
    url(r'^set-photo-backup-setting/$', SetPhotoBackupSetting.as_view(), name='set_photo_backup_setting'),
    url(r'^request-email-code/$', RequestEmailCode.as_view(), name='request_email_code'),
    url(r'^verify-email-code/$', VerifyEmailCode.as_view(), name='verify_email_code'),
    url(r'^check-user-phone-exists/$', CheckUserPhoneExists.as_view(), name='check_user_phone_exists'),
    url(r'^set-folder-icon/$', SetFolderIcon.as_view(), name='set_folder_icon'),
    url(r'^set-platform/$', SetPlatform.as_view(), name='set_platform'),
    url(r'^ping-server/$', PingServer.as_view(), name='ping_server'),
    url(r'^email-reminder/$', EmailReminder.as_view(), name='email_reminder'),
    url(r'^create-e2e-user/$', CreateE2EUser.as_view(), name='create_e2e_user'),
]
