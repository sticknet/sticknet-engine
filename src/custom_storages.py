import os
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage, _cloud_front_signer_from_pem


class StaticStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STATIC_BUCKET_NAME
    location = settings.STATICFILES_LOCATION
    custom_domain = os.environ['STATIC_CDN']


class PublicStorage(S3Boto3Storage):
    bucket_name = settings.AWS_PUBLIC_BUCKET_NAME
    location = settings.PUBLICFILES_LOCATION
    custom_domain = os.environ['PUBLIC_CDN']

if not settings.TESTING:
    with open(os.environ['AWS_CLOUDFRONT_KEY'], 'rb') as sk:
        data = sk.read()

class MediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = settings.MEDIAFILES_LOCATION
    custom_domain = os.environ['CDN']
    cloudfront_signer = _cloud_front_signer_from_pem(os.environ['AWS_CLOUDFRONT_KEY_ID'], data) if not settings.DEBUG else None



from django.conf import settings
import boto3
from botocore.config import Config

class S3:
    def __init__(self):
        self.client = boto3.client('s3',
                                   'eu1',
                                   aws_access_key_id=os.environ['STORJ_ACCESS_KEY_ID'],
                                   aws_secret_access_key=os.environ['STORJ_SECRET_ACCESS_KEY'],
                                   endpoint_url=os.environ['STORJ_URL'],
                                   config=Config(signature_version='s3v4'))

    def get_presigned_url(self, key, time=3600):
        return self.client.generate_presigned_url(ClientMethod='put_object', ExpiresIn=time,
                                                  Params={'Bucket': settings.STORJ_BUCKET_NAME, 'Key':  key})

    def get_file(self, key, time=3600):
        return self.client.generate_presigned_url(ClientMethod='get_object', ExpiresIn=time,
                                                  Params={'Bucket': settings.STORJ_BUCKET_NAME, 'Key':  key})

    def delete_file(self, key):
        return self.client.delete_object(Bucket=settings.STORJ_BUCKET_NAME, Key=key)

########################################################################################################################

# # Usage example:
# mock_s3 = MockS3()
#
# # Mock responses for the client methods
# mock_s3.client.generate_presigned_url.return_value = 'http://example.com/presigned_url'
# mock_s3.client.delete_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 204}}
