# -*- coding: utf-8 -*-

import typing as T

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_ssm.type_defs import TagTypeDef


def encode_tags(tags: dict[str, str]) -> list["TagTypeDef"]:
    """
    Example:
        >>> encode_tags({"name": "Alice"})
        [
            {'Key': 'name', 'Value': 'Alice'}
        ]
    """
    # note: static check would fail if use list comprehension here
    results: list["TagTypeDef"] = []
    for key, value in tags.items():
        results.append({"Key": key, "Value": value})
    return results


def decode_tags(tag_list: list["TagTypeDef"]) -> dict[str, str]:
    """
    Example:
        >>> decode_tags([{'Key': 'name', 'Value': 'Alice'}])
        {'name': 'Alice'}
    """
    return {dct["Key"]: dct["Value"] for dct in tag_list}
