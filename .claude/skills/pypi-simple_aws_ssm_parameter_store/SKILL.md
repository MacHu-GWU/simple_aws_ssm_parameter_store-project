---
name: pypi-simple_aws_ssm_parameter_store
description: "Python library simple_aws_ssm_parameter_store (v0.3.0): Pythonic helpers over the boto3 SSM client for AWS Systems Manager Parameter Store. get_parameter returns None when missing, put_parameter_if_changed writes only when the desired state differs, delete_parameter is idempotent, and get/update/put/remove_parameter_tags manage tags as a dict. Public API: get_parameter, put_parameter_if_changed, delete_parameter, get_parameter_tags, update_parameter_tags, put_parameter_tags, remove_parameter_tags, Parameter, ParameterType, ParameterTier."
---

# simple_aws_ssm_parameter_store (v0.3.0)

Plain functions over your own boto3 SSM client (`boto3.client("ssm")`). They turn "not found" into return values, skip writes that would only burn one of the 100 versions SSM keeps per parameter, and take tags as `dict[str, str]`. Python 3.11+. No client class, no config, no cache.

## Import

```python
from simple_aws_ssm_parameter_store.api import get_parameter
import simple_aws_ssm_parameter_store.api as simple_aws_ssm_parameter_store  # then simple_aws_ssm_parameter_store.get_parameter
```

## Public API

Functions (`ssm_client` is a boto3 SSM client; optional args default to "not sent"):

- `get_parameter(ssm_client, name: str, with_decryption: bool = False) -> Parameter | None`: `None` if the parameter (or `name:version`) does not exist.
- `put_parameter_if_changed(ssm_client, name: str, value: str, description=..., type: ParameterType=..., tier: ParameterTier=..., key_id=..., allowed_pattern=..., tags: dict[str, str]=..., policies: str=..., data_type=...) -> tuple[Parameter | None, Parameter | None]`: make the parameter match the arguments you pass; write only if it is missing or differs. Returns `(before, after)`.
- `delete_parameter(ssm_client, name: str) -> bool`: `True` if deleted, `False` if it did not exist.
- `get_parameter_tags(ssm_client, name: str) -> dict[str, str]`: `{}` when there are no tags.
- `update_parameter_tags(ssm_client, name: str, tags: dict[str, str])`: add or overwrite these keys, keep others.
- `put_parameter_tags(ssm_client, name: str, tags: dict[str, str]) -> None`: make `tags` the full tag set; `{}` removes all.
- `remove_parameter_tags(ssm_client, name: str, tag_keys: list[str])`: remove only these keys.
- `encode_tags(tags: dict[str, str]) -> list[dict]` / `decode_tags(tag_list: list[dict]) -> dict[str, str]`: convert to and from boto3's `[{"Key": ..., "Value": ...}]`.

`Parameter` (frozen dataclass, one field `_data`: the raw API dict; build with `Parameter(_data=item)`). Properties, `None` when absent from the response:

- `name: str`, `value: str | None`, `type: str | None`, `version: int | None`, `arn: str | None`, `data_type: str | None`, `last_modified_date: datetime | None`, `selector`, `source_result`
- only filled from `describe_parameters` items: `tier`, `key_id`, `description`, `allowed_pattern`, `policies`, `last_modified_user`
- `aws_account_id: str`, `aws_region: str` (parsed from `arn`)
- `is_string_type`, `is_string_list_type`, `is_secure_string_type`, `is_standard_tier`, `is_advanced_tier`, `is_intelligent_tiering: bool`
- `response: dict` (the raw dict), `core_data: dict` (name, type, tier, version, last_modified_date, arn)

Constants (`str` enums, so they compare equal to the plain strings AWS returns):

- `ParameterType`: `STRING`, `STRING_LIST`, `SECURE_STRING`
- `ParameterTier`: `STANDARD`, `ADVANCED`, `INTELLIGENT_TIERING`
- `ResourceType`: `PARAMETER`, `DOCUMENT`, ... (values for `list_tags_for_resource`)
- `DEFAULT_KMS_KEY = "alias/aws/ssm"`

## Typical use

```python
import boto3
from simple_aws_ssm_parameter_store.api import ParameterType
from simple_aws_ssm_parameter_store.api import get_parameter
from simple_aws_ssm_parameter_store.api import put_parameter_if_changed

ssm_client = boto3.client("ssm")
before, after = put_parameter_if_changed(
    ssm_client=ssm_client,
    name="/app/database/host",
    value="db-1.example.com",
    type=ParameterType.STRING,
    tags={"Team": "platform"},
)
# (None, P) created; (P, None) already matched, nothing written; (P, P) new version written
param = get_parameter(ssm_client, "/app/database/host")
if param is not None:
    print(param.value, param.version)
```

## put_parameter_if_changed gotchas

- Compares `value` always, plus only the other arguments you pass; a left-out argument keeps the current setting.
- Always reads with decryption, so a `SecureString` compares correctly even without `type`; needs `kms:Decrypt`.
- `tags`, when passed, become the full tag set on every call (replaced via `put_parameter_tags` if they differ). Tag-only changes return `after=None`. Leave `tags` out to keep tags.
- `after` holds only your inputs plus `Version`/`Tier`; call `get_parameter` for `arn` etc.
- Best effort, not atomic: concurrent updates can both write. A concurrent create is retried once.

## More detail

For full API docs see `ref/public-api.md`.
