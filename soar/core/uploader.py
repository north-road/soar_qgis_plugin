from ..external import oss2


class SoarUploader:

    def __init__(self):
        pass

    @staticmethod
    def upload_file(local_file_path: str,
                    bucket_name: str,
                    filename: str,
                    access_key_id: str,
                    security_token: str,
                    access_secret_key: str,
                    listing_id: int,
                    key: str,
                    oss_region: str
                    ):

        endpoint = 'https://{}.aliyuncs.com'.format(oss_region)

        auth = oss2.StsAuth(access_key_id, access_secret_key, security_token)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)

        # Upload
        with open(local_file_path, 'rb') as f:
            bucket.put_object(key, f)
