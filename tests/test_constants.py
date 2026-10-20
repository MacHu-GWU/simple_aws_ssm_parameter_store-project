# -*- coding: utf-8 -*-

from simple_aws_ssm_parameter_store.constants import ParameterType
from simple_aws_ssm_parameter_store.constants import ParameterTier
from simple_aws_ssm_parameter_store.constants import ResourceType
from simple_aws_ssm_parameter_store.constants import DEFAULT_KMS_KEY


def test_values_match_aws():
    # the enum values are sent to AWS as is
    assert ParameterType.SECURE_STRING.value == "SecureString"
    assert ParameterTier.INTELLIGENT_TIERING.value == "Intelligent-Tiering"
    assert ResourceType.PARAMETER.value == "Parameter"
    assert DEFAULT_KMS_KEY == "alias/aws/ssm"


def test_str_enum():
    # a str enum compares equal to the plain string returned by AWS
    assert ParameterType.STRING == "String"
    assert ParameterTier.STANDARD == "Standard"


if __name__ == "__main__":
    from simple_aws_ssm_parameter_store.tests import run_cov_test

    run_cov_test(
        __file__,
        "simple_aws_ssm_parameter_store.constants",
        preview=False,
    )
