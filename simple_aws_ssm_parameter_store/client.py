# -*- coding: utf-8 -*-

"""
Enhanced boto3 SSM client functions.

This module provides high-level, Pythonic wrapper functions around the AWS SSM
Parameter Store boto3 client operations. The functions handle error cases gracefully,
provide better return values, and implement common patterns like existence testing
and idempotent operations.
"""

import typing as T
import json

import botocore.exceptions
from func_args.api import OPT
from func_args.api import remove_optional

from .constants import ParameterType
from .constants import ParameterTier
from .constants import ResourceType
from .utils import encode_tags
from .utils import decode_tags
from .model import Parameter

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


def _get_parameter_metadata(
    ssm_client: "SSMClient",
    name: str,
) -> dict[str, T.Any]:
    """
    Get the metadata of a parameter that ``get_parameter`` does not return,
    such as ``Description``, ``Tier``, ``KeyId``, ``AllowedPattern``, and ``Policies``.

    Ref:

    - `describe_parameters <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.describe_parameters>`_

    :param ssm_client: SSM client
    :param name: parameter name (e.g., "/app/database/host")

    :return: The ``describe_parameters`` item of the parameter, or an empty dict
        if the parameter does not exist.
    """
    response = ssm_client.describe_parameters(
        ParameterFilters=[
            {
                "Key": "Name",
                "Option": "Equals",
                "Values": [name],
            },
        ],
    )
    for item in response.get("Parameters", []):
        if item["Name"] == name:
            return item
    return {}


def _is_same_policies(
    desired: str,
    current: list[dict[str, str]] | None,
) -> bool:
    """
    Compare the ``Policies`` JSON string passed to ``put_parameter`` with the
    ``Policies`` list returned by ``describe_parameters``, ignoring key order
    and policy order.

    :param desired: the JSON array string to pass to ``put_parameter``
    :param current: the ``Policies`` list of a ``describe_parameters`` item

    :return: True only if both hold the same policies. Anything that cannot be
        parsed counts as different, so the caller writes rather than skips.
    """
    try:
        desired_policies = json.loads(desired)
        if isinstance(desired_policies, dict):
            desired_policies = [desired_policies]
        current_policies = []
        for policy in current or []:
            current_policies.append(json.loads(policy["PolicyText"]))
        desired_keys = sorted(json.dumps(p, sort_keys=True) for p in desired_policies)
        current_keys = sorted(json.dumps(p, sort_keys=True) for p in current_policies)
    except (ValueError, KeyError, TypeError):
        return False
    return desired_keys == current_keys


def _is_parameter_changed(
    ssm_client: "SSMClient",
    before_param: Parameter,
    value: str,
    description: str | None = OPT,
    type: str | None = OPT,
    tier: str | None = OPT,
    key_id: str | None = OPT,
    allowed_pattern: str | None = OPT,
    policies: str | None = OPT,
    data_type: str | None = OPT,
) -> bool:
    """
    Check whether an existing parameter differs from the desired state.

    Only the arguments that are passed are compared; an argument left as ``OPT``
    means "keep whatever is there". ``describe_parameters`` is called only when
    one of the fields it alone returns is passed.

    :param before_param: the current parameter, read with decryption
    :param type: the parameter type as a plain string (e.g. "SecureString")
    :param tier: the parameter tier as a plain string (e.g. "Standard")

    :return: True if ``put_parameter`` has to be called.
    """
    if value != before_param.value:
        return True
    if type is not OPT and type != before_param.type:
        return True
    if data_type is not OPT and data_type != before_param.data_type:
        return True

    # These fields are only returned by describe_parameters
    metadata_args = [description, tier, key_id, allowed_pattern, policies]
    if all(arg is OPT for arg in metadata_args):
        return False
    metadata = _get_parameter_metadata(ssm_client, before_param.name)
    if description is not OPT and description != metadata.get("Description", ""):
        return True
    # An Intelligent-Tiering parameter is stored as Standard or Advanced,
    # so there is nothing to compare it with
    if tier is not OPT and tier != ParameterTier.INTELLIGENT_TIERING.value:
        if tier != metadata.get("Tier"):
            return True
    if key_id is not OPT and key_id != metadata.get("KeyId"):
        return True
    if allowed_pattern is not OPT:
        if allowed_pattern != metadata.get("AllowedPattern", ""):
            return True
    if policies is not OPT:
        if not _is_same_policies(policies, metadata.get("Policies")):
            return True
    return False


