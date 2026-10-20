# -*- coding: utf-8 -*-

from simple_aws_ssm_parameter_store.client import get_parameter
from simple_aws_ssm_parameter_store.client import put_parameter_if_changed
from simple_aws_ssm_parameter_store.client import delete_parameter
from simple_aws_ssm_parameter_store.client import get_parameter_tags
from simple_aws_ssm_parameter_store.client import remove_parameter_tags
from simple_aws_ssm_parameter_store.client import update_parameter_tags
from simple_aws_ssm_parameter_store.client import put_parameter_tags
from simple_aws_ssm_parameter_store.client import _get_parameter_metadata
from simple_aws_ssm_parameter_store.client import _is_same_policies
from simple_aws_ssm_parameter_store.client import _is_parameter_changed
from simple_aws_ssm_parameter_store.constants import ParameterType
from simple_aws_ssm_parameter_store.constants import ParameterTier
from simple_aws_ssm_parameter_store.model import Parameter

import json

from simple_aws_ssm_parameter_store.tests.mock_aws import BaseMockAwsTest


class RaceSsmClient:
    """
    Wrap an SSM client and create the parameter right before the first create
    call, as a concurrent writer would between our read and our write.
    """

    def __init__(self, ssm_client, race_value: str):
        self._ssm_client = ssm_client
        self._race_value = race_value
        self._raced = False

    def __getattr__(self, name):
        return getattr(self._ssm_client, name)

    def put_parameter(self, **kwargs):
        if self._raced is False and "Overwrite" not in kwargs:
            self._raced = True
            self._ssm_client.put_parameter(
                Name=kwargs["Name"],
                Value=self._race_value,
                Type=ParameterType.STRING.value,
            )
        return self._ssm_client.put_parameter(**kwargs)


def test_is_same_policies():
    policy = {
        "Type": "Expiration",
        "Version": "1.0",
        "Attributes": {"Timestamp": "2030-01-01T00:00:00.000Z"},
    }
    current = [{"PolicyText": json.dumps(policy), "PolicyStatus": "Pending"}]
    # same policy, different key order
    desired = json.dumps(dict(reversed(list(policy.items()))))
    assert _is_same_policies(f"[{desired}]", current) is True
    # a single policy object instead of an array
    assert _is_same_policies(desired, current) is True
    assert _is_same_policies("[]", current) is False
    assert _is_same_policies("[]", None) is True
    # anything that cannot be parsed counts as different
    assert _is_same_policies("not json", current) is False
    assert _is_same_policies("[]", [{"PolicyText": "{'Type': 1}"}]) is False


