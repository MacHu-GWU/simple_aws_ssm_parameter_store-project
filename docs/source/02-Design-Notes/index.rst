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


Writing Only When Something Changes
------------------------------------------------------------------------------
SSM keeps only the last 100 versions of a parameter. A deployment script that calls ``put_parameter`` with ``Overwrite=True`` on every run creates a new version each time, even when the value is the same, and after 100 runs the older versions are gone.

:func:`~simple_aws_ssm_parameter_store.client.put_parameter_if_changed` treats its arguments as the desired state of the parameter. It reads the parameter, compares, and calls ``put_parameter`` only if the parameter does not exist or differs, so running the same call again writes nothing. Its ``(before, after)`` result says what happened:

==========================  ==========================================================
``(before, after)``         Meaning
==========================  ==========================================================
``(None, Parameter)``       The parameter did not exist and was created.
``(Parameter, None)``       The parameter already matched; nothing was written.
``(Parameter, Parameter)``  The parameter differed; a new version was written.
==========================  ==========================================================

What is compared:

- **The value, always.** The current value is read with decryption, so a ``SecureString`` is compared by its plain value, whether you pass ``type`` as ``ParameterType.SECURE_STRING``, as the string ``"SecureString"``, or not at all. Reading it needs ``kms:Decrypt`` on its KMS key. For ``String`` and ``StringList``, AWS ignores the decryption flag.
- **Every other argument you pass:** ``description``, ``type``, ``tier``, ``key_id``, ``allowed_pattern``, ``policies``, and ``data_type``. An argument you leave out means "keep whatever the parameter has", and is not compared. A changed description with the same value is a change, and writes a new version.
- ``get_parameter`` does not return ``description``, ``tier``, ``key_id``, ``allowed_pattern``, or ``policies``. When you pass one of them, the function makes one extra ``describe_parameters`` call to read them.

Two exceptions to "compare what you pass":

- ``tier=ParameterTier.INTELLIGENT_TIERING`` is not compared: AWS stores such a parameter as Standard or Advanced, so the two never match.
- ``policies`` is compared as parsed JSON, ignoring key order and policy order. If either side cannot be parsed, it counts as changed, and the parameter is written.

``key_id`` is compared as a string, so pass it in the same form every time: an alias and the ARN of the same key count as different.

The ``after`` object is built from the arguments you passed and the ``put_parameter`` response, which holds only ``Version`` and ``Tier``. Fields such as ``ARN`` or ``LastModifiedDate`` are not in it; call :func:`~simple_aws_ssm_parameter_store.client.get_parameter` when you need them.


Concurrent Writers: Best Effort
------------------------------------------------------------------------------
SSM has no conditional write: ``put_parameter`` cannot say "only if the current version is still 3". The read and the write are two calls, so the result is as consistent as the API allows, and no more:

- **Two writers create the same parameter.** The create is sent without ``Overwrite``, so the second one fails with ``ParameterAlreadyExists`` instead of replacing the first. The function then reads and compares once more: if the other writer stored the same value, nothing is written; otherwise it is updated.
- **Two writers update an existing parameter at the same time.** Both may read the old value, and both may write: the last write wins, and two versions are used. Preventing that is outside this library. Serialize such writers yourself, for example with one deployment pipeline that runs one job at a time.


Tags Are Part of the Desired State
------------------------------------------------------------------------------
When you pass ``tags`` to :func:`~simple_aws_ssm_parameter_store.client.put_parameter_if_changed`, they become the parameter's full tag set:

- **On create,** they are sent with ``put_parameter``.
- **On an existing parameter,** ``put_parameter`` does not accept tags together with ``Overwrite``, so the function reads the current tags and, only if they differ, replaces them with :func:`~simple_aws_ssm_parameter_store.client.put_parameter_tags`. This happens whether or not the value changed. Tags have no versions, so a tag change alone still returns ``after`` as ``None``.
- **Left out,** the tags are kept as they are. Pass ``tags={}`` to remove them all.

To change tags without touching the parameter, use the tag functions:

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
