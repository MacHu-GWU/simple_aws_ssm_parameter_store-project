# -*- coding: utf-8 -*-

"""
Data Model.
"""

import typing as T
import dataclasses
from datetime import datetime
from func_args.api import BaseFrozenModel
from func_args.api import T_KWARGS

from .constants import ParameterType
from .constants import ParameterTier


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
        """
        Parameter name, such as ``/app/database/host``.
        """
        return self._data["Name"]

    @property
    def type(self) -> str | None:
        """
        Parameter type: ``String``, ``StringList``, or ``SecureString``.
        """
        return self._data.get("Type")

    @property
    def tier(self) -> str | None:
        """
        Parameter tier: ``Standard`` or ``Advanced``. Not returned by ``get_parameter``.
        """
        return self._data.get("Tier")

    @property
    def value(self) -> str | None:
        """
        Parameter value. A ``SecureString`` read without decryption holds the encrypted value.
        """
        return self._data.get("Value")

    @property
    def version(self) -> int | None:
        """
        Parameter version, starting at 1 and increased by every write.
        """
        return self._data.get("Version")

    @property
    def selector(self) -> str | None:
        """
        The version or label suffix of the requested name, such as ``:3``.
        """
        return self._data.get("Selector")

    @property
    def source_result(self) -> str | None:
        """
        For a parameter that references another AWS resource, the raw result of that reference.
        """
        return self._data.get("SourceResult")

    @property
    def last_modified_date(self) -> datetime | None:
        """
        When the parameter was last written.
        """
        return self._data.get("LastModifiedDate")

    @property
    def arn(self) -> str | None:
        """
        Parameter ARN.
        """
        return self._data.get("ARN")

    @property
    def data_type(self) -> str | None:
        """
        Data type of a ``String`` parameter: ``text``, ``aws:ec2:image``, or ``aws:ssm:integration``.
        """
        return self._data.get("DataType")

    @property
    def key_id(self) -> str | None:
        """
        KMS key of a ``SecureString`` parameter. Only returned by ``describe_parameters``.
        """
        return self._data.get("KeyId")

    @property
    def last_modified_user(self) -> str | None:
        """
        ARN of the identity that last wrote the parameter. Only returned by ``describe_parameters``.
        """
        return self._data.get("LastModifiedUser")

    @property
    def description(self) -> str | None:
        """
        Parameter description. Only returned by ``describe_parameters``.
        """
        return self._data.get("Description")

    @property
    def allowed_pattern(self) -> str | None:
        """
        Regular expression the value must match. Only returned by ``describe_parameters``.
        """
        return self._data.get("AllowedPattern")

    @property
    def policies(self) -> list[dict[str, str]] | None:
        """
        Parameter policies. Only returned by ``describe_parameters``.
        """
        return self._data.get("Policies")

    @property
    def aws_account_id(self) -> str:
        """
        AWS account ID, parsed from :attr:`arn`.
        """
        return self.arn.split(":")[4]

    @property
    def aws_region(self) -> str:
        """
        AWS region, parsed from :attr:`arn`.
        """
        return self.arn.split(":")[3]

    @property
    def is_string_type(self) -> bool:
        """
        Whether the parameter is a ``String``.
        """
        return self.type == ParameterType.STRING

    @property
    def is_string_list_type(self) -> bool:
        """
        Whether the parameter is a ``StringList``.
        """
        return self.type == ParameterType.STRING_LIST

    @property
    def is_secure_string_type(self) -> bool:
        """
        Whether the parameter is a ``SecureString``.
        """
        return self.type == ParameterType.SECURE_STRING

    @property
    def is_standard_tier(self) -> bool:
        """
        Whether the parameter is in the Standard tier.
        """
        return self.tier == ParameterTier.STANDARD

    @property
    def is_advanced_tier(self) -> bool:
        """
        Whether the parameter is in the Advanced tier.
        """
        return self.tier == ParameterTier.ADVANCED

    @property
    def is_intelligent_tiering(self) -> bool:
        """
        Whether the parameter tier is ``Intelligent-Tiering``.
        """
        return self.tier == ParameterTier.INTELLIGENT_TIERING

    @property
    def core_data(self) -> T_KWARGS:
        """
        Essential parameter information in standardized format.
        """
        return {
            "name": self.name,
            "type": self.type,
            "tier": self.tier,
            "version": self.version,
            "last_modified_date": self.last_modified_date,
            "arn": self.arn,
        }
