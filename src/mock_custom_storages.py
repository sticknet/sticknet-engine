
from unittest.mock import Mock

class S3:
    def __init__(self):
        self.client = Mock()
        self.client.generate_presigned_url.return_value = 'http://example.com/presigned_url'
        self.client.delete_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 204}}

    def get_presigned_url(self, key, time=3600):
        return self.client.generate_presigned_url(
            ClientMethod='put_object',
            ExpiresIn=time,
            Params={'Bucket': 'mock_bucket', 'Key': key}
        )

    def get_file(self, key, time=3600):
        return self.client.generate_presigned_url(
            ClientMethod='get_object',
            ExpiresIn=time,
            Params={'Bucket': 'mock_bucket', 'Key': key}
        )

    def delete_file(self, key):
        return self.client.delete_object(
            Bucket='mock_bucket',
            Key=key
        )