def _put_parameter_if_changed(
    ssm_client: "SSMClient",
    name: str,
    value: str,
    description: str | None = OPT,
    type: str | None = OPT,
    tier: str | None = OPT,
    key_id: str | None = OPT,
    allowed_pattern: str | None = OPT,
    tags: dict[str, str] | None = OPT,
    policies: str | None = OPT,
    data_type: str | None = OPT,
) -> tuple[Parameter | None, Parameter | None]:
    """
    One read-compare-write round of :func:`put_parameter_if_changed`, with
    ``type`` and ``tier`` already converted to plain strings.

    It raises the ``ParameterAlreadyExists`` error when another writer creates
    the parameter between the read and the write.
    """
    # Always decrypt: the flag is ignored for String and StringList, and a
    # SecureString can only be compared by its plain value
    before_param = get_parameter(ssm_client, name, with_decryption=True)
    is_param_exists = before_param is not None

    if is_param_exists:
        should_write = _is_parameter_changed(
            ssm_client=ssm_client,
            before_param=before_param,
            value=value,
            description=description,
            type=type,
            tier=tier,
            key_id=key_id,
            allowed_pattern=allowed_pattern,
            policies=policies,
            data_type=data_type,
        )
    else:
        should_write = True

    if should_write is False:
        return before_param, None

    kwargs = dict(
        Name=name,
        Value=value,
        Description=description,
        Type=type,
        Tier=tier,
        KeyId=key_id,
        AllowedPattern=allowed_pattern,
        Policies=policies,
        DataType=data_type,
    )
    if is_param_exists:
        # put_parameter does not accept Tags together with Overwrite;
        # the caller syncs the tags of an existing parameter separately
        kwargs["Overwrite"] = True
    elif isinstance(tags, dict) and len(tags):
        kwargs["Tags"] = encode_tags(tags)
    # Without Overwrite, this fails with ParameterAlreadyExists instead of
    # replacing a parameter that another writer has just created
    response = ssm_client.put_parameter(**remove_optional(**kwargs))

    # put_parameter only returns Version and Tier, so build the rest from the input
    if type is OPT and is_param_exists:
        type = before_param.type
    param_data = dict(
        Name=name,
        Value=value,
        Description=description,
        Type=type,
        Tier=tier,
    )
    param_data = remove_optional(**param_data)
    param_data.update(response)
    after_param = Parameter(_data=param_data)
    return before_param, after_param


def put_parameter_if_changed(
    ssm_client: "SSMClient",
    name: str,
    value: str,
    description: str | None = OPT,
    type: ParameterType | None = OPT,
    tier: ParameterTier | None = OPT,
    key_id: str | None = OPT,
    allowed_pattern: str | None = OPT,
    tags: dict[str, str] | None = OPT,
    policies: str | None = OPT,
    data_type: str | None = OPT,
) -> tuple[Parameter | None, Parameter | None]:
    """
    Make a parameter match the desired state, writing a new version only when
    something actually changed (conditional write).

    The function reads the parameter, compares it with the arguments you pass,
    and calls ``put_parameter`` only if the parameter does not exist or differs.
    Running it again with the same arguments writes nothing.

    **Why This Matters - Version History Preservation:**

    AWS SSM Parameter Store only retains the last 100 parameter versions. During
    development, debugging, or frequent deployments, blindly calling put_parameter()
    can rapidly consume this version history - even when values haven't actually
    changed. This can make older parameter versions permanently inaccessible.

    **What is compared:**

    - ``value``, always. The current value is read with decryption, so a
      ``SecureString`` is compared by its plain value whether or not you pass
      ``type``. This needs ``kms:Decrypt`` on its KMS key.
    - ``description``, ``type``, ``tier``, ``key_id``, ``allowed_pattern``,
      ``policies``, and ``data_type``, but only the ones you pass. An argument you
      leave out keeps whatever the parameter has. ``tier=INTELLIGENT_TIERING``
      is not compared, because AWS stores such a parameter as Standard or Advanced.

    **Tags:**

    When you pass ``tags``, they become the parameter's full tag set: on create
    they are sent with ``put_parameter``; on an existing parameter they are
    replaced with :func:`put_parameter_tags`, only if they differ. Tag changes
    do not create a parameter version. Leave ``tags`` out to keep the tags as they are.

    **Concurrency:**

    The read and the write are separate calls, and SSM has no conditional write,
    so this is a best effort. If another writer creates the parameter between
    the read and the write, the create fails with ``ParameterAlreadyExists``;
    the function then reads and compares once more. Two writers that update an
    existing parameter at the same time can still both write: serialize such
    writers outside this library.

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
    - ``(Parameter, None)``: Parameter already matched, nothing was written
    - ``(Parameter, Parameter)``: Parameter differed, a new version was written

    Ref:

    - `put_parameter <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.put_parameter>`_

    :param ssm_client: SSM client
    :param name: parameter name (e.g., "/app/database/host")
    :param value: parameter value to set
    :param description: parameter description
    :param type: parameter type (String, StringList, SecureString)
    :param tier: parameter tier (Standard, Advanced, Intelligent-Tiering)
    :param key_id: KMS key ID for SecureString encryption
    :param allowed_pattern: regex pattern for parameter validation
    :param tags: the full tag set of the parameter, as key-value pairs
    :param policies: parameter policies (JSON string)
    :param data_type: parameter data type (e.g., "text", "aws:ec2:image")

    :returns: Tuple of (before_parameter, after_parameter) where:
        - before_parameter: Parameter object before operation (None if didn't exist)
        - after_parameter: Parameter object after operation (None if no write occurred)
    """
    kwargs = dict(
        ssm_client=ssm_client,
        name=name,
        value=value,
        description=description,
        type=type.value if isinstance(type, ParameterType) else type,
        tier=tier.value if isinstance(tier, ParameterTier) else tier,
        key_id=key_id,
        allowed_pattern=allowed_pattern,
        tags=tags,
        policies=policies,
        data_type=data_type,
    )
    try:
        before_param, after_param = _put_parameter_if_changed(**kwargs)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] != "ParameterAlreadyExists":
            raise  # pragma: no cover
        # Another writer created it between our read and write: compare again
        before_param, after_param = _put_parameter_if_changed(**kwargs)

    if isinstance(tags, dict) and before_param is not None:
        if get_parameter_tags(ssm_client, name) != tags:
            put_parameter_tags(ssm_client, name, tags)

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

    Example::

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

    Example::

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
