# -*- coding: utf-8 -*-

"""
Enhanced boto3 SSM client functions.

This module provides high-level, Pythonic wrapper functions around the AWS SSM
Parameter Store boto3 client operations. The functions handle error cases gracefully,
provide better return values, and implement common patterns like existence testing
and idempotent operations.
"""

import typing as T

import botocore.exceptions
from func_args.api import OPT, remove_optional

from .constants import (
    ParameterType,
    ParameterTier,
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
    Get a parameter by name with built-in existence testing.

    This function provides a convenient way to retrieve parameters while gracefully
    handling non-existent parameters. Unlike the raw boto3 client which raises
    exceptions for missing parameters, this function returns None, making it ideal
    for existence testing and conditional parameter access.

    Example usage for existence testing::

        param = get_parameter(ssm_client, "/my/param")
        if param is not None:
            print("Parameter exists")
        else:
            print("Parameter does not exist")

    Ref:

    - `get_parameter <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameter>`_

    :param ssm_client: SSM client
    :param name: parameter name (e.g., "/app/database/host")
    :param with_decryption: whether to decrypt SecureString parameter values

    :return: ``Parameter`` object if the parameter exists, None if it does not exist.
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


def put_parameter_if_changed(
    ssm_client: "SSMClient",
    name: str,
    value: str,
    description: str | None = OPT,
    type: ParameterType | None = OPT,
    tier: ParameterTier | None = OPT,
    key_id: str | None = OPT,
    overwrite: bool = False,
    allowed_pattern: str | None = OPT,
    tags: dict[str, str] | None = OPT,
    policies: str | None = OPT,
    data_type: str | None = OPT,
) -> tuple[Parameter | None, Parameter | None]:
    """
    Put a parameter only if its value has changed (conditional write).

    This function implements an optimized "get-then-put" operation that avoids
    unnecessary write operations when the parameter value hasn't changed. It first
    retrieves the current parameter value and compares it with the desired value.
    Only if they differ (or if the parameter doesn't exist) does it perform the
    actual write operation.

    **Why This Matters - Version History Preservation:**

    AWS SSM Parameter Store only retains the last 100 parameter versions. During
    development, debugging, or frequent deployments, blindly calling put_parameter()
    can rapidly consume this version history - even when values haven't actually
    changed. This can make older parameter versions permanently inaccessible.

    Consider a debugging scenario where you run a deployment script 50 times with
    the same configuration values. Without conditional updates, you've just consumed
    50% of your version history for no benefit. This function prevents such waste.

    **Additional Benefits:**

    - **Performance**: Reduces unnecessary API calls and write operations
    - **Change tracking**: Returns clear indication of whether a write occurred
    - **Audit efficiency**: Minimizes noise in CloudTrail logs from no-op updates
    - **Version conservation**: Preserves parameter version history for actual changes

    The function handles SecureString parameters correctly by automatically enabling
    decryption when comparing values, ensuring accurate change detection even for
    encrypted parameters.

    Example usage::

        # Create or update parameter only if value changed
        before, after = put_parameter_if_changed(
            ssm_client=client,
            name="/app/database/host",
            value="new-db-host.example.com",
            type=ParameterType.STRING
        )

        if after is not None:
            print(f"Parameter updated: version {after.version}")
        else:
            print("No update needed - value unchanged")

    Return value interpretation:

    - ``(None, Parameter)``: Parameter didn't exist, was created
    - ``(Parameter, None)``: Parameter existed with same value, no update
    - ``(Parameter, Parameter)``: Parameter existed with different value, was updated

    Ref:

    - `put_parameter <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.put_parameter>`_

    :param ssm_client: SSM client
    :param name: parameter name (e.g., "/app/database/host")
    :param value: parameter value to set
    :param description: parameter description
    :param type: parameter type (String, StringList, SecureString)
    :param tier: parameter tier (Standard, Advanced, Intelligent-Tiering)
    :param key_id: KMS key ID for SecureString encryption
    :param overwrite: whether to overwrite existing parameter (required for updates)
    :param allowed_pattern: regex pattern for parameter validation
    :param tags: dictionary of tag key-value pairs
    :param policies: parameter policies (JSON string)
    :param data_type: parameter data type (e.g., "text", "aws:ec2:image")

    :returns: Tuple of (before_parameter, after_parameter) where:
        - before_parameter: Parameter object before operation (None if didn't exist)
        - after_parameter: Parameter object after operation (None if no write occurred)
    """
    # Determine if decryption is needed for SecureString comparison
    if isinstance(type, ParameterType):
        with_decryption = type is ParameterType.SECURE_STRING
    else:  # pragma: no cover
        with_decryption = False

    # Get current parameter value to compare against desired value
    before_param = get_parameter(ssm_client, name, with_decryption=with_decryption)

    # Determine if write operation is needed
    if before_param is not None:
        # Parameter exists - only write if value has changed
        should_write = not (value == before_param.value)
    else:
        # Parameter doesn't exist - always write
        should_write = True

    if should_write:
        # Prepare parameters for put_parameter API call
        kwargs = dict(
            Name=name,
            Value=value,
            Description=description,
            Type=type.value if isinstance(type, ParameterType) else type,
            Tier=tier.value if isinstance(tier, ParameterTier) else tier,
            KeyId=key_id,
            Overwrite=overwrite,
            AllowedPattern=allowed_pattern,
            Tags=encode_tags(tags) if isinstance(tags, dict) else tags,
            Policies=policies,
            DataType=data_type,
        )

        # Execute the parameter write operation
        response = ssm_client.put_parameter(**remove_optional(**kwargs))

        # Construct Parameter object from put_parameter response and input data
        # Note: put_parameter response only contains Version and Tier, not full parameter data
        param_data = dict(
            Name=name,
            Value=value,
            Description=description,
            Type=type.value if isinstance(type, ParameterType) else type,
            Tier=tier.value if isinstance(tier, ParameterTier) else tier,
        )
        param_data = remove_optional(**param_data)
        param_data.update(response)
        after_param = Parameter(_data=param_data)
    else:
        # No write needed - value hasn't changed
        after_param = None

    return before_param, after_param


def delete_parameter(
    ssm_client: "SSMClient",
    name: str,
) -> bool:
    """
    Delete a parameter by name with idempotent behavior.

    This function provides idempotent parameter deletion - it can be called multiple
    times safely without raising errors. Unlike the raw boto3 client which raises
    ParameterNotFound exceptions, this function returns False for non-existent
    parameters, making it safe to use in cleanup operations and automation scripts.

    The idempotent behavior ensures that:

    - If the parameter exists, it will be deleted and return True
    - If the parameter doesn't exist, it returns False without raising an error
    - Multiple calls with the same parameter name are safe

    Example usage in cleanup scripts::

        # Safe to call even if parameter doesn't exist
        deleted = delete_parameter(client, "/app/temp/config")
        if deleted:
            print("Parameter was deleted")
        else:
            print("Parameter did not exist")

    Ref:

    - `delete_parameter <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.delete_parameter>`_

    :param ssm_client: SSM client
    :param name: parameter name (e.g., "/app/database/host")

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
    Get all tags associated with a parameter.

    This function retrieves all tags for the specified parameter and returns them
    as a convenient key-value dictionary. If the parameter has no tags, an empty
    dictionary is returned.

    Ref:

    - `list_tags_for_resource <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.list_tags_for_resource>`_

    :param ssm_client: SSM client
    :param name: parameter name (e.g., "/app/database/host")

    :return: Dictionary of tag key-value pairs. Empty dict if parameter has no tags.
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
    Remove specific tags from a parameter by tag keys.

    This function removes only the specified tag keys from the parameter, leaving
    other tags unchanged. It's useful for selective tag cleanup without affecting
    the entire tag set.

    Example:
        # Remove only the "Environment" and "Team" tags
        remove_parameter_tags(client, "/app/config", ["Environment", "Team"])

    Ref:

    - `remove_tags_from_resource <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.remove_tags_from_resource>`_

    :param ssm_client: SSM client
    :param name: parameter name (e.g., "/app/database/host")
    :param tag_keys: list of tag keys to remove (e.g., ["Environment", "Team"])
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
    Add or update specific tags on a parameter (partial update).

    This function performs a partial update of parameter tags. It adds new tags
    and updates existing tags with the provided key-value pairs, while leaving
    other existing tags unchanged. This is useful for adding metadata without
    affecting the entire tag set.

    Example:
        # Add/update only specific tags, keeping others intact
        update_parameter_tags(client, "/app/config", {
            "Environment": "production",
            "LastUpdated": "2024-01-15"
        })

    Ref:

    - `add_tags_to_resource <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.add_tags_to_resource>`_

    :param ssm_client: SSM client
    :param name: parameter name (e.g., "/app/database/host")
    :param tags: dictionary of tag key-value pairs to add/update
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
    Replace all parameter tags with the provided tag set (full replacement).

    This function performs a complete replacement of all parameter tags. It removes
    all existing tags and replaces them with the provided tags. If an empty
    dictionary is provided, all tags are removed from the parameter.

    Behavior:

    - Empty dict: Remove all existing tags from the parameter
    - Non-empty dict: Replace all existing tags with the provided tags

    Example::

        # Replace all tags with new set
        put_parameter_tags(client, "/app/config", {
            "Environment": "production",
            "Owner": "platform-team"
        })

        # Remove all tags
        put_parameter_tags(client, "/app/config", {})

    Ref:

    - `add_tags_to_resource <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.add_tags_to_resource>`_

    :param ssm_client: SSM client
    :param name: parameter name (e.g., "/app/database/host")
    :param tags: dictionary of tag key-value pairs to set (empty dict removes all tags)
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
