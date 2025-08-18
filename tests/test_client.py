# -*- coding: utf-8 -*-

from simple_aws_ssm_parameter_store.client import (
    get_parameter,
    delete_parameter,
    get_parameter_tags,
    remove_parameter_tags,
    update_parameter_tags,
    put_parameter_tags,
)
from simple_aws_ssm_parameter_store.constants import ParameterType

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


if __name__ == "__main__":
    from simple_aws_ssm_parameter_store.tests import run_cov_test

    run_cov_test(
        __file__,
        "simple_aws_ssm_parameter_store.client",
        preview=False,
    )
