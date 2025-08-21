Updating Validation Rules
===========================

The OSD system uses validation rules defined in ``mid-validation-constants.json`` and ``low-validation-constants.json`` files to perform semantic validation of telescope commands. These rules are tightly coupled with the capabilities defined in ``mid_capabilities.json`` and ``low_capabilities.json``.

Rule Structure and Capabilities Coupling
-----------------------------------------

Validation rules reference capability values using placeholder variables. For example:

.. code-block:: json

    {
        "rule": "(0 < len(receptor_ids) <= number_ska_dishes)",
        "error": "receptor_ids are too many! Current Limit is {number_ska_dishes}"
    }

The variable ``number_ska_dishes`` in this rule corresponds to the ``number_ska_dishes`` field in ``mid_capabilities.json``:

.. code-block:: json

    {
        "AA0.5": {
            "number_ska_dishes": 4
        },
        "AA1": {
            "number_ska_dishes": 8
        },
        "AA2": {
            "number_ska_dishes": 64
        }
    }

Adding New Validation Rules
----------------------------

To add a new validation rule:

1. **Identify the command path**: Determine where in the command structure your rule applies (e.g., ``dish.receptor_ids``, ``sdp.execution_block.beams``).

2. **Define the rule**: Create a rule object with ``rule`` and ``error`` fields.

3. **Add capability constraints if needed**: If your rule references capability values, ensure they exist in ``mid_capabilities.json``.

**Example: Adding a new rule for maximum beam count**

1. First, add the capability constraint to ``mid_capabilities.json``:

.. code-block:: json

    {
        "AA0.5": {
            "max_beams_per_execution_block": 2,
            "number_ska_dishes": 4
        }
    }

2. Then add the validation rule to ``mid-validation-constants.json``:

.. code-block:: json

    {
        "AA0.5": {
            "assign_resource": {
                "sdp": {
                    "execution_block": {
                        "parent_key_rule": [
                            {
                                "rule": "len(beams) <= max_beams_per_execution_block",
                                "error": "Too many beams! Maximum allowed is {max_beams_per_execution_block}"
                            }
                        ]
                    }
                }
            }
        }
    }

Updating Existing Rules
-----------------------

To modify an existing rule:

1. **Locate the rule**: Find the rule in the appropriate array assembly section (AA0.5, AA1, AA2).

2. **Update the rule expression**: Modify the ``rule`` field with new validation logic.

3. **Update the error message**: Modify the ``error`` field to reflect the new validation.

4. **Update capabilities if needed**: If the rule references new capability values, add them to ``mid_capabilities.json``.

**Example: Updating receptor_ids validation**

Original rule:

.. code-block:: json

    {
        "rule": "(0 < len(receptor_ids) <= number_ska_dishes)",
        "error": "receptor_ids are too many!Current Limit is {number_ska_dishes}"
    }

Updated rule with minimum constraint:

.. code-block:: json

    {
        "rule": "(min_receptor_count <= len(receptor_ids) <= number_ska_dishes)",
        "error": "receptor_ids count must be between {min_receptor_count} and {number_ska_dishes}"
    }

And add the new capability to ``mid_capabilities.json``:

.. code-block:: json

    {
        "AA0.5": {
            "min_receptor_count": 2,
            "number_ska_dishes": 4
        }
    }

Rule Types and Syntax
---------------------

**Basic Comparison Rules:**

.. code-block:: json

    {
        "rule": "receiver_band in ['1','2']",
        "error": "Invalid receiver_band! Allowed values: [1,2]"
    }

**Length-based Rules:**

.. code-block:: json

    {
        "rule": "(0 < len(fsp_ids) <= number_fsps)",
        "error": "Too many fsp_ids! Maximum: {number_fsps}"
    }

**Set Operations:**

.. code-block:: json

    {
        "rule": "set(receptor_ids).difference(set(number_dish_ids))",
        "error": "Invalid receptor_ids! Allowed: {number_dish_ids}"
    }

**Dependency Rules:**

For rules that depend on other fields in the same command:

.. code-block:: json

    {
        "rule": "freq_min < freq_max",
        "error": "freq_min must be less than freq_max",
        "dependency_key": ["freq_min"]
    }

**Parent Key Rules:**

For validating array elements:

.. code-block:: json

    {
        "parent_key_rule": [
            {
                "rule": "len(beams) == 1",
                "error": "Only one beam allowed"
            }
        ],
        "beams": {
            "function": [
                {
                    "rule": "function == 'visibilities'",
                    "error": "Invalid function! Must be 'visibilities'"
                }
            ]
        }
    }

Best Practices
--------------

1. **Keep rules simple**: Complex logic should be broken into multiple rules.

2. **Use descriptive error messages**: Include the expected values and current constraints.

3. **Reference capability values**: Use placeholder variables (e.g., ``{number_ska_dishes}``) instead of hardcoded values.

4. **Test thoroughly**: Validate rules with both valid and invalid input data.

5. **Update all array assemblies**: If a rule applies to multiple array assemblies (AA0.5, AA1, AA2), update all relevant sections.

6. **Maintain consistency**: Use consistent naming conventions for capability variables across different array assemblies.

Example: Complete Rule Addition Workflow
----------------------------------------

Let's add a rule to validate that channel_count is within acceptable limits:

**Step 1**: Add capability constraints to ``mid_capabilities.json``:

.. code-block:: json

    {
        "AA0.5": {
            "min_channel_count": 1,
            "max_channel_count": 58982,
            "number_ska_dishes": 4
        }
    }

**Step 2**: Add validation rule to ``mid-validation-constants.json``:

.. code-block:: json

    {
        "AA0.5": {
            "configure": {
                "csp": {
                    "midcbf": {
                        "correlation": {
                            "processing_regions": {
                                "channel_count": [
                                    {
                                        "rule": "min_channel_count <= channel_count <= max_channel_count",
                                        "error": "channel_count must be between {min_channel_count} and {max_channel_count}"
                                    },
                                    {
                                        "rule": "(channel_count % 20) == 0",
                                        "error": "channel_count must be a multiple of 20"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
    }

**Step 3**: Test the rule with sample data to ensure it works correctly.

**Step 4**: Update documentation and commit changes.

Troubleshooting Common Issues
-----------------------------

1. **Missing capability reference**: If a rule references a capability that doesn't exist, validation will fail. Ensure all referenced variables exist in ``mid_capabilities.json``.

2. **Incorrect path structure**: Rules must match the exact JSON path structure of the command being validated.

3. **Syntax errors**: Rule expressions must use valid Python syntax as they are evaluated using ``simpleeval``.

4. **Circular dependencies**: Avoid rules that create circular references between fields.

5. **Array assembly mismatch**: Ensure rules are added to the correct array assembly sections (AA0.5, AA1, AA2) based on the telescope configuration.