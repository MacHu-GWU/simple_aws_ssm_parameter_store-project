# -*- coding: utf-8 -*-

from simple_aws_ssm_parameter_store.client import (
    get_parameter,
    put_parameter_if_changed,
    delete_parameter,
    get_parameter_tags,
    remove_parameter_tags,
    update_parameter_tags,
    put_parameter_tags,
)
from simple_aws_ssm_parameter_store.constants import ParameterType, ParameterTier

from simple_aws_ssm_parameter_store.tests.mock_aws import BaseMockAwsTest


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
            overwrite=True,
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


if __name__ == "__main__":
    from simple_aws_ssm_parameter_store.tests import run_cov_test

    run_cov_test(
        __file__,
        "simple_aws_ssm_parameter_store.client",
        preview=False,
    )