class Test(BaseMockAwsTest):
    use_mock = True

    def test_get_and_delete_parameter(self):
        name = "test_get_and_manage_parameter"

        # Parameter doesn't exist yet
        param = get_parameter(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert param is None

        # Create a parameter
        self.ssm_client.put_parameter(
            Name=name,
            Value="v1",
            Type=ParameterType.STRING.value,
        )

        # Parameter exists now
        param = get_parameter(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert param.value == "v1"
        version = param.version

        # We can also get the same parameter by version
        param = get_parameter(
            ssm_client=self.ssm_client,
            name=f"{name}:{version}",
        )
        assert param.value == "v1"
        assert param.version == version

        # But this parameter version doesn't exists
        param = get_parameter(
            ssm_client=self.ssm_client,
            name=f"{name}:999999",
        )
        assert param is None

        # Delete the parameter
        flag = delete_parameter(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert flag is True

        # Parameter doesn't exist now
        param = get_parameter(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert param is None

        # No deletion happened this time
        flag = delete_parameter(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert flag is False

    def test_manage_tags(self):
        name = "test_manage_tags"
        self.ssm_client.put_parameter(
            Name=name,
            Value="v1",
            Type=ParameterType.STRING.value,
        )

        # Get tags, should be empty
        tags = get_parameter_tags(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert tags == {}

        # Full replace tags
        put_parameter_tags(
            ssm_client=self.ssm_client,
            name=name,
            tags=dict(k1="v1", k2="v2"),
        )
        tags = get_parameter_tags(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert tags == {"k1": "v1", "k2": "v2"}

        # Update tags, should add k3 and update k2
        update_parameter_tags(
            ssm_client=self.ssm_client,
            name=name,
            tags=dict(k2="v22", k3="v3"),
        )
        tags = get_parameter_tags(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert tags == {"k1": "v1", "k2": "v22", "k3": "v3"}

        # Remove some tags
        remove_parameter_tags(
            ssm_client=self.ssm_client,
            name=name,
            tag_keys=["k1", "k4"],
        )
        tags = get_parameter_tags(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert tags == {"k2": "v22", "k3": "v3"}

        # Full replace tags again
        put_parameter_tags(
            ssm_client=self.ssm_client,
            name=name,
            tags=dict(k3="v33"),
        )
        tags = get_parameter_tags(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert tags == {"k3": "v33"}

        # Remove all tags using put_parameter_tags
        put_parameter_tags(
            ssm_client=self.ssm_client,
            name=name,
            tags={},
        )
        tags = get_parameter_tags(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert tags == {}

    def test_put_parameter_if_changed(self):
        name = "test_put_parameter_if_changed"

        # Test 1: Parameter doesn't exist - should create it
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v1",
            type=ParameterType.STRING,
            tier=ParameterTier.INTELLIGENT_TIERING,
        )
        assert before_param is None  # Parameter didn't exist before
        assert after_param is not None  # Parameter was created
        assert after_param.name == name
        assert after_param.value == "v1"

        # Verify parameter was actually created
        param = get_parameter(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert param.value == "v1"

        # Test 2: Parameter exists with same value - should not update
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v1",  # Same value
            type=ParameterType.STRING,
        )
        assert before_param is not None  # Parameter existed before
        assert before_param.value == "v1"
        assert after_param is None  # No update occurred

        # Test 3: Parameter exists with different value - should update
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v2",  # Different value
            type=ParameterType.STRING,
        )
        assert before_param is not None  # Parameter existed before
        assert before_param.value == "v1"
        assert after_param is not None  # Update occurred
        assert after_param.name == name
        assert after_param.value == "v2"

        # Verify parameter was actually updated
        param = get_parameter(
            ssm_client=self.ssm_client,
            name=name,
        )
        assert param.value == "v2"

        # Test 4: SecureString parameter with decryption
        secure_name = "test_secure_param"
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=secure_name,
            value="secret123",
            type=ParameterType.SECURE_STRING,
        )
        assert before_param is None  # Parameter didn't exist before
        assert after_param is not None  # Parameter was created

        # Test with same SecureString value - should not update
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=secure_name,
            value="secret123",  # Same value
            type=ParameterType.SECURE_STRING,
        )
        assert before_param is not None  # Parameter existed before
        assert after_param is None  # No update occurred

        # Cleanup
        delete_parameter(self.ssm_client, name)
        delete_parameter(self.ssm_client, secure_name)

    def test_put_parameter_if_changed_secure_string_without_type(self):
        name = "test_put_parameter_if_changed_secure_string_without_type"
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="secret123",
            type=ParameterType.SECURE_STRING,
        )
        assert after_param.version == 1

        # type left out: still compared by the decrypted value
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="secret123",
        )
        assert before_param.value == "secret123"
        assert after_param is None

        # type as a plain string: same
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="secret123",
            type="SecureString",
        )
        assert after_param is None

        # a new value without type keeps the parameter a SecureString
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="secret456",
        )
        assert after_param.version == 2
        assert after_param.is_secure_string_type is True

        delete_parameter(self.ssm_client, name)

    def test_put_parameter_if_changed_metadata(self):
        name = "test_put_parameter_if_changed_metadata"
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v1",
            description="d1",
            type=ParameterType.STRING,
            data_type="text",
        )
        assert after_param.version == 1

        # same value and same metadata: nothing written
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v1",
            description="d1",
            type=ParameterType.STRING,
            tier=ParameterTier.STANDARD,
            allowed_pattern="",
            data_type="text",
        )
        assert after_param is None

        # Intelligent-Tiering is never compared
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v1",
            tier=ParameterTier.INTELLIGENT_TIERING,
        )
        assert after_param is None

        # each changed field writes a new version, even with the same value
        changes = [
            dict(description="d2"),
            dict(tier=ParameterTier.ADVANCED),
            dict(allowed_pattern="^v.*$"),
            dict(type=ParameterType.STRING_LIST),
        ]
        version = 1
        for change in changes:
            before_param, after_param = put_parameter_if_changed(
                ssm_client=self.ssm_client,
                name=name,
                value="v1",
                **change,
            )
            version += 1
            assert after_param.version == version
            # the same call again writes nothing
            before_param, after_param = put_parameter_if_changed(
                ssm_client=self.ssm_client,
                name=name,
                value="v1",
                **change,
            )
            assert after_param is None

        # moto returns PolicyText that is not JSON, so policies always count as changed
        policies = json.dumps(
            [
                {
                    "Type": "Expiration",
                    "Version": "1.0",
                    "Attributes": {"Timestamp": "2030-01-01T00:00:00.000Z"},
                }
            ]
        )
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v1",
            policies=policies,
        )
        assert after_param is not None

        delete_parameter(self.ssm_client, name)

        secure_name = "test_put_parameter_if_changed_metadata_secure"
        put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=secure_name,
            value="secret",
            type=ParameterType.SECURE_STRING,
        )
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=secure_name,
            value="secret",
            key_id="alias/aws/ssm",
        )
        assert after_param is None
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=secure_name,
            value="secret",
            key_id="alias/my-key",
        )
        assert after_param.version == 2

        delete_parameter(self.ssm_client, secure_name)

    def test_is_parameter_changed_data_type(self):
        # moto rejects data types other than text, so compare without a write
        param = Parameter(
            _data={
                "Name": "test_is_parameter_changed_data_type",
                "Type": ParameterType.STRING.value,
                "Value": "v1",
                "DataType": "text",
            }
        )
        kwargs = dict(ssm_client=self.ssm_client, before_param=param, value="v1")
        assert _is_parameter_changed(data_type="text", **kwargs) is False
        assert _is_parameter_changed(data_type="aws:ec2:image", **kwargs) is True

    def test_get_parameter_metadata(self):
        assert _get_parameter_metadata(self.ssm_client, "/not/exists") == {}

    def test_put_parameter_if_changed_tags(self):
        name = "test_put_parameter_if_changed_tags"
        put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v1",
            type=ParameterType.STRING,
            tags={"k1": "v1"},
        )
        assert get_parameter_tags(self.ssm_client, name) == {"k1": "v1"}

        # tags left out: kept as they are
        put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v2",
        )
        assert get_parameter_tags(self.ssm_client, name) == {"k1": "v1"}

        # same value, new tags: tags replaced, no new version
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v2",
            tags={"k2": "v2"},
        )
        assert after_param is None
        assert get_parameter_tags(self.ssm_client, name) == {"k2": "v2"}

        # new value, same tags
        before_param, after_param = put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v3",
            tags={"k2": "v2"},
        )
        assert after_param.version == 3
        assert get_parameter_tags(self.ssm_client, name) == {"k2": "v2"}

        # empty dict removes every tag
        put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=name,
            value="v3",
            tags={},
        )
        assert get_parameter_tags(self.ssm_client, name) == {}

        delete_parameter(self.ssm_client, name)

        # empty tags on create
        empty_name = "test_put_parameter_if_changed_tags_empty"
        put_parameter_if_changed(
            ssm_client=self.ssm_client,
            name=empty_name,
            value="v1",
            type=ParameterType.STRING,
            tags={},
        )
        assert get_parameter_tags(self.ssm_client, empty_name) == {}
        delete_parameter(self.ssm_client, empty_name)

    def test_put_parameter_if_changed_create_race(self):
        # another writer creates a different value: we compare again and overwrite
        name = "test_put_parameter_if_changed_create_race_1"
        before_param, after_param = put_parameter_if_changed(
            ssm_client=RaceSsmClient(self.ssm_client, race_value="theirs"),
            name=name,
            value="mine",
            type=ParameterType.STRING,
            tags={"k1": "v1"},
        )
        assert before_param.value == "theirs"
        assert after_param.version == 2
        assert get_parameter(self.ssm_client, name).value == "mine"
        assert get_parameter_tags(self.ssm_client, name) == {"k1": "v1"}
        delete_parameter(self.ssm_client, name)

        # another writer creates the same value: nothing more to write
        name = "test_put_parameter_if_changed_create_race_2"
        before_param, after_param = put_parameter_if_changed(
            ssm_client=RaceSsmClient(self.ssm_client, race_value="same"),
            name=name,
            value="same",
            type=ParameterType.STRING,
        )
        assert before_param.version == 1
        assert after_param is None
        delete_parameter(self.ssm_client, name)


if __name__ == "__main__":
    from simple_aws_ssm_parameter_store.tests import run_cov_test

    run_cov_test(
        __file__,
        "simple_aws_ssm_parameter_store.client",
        preview=False,
    )
