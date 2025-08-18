# -*- coding: utf-8 -*-

import typing as T

from .model import (
    ParameterType,
    ParameterTier,
    Parameter,
)

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_ssm.client import SSMClient
