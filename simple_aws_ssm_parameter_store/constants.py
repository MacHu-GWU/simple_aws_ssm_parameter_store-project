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


class ResourceType(str, enum.Enum):
    """
    Resource type parameter value enum for:

    - `list_tags_for_resource <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.list_tags_for_resource>`_
    """

    DOCUMENT = "Document"
    MANAGED_INSTANCE = "ManagedInstance"
    MAINTENANCE_WINDOW = "MaintenanceWindow"
    PARAMETER = "Parameter"
    PATCH_BASELINE = "PatchBaseline"
    OPS_ITEM = "OpsItem"
    OPS_METADATA = "OpsMetadata"
    AUTOMATION = "Automation"
    ASSOCIATION = "Association"


DEFAULT_KMS_KEY = "alias/aws/ssm"
