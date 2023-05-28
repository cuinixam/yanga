Variant
=======

Requirements
------------

.. item:: REQ-VARIANT_NAME-0.0.1
   :status: Approved

   A Variant **shall** have a unique name.

.. item:: REQ-VARIANT_SLUG-0.0.1
   :status: Approved

   A Variant **shall** have a unique slug generated from its name. The slug will be used to find a variant directory in the project structure.
   The user **shall not** be able to specify a custom slug for a variant.
   A slug is typically generated from the title/name of the resource by removing any special characters, converting spaces to hyphens, and making the string lowercase.

.. item:: REQ-VARIANT_DESCRIPTION-0.0.1
   :status: Approved

   A Variant **shall** have a description.

.. item:: REQ-VARIANT_TAGS-0.0.1
   :status: Approved

   A Variant **shall** have a list of tags.

Implementation
--------------

.. automodule:: yanga.spl.variant
   :members:
   :private-members:

Testing
-------

.. automodule:: test_variant
   :members:
   :show-inheritance:


Reports
-------

.. item-matrix:: Trace requirements to implementation
    :source: REQ-VARIANT
    :target: IMPL
    :sourcetitle: Requirement
    :targettitle: Implementation
    :stats:

.. item-piechart:: Implementation coverage chart
    :id_set: REQ-VARIANT IMPL
    :label_set: Not implemented, Implemented
    :sourcetype: fulfilled_by


.. item-matrix:: Requirements to test case description traceability
    :source: REQ-VARIANT
    :target: [IU]TEST
    :sourcetitle: Requirements
    :targettitle: Test cases
    :sourcecolumns: status
    :group: bottom
    :stats:
