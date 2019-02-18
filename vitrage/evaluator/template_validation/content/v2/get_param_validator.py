# Copyright 2019 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from vitrage.evaluator.template_functions.function_resolver import \
    FuncInfo
from vitrage.evaluator.template_functions.function_resolver import \
    FunctionResolver
from vitrage.evaluator.template_functions import GET_PARAM
from vitrage.evaluator.template_functions.v2.functions import get_param


class GetParamValidator(object):

    @classmethod
    def validate(cls, template, actual_params):
        return FunctionResolver().validate_function(
            func_info=FuncInfo(name=GET_PARAM, func=get_param, error_code=160),
            template=template,
            actual_params=actual_params)