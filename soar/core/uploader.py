# -*- coding: utf-8 -*-
"""soar.earth API client

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2022 by Nyall Dawson'
__date__ = '22/11/2022'
__copyright__ = 'Copyright 2022, North Road'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from ..external import oss2


class SoarUploader:
    """
    Handles uploading files to soar.earth
    """

    @staticmethod
    def upload_file(local_file_path: str,
                    bucket_name: str,
                    filename: str,  # pylint: disable=unused-argument
                    access_key_id: str,
                    security_token: str,
                    access_secret_key: str,
                    listing_id: int,  # pylint: disable=unused-argument
                    key: str,
                    oss_region: str
                    ):
        """
        Uploads a file to soar.earth OSS bucket
        """
        endpoint = 'https://{}.aliyuncs.com'.format(oss_region)

        auth = oss2.StsAuth(access_key_id, access_secret_key, security_token)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)

        # Upload
        with open(local_file_path, 'rb') as f:
            bucket.put_object(key, f)
