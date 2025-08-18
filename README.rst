
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

``simple_aws_ssm_parameter_store`` is a Pythonic wrapper library for AWS SSM Parameter Store that enhances the standard boto3 client with better error handling, existence testing, idempotent operations, and comprehensive tag management. Instead of dealing with exceptions for missing parameters or complex tag operations, this library provides intuitive functions that return meaningful values and handle edge cases gracefully.


Quick Tutorial
------------------------------------------------------------------------------
**1. Parameter Existence Testing**

Check if a parameter exists without handling exceptions. The function returns ``None`` for non-existent parameters instead of raising ``ParameterNotFound`` exceptions.

.. code-block:: python

    import boto3
    from simple_aws_ssm_parameter_store.api import get_parameter

    ssm_client = boto3.client("ssm")
    
    # Test if parameter exists
    param = get_parameter(ssm_client, "/app/database/host")
    if param is not None:
        print(f"Parameter exists with value: {param.value}")
    else:
        print("Parameter does not exist")

**2. Idempotent Parameter Deletion**

Delete parameters safely without worrying about whether they exist. The function returns ``True`` if deletion occurred, ``False`` if the parameter didn't exist.

.. code-block:: python

    from simple_aws_ssm_parameter_store import delete_parameter

    # Safe to call multiple times
    deleted = delete_parameter(ssm_client, "/app/temp/config")
    if deleted:
        print("Parameter was deleted")
    else:
        print("Parameter didn't exist")
    
    # Call again - no exception raised
    deleted = delete_parameter(ssm_client, "/app/temp/config")
    print(f"Second deletion attempt: {deleted}")

**3. Comprehensive Tag Management**

Manage parameter tags with intuitive functions for getting, updating, and replacing tags.

.. code-block:: python

    from simple_aws_ssm_parameter_store.api import (
        get_parameter_tags,
        update_parameter_tags, 
        put_parameter_tags,
        remove_parameter_tags
    )

    # Get all tags (returns empty dict if no tags)
    tags = get_parameter_tags(ssm_client, "/app/config")
    print(f"Current tags: {tags}")

    # Add/update specific tags (partial update)
    update_parameter_tags(ssm_client, "/app/config", {
        "Environment": "production",
        "Team": "platform"
    })

    # Replace all tags (full replacement)
    put_parameter_tags(ssm_client, "/app/config", {
        "Environment": "production",
        "Owner": "alice"
    })

    # Remove specific tags
    remove_parameter_tags(ssm_client, "/app/config", ["Team"])

    # Remove all tags
    put_parameter_tags(ssm_client, "/app/config", {})

Expected output progression:

.. code-block:: console

    Current tags: {}
    After update: {"Environment": "production", "Team": "platform"}
    After replacement: {"Environment": "production", "Owner": "alice"}
    After removal: {"Environment": "production", "Owner": "alice"}
    After clearing: {}

**4. Smart Parameter Updates (Version Management)**

Avoid unnecessary parameter writes and preserve version history with conditional updates. AWS SSM only keeps the last 100 versions - blindly updating parameters during debugging or deployment can quickly exhaust this limit and make older versions inaccessible.

.. code-block:: python

    from simple_aws_ssm_parameter_store.api import put_parameter_if_changed
    from simple_aws_ssm_parameter_store.constants import ParameterType

    # Smart update - only writes if value actually changed
    before, after = put_parameter_if_changed(
        ssm_client=ssm_client,
        name="/app/database/host",
        value="prod-db.example.com",
        type=ParameterType.STRING,
        overwrite=True
    )

    # Check what happened
    if before is None and after is not None:
        print(f"Parameter created: version {after.version}")
    elif before is not None and after is None:
        print(f"No update needed - value unchanged (version {before.version})")
    elif before is not None and after is not None:
        print(f"Parameter updated: {before.version} → {after.version}")

Example debugging scenario - avoiding version waste:

.. code-block:: python

    # During debugging, you might run this script multiple times
    # Without conditional updates, each run would increment the version
    
    # ❌ Bad: Always increments version (wastes version history)
    ssm_client.put_parameter(
        Name="/app/config/debug",
        Value="same-value",
        Type="String",
        Overwrite=True  # This always creates new version
    )
    
    # ✅ Good: Only increments version when value actually changes
    put_parameter_if_changed(
        ssm_client=ssm_client,
        name="/app/config/debug", 
        value="same-value",
        type=ParameterType.STRING,
        overwrite=True  # Only used when value differs
    )

Expected output progression:

.. code-block:: console

    # First run - parameter doesn't exist
    Parameter created: version 1
    
    # Second run - same value
    No update needed - value unchanged (version 1)
    
    # Third run - different value  
    Parameter updated: 1 → 2
    
    # Fourth run - same value again
    No update needed - value unchanged (version 2)

**5. Working with Parameter Objects**

Access parameter metadata through a rich Parameter object with convenient properties.

.. code-block:: python

    # Create a parameter first
    ssm_client.put_parameter(
        Name="/app/database/password",
        Value="secret123",
        Type="SecureString"
    )

    # Get parameter with decryption
    param = get_parameter(ssm_client, "/app/database/password", with_decryption=True)
    
    print(f"Name: {param.name}")
    print(f"Value: {param.value}")
    print(f"Type: {param.type}")
    print(f"Version: {param.version}")
    print(f"Is SecureString: {param.is_secure_string_type}")
    print(f"ARN: {param.arn}")

Expected output:

.. code-block:: console

    Name: /app/database/password
    Value: secret123
    Type: SecureString
    Version: 1
    Is SecureString: True
    ARN: arn:aws:ssm:us-east-1:123456789012:parameter/app/database/password


.. _install:

Install
------------------------------------------------------------------------------

``simple_aws_ssm_parameter_store`` is released on PyPI, so all you need is to:

.. code-block:: console

    $ pip install simple-aws-ssm-parameter-store

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade simple-aws-ssm-parameter-store
