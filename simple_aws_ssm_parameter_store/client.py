# -*- coding: utf-8 -*-

import typing as T

import botocore.exceptions
from func_args.api import remove_optional

from .constants import (
    ResourceType,
)
from .utils import (
    encode_tags,
    decode_tags,
)
from .model import (
    Parameter,
)

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_ssm.client import SSMClient


def get_parameter(
    ssm_client: "SSMClient",
    name: str,
    with_decryption: bool = False,
) -> Parameter | None:
    """
    Get a parameter by name.

    Ref:

    - `get_parameter <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameter>`_

    :param ssm_client: SSM client
    :param name: parameter name
    :param with_decryption: whether to decrypt the parameter value

    :return: ``Parameter`` object, or None if the parameter does not exist.
    """
    try:
        response = ssm_client.get_parameter(
            Name=name,
            **remove_optional(
                WithDecryption=with_decryption,
            ),
        )
        return Parameter(_data=response["Parameter"])
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] in [
            "ParameterNotFound",
            "ParameterVersionNotFound",
        ]:
            return None
        raise  # pragma: no cover


def delete_parameter(
    ssm_client: "SSMClient",
    name: str,
) -> bool:
    """
    Delete a parameter by name.

    Ref:

    - `delete_parameter <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.delete_parameter>`_

    :param ssm_client: SSM client
    :param name: parameter name

    :return: True if the parameter was deleted, False if it did not exist.
    """
    try:
        ssm_client.delete_parameter(Name=name)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ParameterNotFound":
            return False
        raise  # pragma: no cover


def get_parameter_tags(
    ssm_client: "SSMClient",
    name: str,
) -> dict[str, str]:
    """
    Get parameter tags.

    Ref:

    - `list_tags_for_resource <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.list_tags_for_resource>`_

    :return: return empty dict if parameter doesn't have tags. otherwise,
        return tags in format of key value dict.
    """
    response = ssm_client.list_tags_for_resource(
        ResourceType=ResourceType.PARAMETER.value,
        ResourceId=name,
    )
    return decode_tags(response.get("TagList", []))


def remove_parameter_tags(
    ssm_client: "SSMClient",
    name: str,
    tag_keys: list[str],
):
    """
    Delete parameter tags.

    Ref:

    - `remove_tags_from_resource <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.remove_tags_from_resource>`_
    """
    return ssm_client.remove_tags_from_resource(
        ResourceType=ResourceType.PARAMETER.value,
        ResourceId=name,
        TagKeys=tag_keys,
    )


def update_parameter_tags(
    ssm_client: "SSMClient",
    name: str,
    tags: dict[str, str],
):
    """
    Create or update (partial update) tags.

    Ref:

    - `add_tags_to_resource <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.add_tags_to_resource>`_
    """
    return ssm_client.add_tags_to_resource(
        ResourceType=ResourceType.PARAMETER.value,
        ResourceId=name,
        Tags=encode_tags(tags),
    )


def put_parameter_tags(
    ssm_client: "SSMClient",
    name: str,
    tags: dict[str, str],
):
    """
    Full replacement update tags.

    - if empty dict, then delete all tags
    - if non-empty dict, then do full replacement update

    Ref:

    - `add_tags_to_resource <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.add_tags_to_resource>`_
    """
    existing_tags = get_parameter_tags(ssm_client, name)

    if len(tags) == 0:
        if len(existing_tags):  # only run remove tags when there are existing tags
            remove_parameter_tags(ssm_client, name, list(existing_tags))
    else:
        # if to-update tags is super set of the existing tags
        # then no need to run remove tags
        # otherwise, need to run remove tags
        if not (len(set(existing_tags).difference(set(tags))) == 0):
            remove_parameter_tags(ssm_client, name, list(existing_tags))
        ssm_client.add_tags_to_resource(
            ResourceType="Parameter",
            ResourceId=name,
            Tags=encode_tags(tags),
        )
