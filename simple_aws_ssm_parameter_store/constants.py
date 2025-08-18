# -*- coding: utf-8 -*-

import enum


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
