# -*- coding: utf-8 -*-

"""
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html
"""

import typing as T
import enum
import dataclasses
from func_args.api import REQ, OPT, remove_optional, BaseFrozenModel


class ParameterType(str, enum.Enum):
    """
    See `What is a parameter? <https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html#what-is-a-parameter>`_
    """

    STRING = "String"
    STRING_LIST = "StringList"
    SECURE_STRING = "SecureString"


class ParameterTier(str, enum.Enum):
    """
    See `Parameter tiers <https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html>`_
    """

    STANDARD = "Standard"
    ADVANCED = "Advanced"
    INTELLIGENT_TIERING = "Intelligent-Tiering"


@dataclasses.dataclass(frozen=True)
class Parameter(BaseFrozenModel):
    """

    - `get_parameter <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/get_parameter.html>`_
    - `describe_parameters <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/describe_parameters.html>`_
    - `put_parameter <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/put_parameter.html>`_

    get_parameter
    {
        'Name': 'string',
        'Type': 'String'|'StringList'|'SecureString',
        'Value': 'string',
        'Version': 123,
        'Selector': 'string',
        'SourceResult': 'string',
        'LastModifiedDate': datetime(2015, 1, 1),
        'ARN': 'string',
        'DataType': 'string'
    }
    describe_parameters
    {
        'Name': 'string',
        'ARN': 'string',
        'Type': 'String'|'StringList'|'SecureString',
        'KeyId': 'string',
        'LastModifiedDate': datetime(2015, 1, 1),
        'LastModifiedUser': 'string',
        'Description': 'string',
        'AllowedPattern': 'string',
        'Version': 123,
        'Tier': 'Standard'|'Advanced'|'Intelligent-Tiering',
        'Policies': [
            {
                'PolicyText': 'string',
                'PolicyType': 'string',
                'PolicyStatus': 'string'
            },
        ],
        'DataType': 'string'
    }
    put_parameter
    {
        'Version': 123,
        'Tier': 'Standard'|'Advanced'|'Intelligent-Tiering'
    }
    """

    _data: dict[str, T.Any] = dataclasses.field()

    @property
    def response(self) -> dict[str, T.Any]:
        """
        The raw response from the AWS SSM Parameter Store API.
        """
        return self._data

    @property
    def name(self) -> str:
        return self._data["Name"]

    @property
    def type(self) -> str | None:
        return self._data.get("Type")

    @property
    def tier(self) -> str | None:
        return self._data.get("Tier")
