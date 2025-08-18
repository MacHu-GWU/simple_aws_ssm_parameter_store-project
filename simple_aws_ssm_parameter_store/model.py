# -*- coding: utf-8 -*-

"""
Data Model.
"""

import typing as T
import dataclasses
from datetime import datetime
from func_args.api import BaseFrozenModel, T_KWARGS

from .constants import ParameterType, ParameterTier


@dataclasses.dataclass(frozen=True)
class Parameter(BaseFrozenModel):
    """
    Represents a parameter in AWS SSM Parameter Store.

    - `get_parameter <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/get_parameter.html>`_
    - `get_parameters <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/get_parameters.html>`_
    - `describe_parameters <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/describe_parameters.html>`_
    - `put_parameter <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/put_parameter.html>`_
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

    @property
    def value(self) -> str | None:
        return self._data.get("Value")

    @property
    def version(self) -> int | None:
        return self._data.get("Version")

    @property
    def selector(self) -> str | None:
        return self._data.get("Selector")

    @property
    def source_result(self) -> str | None:
        return self._data.get("SourceResult")

    @property
    def last_modified_date(self) -> datetime | None:
        return self._data.get("LastModifiedDate")

    @property
    def arn(self) -> str | None:
        return self._data.get("ARN")

    @property
    def data_type(self) -> str | None:
        return self._data.get("DataType")

    @property
    def key_id(self) -> str | None:
        return self._data.get("KeyId")

    @property
    def last_modified_user(self) -> str | None:
        """Last modified user (from describe_parameters)"""
        return self._data.get("LastModifiedUser")

    @property
    def description(self) -> str | None:
        return self._data.get("Description")

    @property
    def allowed_pattern(self) -> str | None:
        return self._data.get("AllowedPattern")

    @property
    def policies(self) -> T.List[T.Dict[str, str]] | None:
        return self._data.get("Policies")

    @property
    def aws_account_id(self) -> str:
        return self.arn.split(":")[4]

    @property
    def aws_region(self) -> str:
        return self.arn.split(":")[3]

    @property
    def is_string_type(self) -> bool:
        return self.type == ParameterType.STRING

    @property
    def is_string_list_type(self) -> bool:
        return self.type == ParameterType.STRING_LIST

    @property
    def is_secure_string_type(self) -> bool:
        return self.type == ParameterType.SECURE_STRING

    @property
    def is_standard_tier(self) -> bool:
        return self.tier == ParameterTier.STANDARD

    @property
    def is_advanced_tier(self) -> bool:
        return self.tier == ParameterTier.ADVANCED

    @property
    def is_intelligent_tiering(self) -> bool:
        return self.tier == ParameterTier.INTELLIGENT_TIERING

    @property
    def core_data(self) -> T_KWARGS:
        """Essential parameter information in standardized format"""
        return {
            "name": self.name,
            "type": self.type,
            "tier": self.tier,
            "version": self.version,
            "last_modified_date": self.last_modified_date,
            "arn": self.arn,
        }
