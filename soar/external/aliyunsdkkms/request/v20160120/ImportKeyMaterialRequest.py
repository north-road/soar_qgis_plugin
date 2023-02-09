# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from aliyunsdkcore.request import RpcRequest
from aliyunsdkkms.endpoint import endpoint_data

class ImportKeyMaterialRequest(RpcRequest):

	def __init__(self):
		RpcRequest.__init__(self, 'Kms', '2016-01-20', 'ImportKeyMaterial','kms')
		self.set_protocol_type('https')
		self.set_method('POST')

		if hasattr(self, "endpoint_map"):
			setattr(self, "endpoint_map", endpoint_data.getEndpointMap())
		if hasattr(self, "endpoint_regional"):
			setattr(self, "endpoint_regional", endpoint_data.getEndpointRegional())

	def get_ImportToken(self): # String
		return self.get_query_params().get('ImportToken')

	def set_ImportToken(self, ImportToken):  # String
		self.add_query_param('ImportToken', ImportToken)
	def get_EncryptedKeyMaterial(self): # String
		return self.get_query_params().get('EncryptedKeyMaterial')

	def set_EncryptedKeyMaterial(self, EncryptedKeyMaterial):  # String
		self.add_query_param('EncryptedKeyMaterial', EncryptedKeyMaterial)
	def get_KeyMaterialExpireUnix(self): # Long
		return self.get_query_params().get('KeyMaterialExpireUnix')

	def set_KeyMaterialExpireUnix(self, KeyMaterialExpireUnix):  # Long
		self.add_query_param('KeyMaterialExpireUnix', KeyMaterialExpireUnix)
	def get_KeyId(self): # String
		return self.get_query_params().get('KeyId')

	def set_KeyId(self, KeyId):  # String
		self.add_query_param('KeyId', KeyId)
