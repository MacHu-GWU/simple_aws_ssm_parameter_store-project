# -*- coding: utf-8 -*-

import typing as T
import dataclasses

import moto
import boto3

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_ssm.client import SSMClient


@dataclasses.dataclass(frozen=True)
class MockAwsTestConfig:
    use_mock: bool = dataclasses.field()
    aws_region: str = dataclasses.field()
    aws_profile: T.Optional[str] = dataclasses.field(default=None)


class BaseMockAwsTest:
    use_mock: bool
    boto_ses: "boto3.Session"
    ssm_client: "SSMClient"

    @classmethod
    def setup_mock(cls, mock_aws_test_config: MockAwsTestConfig):
        cls.mock_aws_test_config = mock_aws_test_config
        if mock_aws_test_config.use_mock:
            cls.mock_aws = moto.mock_aws()
            cls.mock_aws.start()

        if mock_aws_test_config.use_mock:
            cls.boto_ses: "boto3.Session" = boto3.Session(
                region_name=mock_aws_test_config.aws_region
            )
        else:
            cls.boto_ses: "boto3.Session" = boto3.Session(
                profile_name=mock_aws_test_config.aws_profile,
                region_name=mock_aws_test_config.aws_region,
            )
        cls.ssm_client: "SSMClient" = cls.boto_ses.client("ssm")

    @classmethod
    def setup_class_post_hook(cls):
        pass

    @classmethod
    def setup_class(cls):
        mock_aws_test_config = MockAwsTestConfig(
            use_mock=cls.use_mock,
            aws_region="us-east-1",
            aws_profile="bmt_app_dev_us_east_1",  # Use default profile
        )
        cls.setup_mock(mock_aws_test_config)
        cls.setup_class_post_hook()

    @classmethod
    def teardown_class(cls):
        if cls.mock_aws_test_config.use_mock:
            cls.mock_aws.stop()
