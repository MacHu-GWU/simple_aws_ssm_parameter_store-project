
.. image:: https://readthedocs.org/projects/simple-aws-ssm-parameter-store/badge/?version=latest
    :target: https://simple-aws-ssm-parameter-store.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://github.com/MacHu-GWU/simple_aws_ssm_parameter_store-project/actions/workflows/main.yml/badge.svg
    :target: https://github.com/MacHu-GWU/simple_aws_ssm_parameter_store-project/actions?query=workflow:CI

.. image:: https://codecov.io/gh/MacHu-GWU/simple_aws_ssm_parameter_store-project/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/MacHu-GWU/simple_aws_ssm_parameter_store-project

.. image:: https://img.shields.io/pypi/v/simple-aws-ssm-parameter-store.svg
    :target: https://pypi.python.org/pypi/simple-aws-ssm-parameter-store

.. image:: https://img.shields.io/pypi/l/simple-aws-ssm-parameter-store.svg
    :target: https://pypi.python.org/pypi/simple-aws-ssm-parameter-store

.. image:: https://img.shields.io/pypi/pyversions/simple-aws-ssm-parameter-store.svg
    :target: https://pypi.python.org/pypi/simple-aws-ssm-parameter-store

.. image:: https://img.shields.io/badge/✍️_Release_History!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/simple_aws_ssm_parameter_store-project/blob/main/release-history.rst

.. image:: https://img.shields.io/badge/⭐_Star_me_on_GitHub!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/simple_aws_ssm_parameter_store-project

------

.. image:: https://img.shields.io/badge/Link-API-blue.svg
    :target: https://simple-aws-ssm-parameter-store.readthedocs.io/en/latest/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Install-blue.svg
    :target: `install`_

.. image:: https://img.shields.io/badge/Link-GitHub-blue.svg
    :target: https://github.com/MacHu-GWU/simple_aws_ssm_parameter_store-project

.. image:: https://img.shields.io/badge/Link-Submit_Issue-blue.svg
    :target: https://github.com/MacHu-GWU/simple_aws_ssm_parameter_store-project/issues

.. image:: https://img.shields.io/badge/Link-Request_Feature-blue.svg
    :target: https://github.com/MacHu-GWU/simple_aws_ssm_parameter_store-project/issues

.. image:: https://img.shields.io/badge/Link-Download-blue.svg
    :target: https://pypi.org/pypi/simple-aws-ssm-parameter-store#files


Welcome to ``simple_aws_ssm_parameter_store`` Documentation
==============================================================================
.. image:: https://simple-aws-ssm-parameter-store.readthedocs.io/en/latest/_static/simple_aws_ssm_parameter_store-logo.png
    :target: https://simple-aws-ssm-parameter-store.readthedocs.io/en/latest/

``simple_aws_ssm_parameter_store`` is a small, Pythonic layer over the boto3 SSM client for `AWS Systems Manager Parameter Store <https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html>`_. It does not replace boto3: every function takes your own ``ssm_client`` and smooths over the parts of the raw API that are awkward to use.

What it gives you over the raw client:

- **Existence check without exceptions:** ``get_parameter`` returns ``None`` instead of raising ``ParameterNotFound``.
- **Idempotent delete:** ``delete_parameter`` returns ``True`` or ``False`` and is safe to call twice.
- **Writes only on change:** ``put_parameter_if_changed`` skips the write when the value is the same, so re-running a script does not use up the 100 versions SSM keeps per parameter.
- **Tags as a dict:** get, add, replace, or remove tags with plain ``dict[str, str]`` instead of ``[{"Key": ..., "Value": ...}]`` lists.
- **A typed result:** a ``Parameter`` object with properties such as ``value``, ``version``, ``arn``, and ``aws_account_id``.


Quick Tour
------------------------------------------------------------------------------
Every public name is imported from ``simple_aws_ssm_parameter_store.api``:

.. code-block:: python

    import boto3
    from simple_aws_ssm_parameter_store.api import ParameterType
    from simple_aws_ssm_parameter_store.api import get_parameter
    from simple_aws_ssm_parameter_store.api import put_parameter_if_changed
    from simple_aws_ssm_parameter_store.api import delete_parameter

    ssm_client = boto3.client("ssm")

**Read a parameter, or learn that it does not exist**

.. code-block:: python

    param = get_parameter(ssm_client, "/app/database/password", with_decryption=True)
    if param is None:
        print("not found")
    else:
        print(param.value, param.version, param.is_secure_string_type)

**Write only when the value changed**

.. code-block:: python

    before, after = put_parameter_if_changed(
        ssm_client=ssm_client,
        name="/app/database/host",
        value="prod-db.example.com",
        type=ParameterType.STRING,
        tags={"Team": "platform"},  # applied only when the parameter is created
    )

The result tells you what happened:

==========================  =========================================
``(before, after)``         Meaning
==========================  =========================================
``(None, Parameter)``       Created, ``after.version == 1``
``(Parameter, None)``       Value unchanged, nothing written
``(Parameter, Parameter)``  Updated from ``before.version`` to ``after.version``
==========================  =========================================

For a ``SecureString``, pass ``type=ParameterType.SECURE_STRING``: the current value is then read decrypted, so the comparison is correct.

**Delete, whether or not it exists**

.. code-block:: python

    delete_parameter(ssm_client, "/app/temp/config")  # True: it was deleted
    delete_parameter(ssm_client, "/app/temp/config")  # False: it was already gone

**Manage tags as a dict**

.. code-block:: python

    from simple_aws_ssm_parameter_store.api import get_parameter_tags
    from simple_aws_ssm_parameter_store.api import update_parameter_tags
    from simple_aws_ssm_parameter_store.api import put_parameter_tags
    from simple_aws_ssm_parameter_store.api import remove_parameter_tags

    name = "/app/config"

    update_parameter_tags(ssm_client, name, {"Env": "prod", "Team": "platform"})
    # tags are now {"Env": "prod", "Team": "platform"}

    put_parameter_tags(ssm_client, name, {"Env": "prod", "Owner": "alice"})
    # tags are now {"Env": "prod", "Owner": "alice"}

    remove_parameter_tags(ssm_client, name, ["Owner"])
    # tags are now {"Env": "prod"}

    put_parameter_tags(ssm_client, name, {})
    # tags are now {}

    get_parameter_tags(ssm_client, name)  # read them back as a dict

- ``update_parameter_tags`` adds or overwrites the given keys and keeps the others.
- ``put_parameter_tags`` makes the given dict the full tag set; ``{}`` removes every tag.
- ``remove_parameter_tags`` removes only the given keys.

Learn more:

- `Getting Started <https://simple-aws-ssm-parameter-store.readthedocs.io/en/latest/01-Getting-Started/index.html>`_: every function, run step by step with real output.
- `Design Notes <https://simple-aws-ssm-parameter-store.readthedocs.io/en/latest/02-Design-Notes/index.html>`_: why the functions behave this way, and the cases to watch for.
- `API reference <https://simple-aws-ssm-parameter-store.readthedocs.io/en/latest/py-modindex.html>`_: every argument.


.. _install:

Install
------------------------------------------------------------------------------

``simple_aws_ssm_parameter_store`` is released on PyPI and needs Python 3.11 or newer:

.. code-block:: console

    $ pip install simple-aws-ssm-parameter-store

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade simple-aws-ssm-parameter-store
