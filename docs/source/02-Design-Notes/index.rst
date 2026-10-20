.. _design-notes:

Design Notes
==============================================================================
Why the functions of ``simple_aws_ssm_parameter_store`` behave the way they do, and the cases to watch for. Read :ref:`getting-started` first for what each function does.


A Thin Layer over boto3
------------------------------------------------------------------------------
Every function is a plain function that takes your own boto3 SSM client as its first argument. The library has no client class, no configuration, and no cache: it never decides which account, region, or credentials you use, and it works with any client you already have, including one created by moto in tests.

Each function maps to one or two calls of the raw API, and every argument that you leave out is not sent at all, so AWS applies its own defaults.


A Missing Parameter Is a Value, Not an Error
------------------------------------------------------------------------------
With the raw client, "does this parameter exist?" means catching ``ParameterNotFound``. Here the answer is a return value:

- :func:`~simple_aws_ssm_parameter_store.client.get_parameter` returns ``None`` when the parameter, or the requested version, does not exist.
- :func:`~simple_aws_ssm_parameter_store.client.delete_parameter` returns ``True`` if it deleted the parameter and ``False`` if there was nothing to delete, so a cleanup script can run any number of times.

Only "not found" is turned into a return value. Every other error, such as a missing permission or throttling, is raised as the usual ``botocore.exceptions.ClientError``.


Writing Only When the Value Changes
------------------------------------------------------------------------------
SSM keeps only the last 100 versions of a parameter. A deployment script that calls ``put_parameter`` with ``Overwrite=True`` on every run creates a new version each time, even when the value is the same, and after 100 runs the older versions are gone.

:func:`~simple_aws_ssm_parameter_store.client.put_parameter_if_changed` reads the current value first and writes only if it differs. Its ``(before, after)`` result says what happened:

==========================  ==========================================================
``(before, after)``         Meaning
==========================  ==========================================================
``(None, Parameter)``       The parameter did not exist and was created.
``(Parameter, None)``       The value was the same; nothing was written.
``(Parameter, Parameter)``  The value differed and was overwritten; the version went up.
==========================  ==========================================================

Two things follow from "read, then write":

- **One extra read per call.** This is the cost of keeping the version history.
- **It is not atomic.** If two processes write the same parameter at the same moment, both may read the old value and both may write. The function is meant for deployment and configuration scripts, not for a value that many writers update concurrently.

The ``after`` object is built from the arguments you passed and the ``put_parameter`` response, which holds only ``Version`` and ``Tier``. Fields such as ``ARN`` or ``LastModifiedDate`` are not in it; call :func:`~simple_aws_ssm_parameter_store.client.get_parameter` when you need them.


SecureString: Always Pass the Type
------------------------------------------------------------------------------
To compare a ``SecureString`` correctly, :func:`~simple_aws_ssm_parameter_store.client.put_parameter_if_changed` must read the current value decrypted. It does so only when ``type`` is ``ParameterType.SECURE_STRING``, a member of the :class:`~simple_aws_ssm_parameter_store.constants.ParameterType` enum.

.. warning::

    If you leave ``type`` out, or pass the plain string ``"SecureString"``, the current value is read encrypted. The ciphertext never equals your plain value, so the parameter is written, and its version goes up, on every call.


Tags on Create, Tag Functions After
------------------------------------------------------------------------------
``put_parameter`` does not accept tags when it overwrites an existing parameter. So the ``tags`` argument of :func:`~simple_aws_ssm_parameter_store.client.put_parameter_if_changed` is applied only when the call creates the parameter, and is ignored on an update. To change the tags of an existing parameter, use one of the three tag functions:

.. list-table::
    :header-rows: 1

    * - Function
      - Effect on the existing tags
    * - :func:`~simple_aws_ssm_parameter_store.client.update_parameter_tags`
      - Adds the given keys, or overwrites their values. Other tags are kept.
    * - :func:`~simple_aws_ssm_parameter_store.client.put_parameter_tags`
      - Makes the given dict the full tag set. ``{}`` removes every tag.
    * - :func:`~simple_aws_ssm_parameter_store.client.remove_parameter_tags`
      - Removes only the given keys.

:func:`~simple_aws_ssm_parameter_store.client.get_parameter_tags` returns the tags as a ``dict[str, str]``, and an empty dict when there are none.

SSM has no "replace all tags" call, so :func:`~simple_aws_ssm_parameter_store.client.put_parameter_tags` reads the current tags and, when some of them must go, removes all of them before adding the new set. Between those two calls the parameter briefly has no tags. When every current key is also in the new set, it skips the removal.


What the Library Does Not Do
------------------------------------------------------------------------------
- **No caching.** Every call goes to AWS. Cache the result yourself if you read the same parameter in a hot loop.
- **No bulk reads.** For ``get_parameters_by_path`` or ``describe_parameters``, use the boto3 client directly. :class:`~simple_aws_ssm_parameter_store.model.Parameter` can wrap any single item of their responses: ``Parameter(_data=item)``.
- **No version history.** :func:`~simple_aws_ssm_parameter_store.client.get_parameter` accepts a versioned name such as ``/app/key:3``, but listing versions (``get_parameter_history``) goes through the boto3 client.
