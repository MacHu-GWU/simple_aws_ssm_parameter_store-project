# simple_aws_ssm_parameter_store public API (v0.3.0)

Every name below is imported from `simple_aws_ssm_parameter_store.api`. Every function takes a boto3 SSM client as its first argument; the library never creates one. In tests, a client created inside `moto.mock_aws()` works the same way.

Optional arguments default to a sentinel (`func_args.OPT`): an argument you leave out is not sent to AWS at all, so AWS applies its own default. Do not pass `None` to mean "leave out"; it is sent and rejected by botocore.

---

## get_parameter

```python
get_parameter(
    ssm_client,
    name: str,
    with_decryption: bool = False,
) -> Parameter | None
```

Wraps `GetParameter`. Returns `None` on `ParameterNotFound` or `ParameterVersionNotFound`; any other `ClientError` (permissions, throttling) is raised.

- `name` may carry a version or label: `"/app/key:3"`.
- `with_decryption=True` returns a `SecureString` in plain text (needs `kms:Decrypt`). AWS ignores it for `String` and `StringList`.
- The result has no `tier`, `description`, `key_id`, `allowed_pattern`, or `policies`: `GetParameter` does not return them.

```python
param = get_parameter(ssm_client, "/app/database/password", with_decryption=True)
if param is None:
    ...
param.value, param.version, param.is_secure_string_type
```

---

## put_parameter_if_changed

```python
put_parameter_if_changed(
    ssm_client,
    name: str,
    value: str,
    description: str = OPT,
    type: ParameterType | str = OPT,
    tier: ParameterTier | str = OPT,
    key_id: str = OPT,
    allowed_pattern: str = OPT,
    tags: dict[str, str] = OPT,
    policies: str = OPT,          # JSON array string
    data_type: str = OPT,         # "text", "aws:ec2:image", ...
) -> tuple[Parameter | None, Parameter | None]
```

Treats the arguments as the desired state. Reads the parameter (always decrypted), compares, and calls `PutParameter` only if the parameter is missing or differs. Running the same call again writes nothing, which keeps the 100-version history SSM retains per parameter.

Return value:

| `(before, after)` | Meaning |
| :--- | :--- |
| `(None, Parameter)` | Created (version 1). |
| `(Parameter, None)` | Already matched; nothing written. |
| `(Parameter, Parameter)` | Differed; a new version was written. |

Comparison rules:

- `value` is always compared, against the decrypted current value. So a `SecureString` compares correctly whether `type` is `ParameterType.SECURE_STRING`, `"SecureString"`, or left out.
- Every other argument is compared only if passed. `description`, `tier`, `key_id`, `allowed_pattern`, and `policies` cost one extra `DescribeParameters` call.
- `tier=ParameterTier.INTELLIGENT_TIERING` is never compared (AWS stores Standard or Advanced).
- `policies` is compared as parsed JSON, ignoring key and list order; unparsable counts as changed.
- `key_id` is compared as a string: pass the same form (alias vs ARN) every time.

Tags:

- On create, `tags` are sent with `PutParameter`.
- On an existing parameter (`PutParameter` rejects `Tags` with `Overwrite`), the current tags are read and replaced via `put_parameter_tags` only if they differ, whether or not the value changed. Tags have no versions, so a tag-only change returns `after=None`.
- Passing `tags` removes tags added elsewhere. Leave `tags` out to keep them; pass `{}` to remove all.

Other notes:

- `after` is built from your inputs plus the `PutParameter` response (`Version`, `Tier`); it has no `arn` or `last_modified_date`. Call `get_parameter` for those.
- Concurrency is best effort: a concurrent create (`ParameterAlreadyExists`) triggers one more read-compare-write; two concurrent updates can both write (last write wins). Serialize writers outside the library if that matters.
- Changing an Advanced parameter back to `tier=STANDARD` writes and fails in AWS, as AWS does not allow it.

```python
before, after = put_parameter_if_changed(
    ssm_client=ssm_client,
    name="/app/database/host",
    value="db-1.example.com",
    type=ParameterType.STRING,
    tags={"Team": "platform"},
)
assert before is None and after.version == 1

before, after = put_parameter_if_changed(ssm_client=ssm_client, name="/app/database/host", value="db-1.example.com")
assert after is None                      # unchanged

before, after = put_parameter_if_changed(
    ssm_client=ssm_client, name="/app/database/host", value="db-1.example.com", description="Primary DB",
)
assert after.version == 2                 # metadata change alone writes a version
```

---

## delete_parameter

```python
delete_parameter(ssm_client, name: str) -> bool
```

Wraps `DeleteParameter`. `True` if deleted, `False` on `ParameterNotFound`; other errors are raised. Safe to call repeatedly.

```python
delete_parameter(ssm_client, "/app/temp/config")  # True
delete_parameter(ssm_client, "/app/temp/config")  # False
```

---

## Tag functions

All take the parameter `name` (not the ARN) and work on resource type `Parameter`.

```python
get_parameter_tags(ssm_client, name: str) -> dict[str, str]
update_parameter_tags(ssm_client, name: str, tags: dict[str, str])        # returns the raw AddTagsToResource response
put_parameter_tags(ssm_client, name: str, tags: dict[str, str]) -> None
remove_parameter_tags(ssm_client, name: str, tag_keys: list[str])         # returns the raw RemoveTagsFromResource response
```

