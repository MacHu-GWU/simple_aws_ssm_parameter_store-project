# -*- coding: utf-8 -*-

from simple_aws_ssm_parameter_store import api


def test():
    _ = api
    _ = api.ParameterType
    _ = api.ParameterTier
    _ = api.ResourceType
    _ = api.DEFAULT_KMS_KEY
    _ = api.encode_tags
    _ = api.decode_tags
    _ = api.Parameter
    _ = api.get_parameter
    _ = api.delete_parameter
    _ = api.get_parameter_tags
    _ = api.remove_parameter_tags
    _ = api.update_parameter_tags
    _ = api.put_parameter_tags


if __name__ == "__main__":
    from simple_aws_ssm_parameter_store.tests import run_cov_test

    run_cov_test(
        __file__,
        "simple_aws_ssm_parameter_store.api",
        preview=False,
    )
