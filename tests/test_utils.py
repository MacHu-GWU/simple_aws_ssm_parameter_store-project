# -*- coding: utf-8 -*-

from simple_aws_ssm_parameter_store.utils import encode_tags, decode_tags


def test_encode_tags():
    tags = {"k1": "v1", "k2": "v2"}
    result = encode_tags(tags)
    assert result == [{"Key": "k1", "Value": "v1"}, {"Key": "k2", "Value": "v2"}]


def test_decode_tags():
    tags = [{"Key": "k1", "Value": "v1"}, {"Key": "k2", "Value": "v2"}]
    result = decode_tags(tags)
    assert result == {"k1": "v1", "k2": "v2"}


if __name__ == "__main__":
    from simple_aws_ssm_parameter_store.tests import run_cov_test

    run_cov_test(
        __file__,
        "simple_aws_ssm_parameter_store.utils",
        preview=False,
    )