| Function | Effect |
| :--- | :--- |
| `get_parameter_tags` | Current tags as a dict; `{}` if none. |
| `update_parameter_tags` | Add the keys, or overwrite their values; other tags kept. |
| `put_parameter_tags` | Make `tags` the full set; `{}` removes all. |
| `remove_parameter_tags` | Remove only these keys; unknown keys are ignored. |

`put_parameter_tags` reads the current tags; if some must go, it removes all of them and then adds the new set (two calls, so the parameter briefly has no tags). If every current key is in the new set, it only adds.

```python
update_parameter_tags(ssm_client, name, {"k1": "v1", "k2": "v2"})
update_parameter_tags(ssm_client, name, {"k2": "v22", "k3": "v3"})
get_parameter_tags(ssm_client, name)      # {"k1": "v1", "k2": "v22", "k3": "v3"}
remove_parameter_tags(ssm_client, name, ["k1", "k4"])
get_parameter_tags(ssm_client, name)      # {"k2": "v22", "k3": "v3"}
put_parameter_tags(ssm_client, name, {"k3": "v33"})
get_parameter_tags(ssm_client, name)      # {"k3": "v33"}
put_parameter_tags(ssm_client, name, {})
get_parameter_tags(ssm_client, name)      # {}
```

---

## encode_tags / decode_tags

```python
encode_tags(tags: dict[str, str]) -> list[dict[str, str]]
decode_tags(tag_list: list[dict[str, str]]) -> dict[str, str]
```

```python
encode_tags({"k1": "v1"})                          # [{"Key": "k1", "Value": "v1"}]
decode_tags([{"Key": "k1", "Value": "v1"}])        # {"k1": "v1"}
```

---

## Parameter

```python
@dataclasses.dataclass(frozen=True)
class Parameter:
    _data: dict[str, Any]   # the raw API dict
```

Wraps one parameter dict from `GetParameter`, `GetParameters`, `GetParametersByPath`, `DescribeParameters`, or (partially) `PutParameter`. Build one from any boto3 item: `Parameter(_data=item)`. Every property reads `_data`; a field the source API did not return is `None`.

| Property | Type | Source key / note |
| :--- | :--- | :--- |
| `name` | `str` | `Name` (required) |
| `value` | `str \| None` | `Value`; encrypted if read without decryption |
| `type` | `str \| None` | `Type` |
| `version` | `int \| None` | `Version` |
| `arn` | `str \| None` | `ARN` |
| `data_type` | `str \| None` | `DataType` |
| `last_modified_date` | `datetime \| None` | `LastModifiedDate` |
| `selector` | `str \| None` | `Selector`, such as `:3` |
| `source_result` | `str \| None` | `SourceResult` |
| `tier` | `str \| None` | `Tier`; describe_parameters / put_parameter only |
| `key_id` | `str \| None` | `KeyId`; describe_parameters only |
| `description` | `str \| None` | `Description`; describe_parameters only |
| `allowed_pattern` | `str \| None` | `AllowedPattern`; describe_parameters only |
| `policies` | `list[dict] \| None` | `Policies`; describe_parameters only |
| `last_modified_user` | `str \| None` | `LastModifiedUser`; describe_parameters only |
| `aws_account_id` | `str` | parsed from `arn`; fails if `arn` is `None` |
| `aws_region` | `str` | parsed from `arn`; fails if `arn` is `None` |
| `is_string_type` / `is_string_list_type` / `is_secure_string_type` | `bool` | by `type` |
| `is_standard_tier` / `is_advanced_tier` / `is_intelligent_tiering` | `bool` | by `tier` |
| `response` | `dict` | the raw `_data` |
| `core_data` | `dict` | `name`, `type`, `tier`, `version`, `last_modified_date`, `arn` |

Inherited from `func_args.BaseFrozenModel`: `to_dict()`, `to_kwargs()`.

```python
param = Parameter(_data={
    "Name": "my_parameter",
    "Type": "String",
    "ARN": "arn:aws:ssm:us-east-1:123456789012:parameter/my_parameter",
})
param.aws_account_id    # "123456789012"
param.is_string_type    # True
```

---

## Constants

`str` enums: members compare equal to AWS's plain strings (`ParameterType.STRING == "String"`); use `.value` to get the string.

```python
class ParameterType(str, Enum):
    STRING = "String"
    STRING_LIST = "StringList"
    SECURE_STRING = "SecureString"

class ParameterTier(str, Enum):
    STANDARD = "Standard"
    ADVANCED = "Advanced"
    INTELLIGENT_TIERING = "Intelligent-Tiering"

class ResourceType(str, Enum):  # ResourceType values of the SSM tagging APIs
    DOCUMENT = "Document"
    MANAGED_INSTANCE = "ManagedInstance"
    MAINTENANCE_WINDOW = "MaintenanceWindow"
    PARAMETER = "Parameter"
    PATCH_BASELINE = "PatchBaseline"
    OPS_ITEM = "OpsItem"
    OPS_METADATA = "OpsMetadata"
    AUTOMATION = "Automation"
    ASSOCIATION = "Association"

DEFAULT_KMS_KEY = "alias/aws/ssm"   # the AWS-managed key SecureString uses by default
```
