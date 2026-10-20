.. _release_history:

Release and Version History
==============================================================================


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.3.0 (2026-10-20)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Breaking Changes**

- Drop Python 3.10 (end of life). Python 3.11 to 3.14 are supported.
- ``put_parameter_if_changed()`` now treats ``tags`` as the full tag set on every call, not only on create: when the parameter already exists and its tags differ, they are replaced. Tags added elsewhere are removed if you pass ``tags``. Leave ``tags`` out to keep the tags as they are.
- ``put_parameter_if_changed()`` now compares every argument you pass, not only ``value``. A changed ``description``, ``type``, ``tier``, ``key_id``, ``allowed_pattern``, ``policies``, or ``data_type`` writes a new version even when the value is the same.
- Remove ``simple_aws_ssm_parameter_store.__version__`` and the other ``__author__``-style attributes. Read the version with ``importlib.metadata.version("simple_aws_ssm_parameter_store")``.

**Minor Improvements**

- ``put_parameter_if_changed()`` handles a concurrent create: if another writer creates the parameter between the read and the write, it reads and compares once more instead of raising ``ParameterAlreadyExists``.
- Add docstrings to every ``Parameter`` property, so they appear in the API reference.

**Bugfixes**

- Fix ``put_parameter_if_changed()`` writing a new ``SecureString`` version on every call when ``type`` was left out or passed as the string ``"SecureString"``. The current value is now always read decrypted before the comparison, which needs ``kms:Decrypt`` on the parameter's KMS key.

**Miscellaneous**

- Move the project to the pywf open-source template: uv and mise instead of poetry, setuptools as the build backend, updated GitHub Actions and Read the Docs builds.
- Rewrite the README, and add the "Getting Started" (a notebook run against moto) and "Design Notes" docs pages.


0.2.3 (2025-08-21)
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
