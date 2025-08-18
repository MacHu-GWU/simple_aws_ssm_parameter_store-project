# -*- coding: utf-8 -*-

from simple_aws_ssm_parameter_store.model import Parameter
from simple_aws_ssm_parameter_store.constants import (
    ParameterType,
    ParameterTier,
)


class TestParameter:
    def test_properties(self):
        param = Parameter(
            _data={
                "Name": "my_parameter",
                "Type": ParameterType.STRING,
                "Tier": ParameterTier.STANDARD,
            }
        )
        assert param.response == param._data
        assert param.name == "my_parameter"
        _ = param.type
        _ = param.tier
        _ = param.value
        _ = param.version
        _ = param.selector
        _ = param.source_result
        _ = param.last_modified_date
        _ = param.arn
        _ = param.data_type
        _ = param.key_id
        _ = param.last_modified_user
        _ = param.description
        _ = param.allowed_pattern
        _ = param.policies
        assert param.is_string_type is True
        assert param.is_string_list_type is False
        assert param.is_secure_string_type is False
        assert param.is_standard_tier is True
        assert param.is_advanced_tier is False
        assert param.is_intelligent_tiering is False

        _ = param.core_data


if __name__ == "__main__":
    from simple_aws_ssm_parameter_store.tests import run_cov_test

    run_cov_test(
        __file__,
        "simple_aws_ssm_parameter_store.model",
        preview=False,
    )
