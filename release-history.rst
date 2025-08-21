.. _release_history:

Release and Version History
==============================================================================


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.2.3 (2025-08-18)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Bugfixes**

- Remove the ``overwrite`` parameter from the ``put_parameter_if_changed`` function because this function is designed to overwrite parameter. Also fix a bug that remove the tags argument when it is an update operation.


0.2.2 (2025-08-18)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Minor Improvements**

- Simplified Parameter object construction logic in ``put_parameter_if_changed`` function using ``remove_optional()`` and ``dict.update()`` for cleaner code


0.2.1 (2025-08-18)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Add the following public APIs:
    - ``simple_aws_ssm_parameter_store.api.put_parameter_if_changed``


0.1.1 (2025-08-18)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- First release
- Add the following public APIs:
    - ``simple_aws_ssm_parameter_store.api.ParameterType``
    - ``simple_aws_ssm_parameter_store.api.ParameterTier``
    - ``simple_aws_ssm_parameter_store.api.ResourceType``
    - ``simple_aws_ssm_parameter_store.api.DEFAULT_KMS_KEY``
    - ``simple_aws_ssm_parameter_store.api.encode_tags``
    - ``simple_aws_ssm_parameter_store.api.decode_tags``
    - ``simple_aws_ssm_parameter_store.api.Parameter``
    - ``simple_aws_ssm_parameter_store.api.get_parameter``
    - ``simple_aws_ssm_parameter_store.api.delete_parameter``
    - ``simple_aws_ssm_parameter_store.api.get_parameter_tags``
    - ``simple_aws_ssm_parameter_store.api.remove_parameter_tags``
    - ``simple_aws_ssm_parameter_store.api.update_parameter_tags``
    - ``simple_aws_ssm_parameter_store.api.put_parameter_tags``
