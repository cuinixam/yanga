Command Line Handler
====================


Requirements
------------

.. item:: REQ-CMDLINE_REGISTER_COMMANDS-0.0.1 Register Commands
   :status: Approved

   The command-line interface shall support the registration of different commands.

.. item:: REQ-CMDLINE_COMMAND_ARGS-0.0.1 Command Arguments
   :status: Approved

   Each command shall support the registration of different arguments.

.. item:: REQ-CMDLINE_COMMAND_EXEC-0.0.1 Command Execution
   :status: Approved

   On execution, the command-line interface shall determine which registered command has been called and execute it with the provided arguments.

.. item:: REQ-CMDLINE_HELP-0.0.1 Help Message
   :status: Approved

   When no command is provided, the command-line interface shall print help messages to assist the user.

.. item:: REQ-CMDLINE_UNKNOWN_COMMAND-0.0.1 Command Error Handling
   :status: Approved

   If an unrecognized or unregistered command is provided, the command-line interface shall log an error message.

.. item:: REQ-CMDLINE_DUPLICATION-0.0.1 Command Duplication
   :status: Approved

   The command-line interface shall not allow the registration of two commands with the same name.

.. item:: REQ-CMDLINE_USER_CUSTOM-0.0.1 Load user defined commands
   :status: Approved

   The command-line interface shall support the loading of user defined commands.
   The user defined commands shall be loaded from a directory specified by the user.


Implementation
--------------

.. automodule:: yanga.core.cmd_line
   :members:
   :show-inheritance:

Testing
-------

.. automodule:: test_cmd_line
   :members:
   :show-inheritance:


Reports
-------

.. item-matrix:: Trace requirements to implementation
    :source: REQ-CMDLINE
    :target: IMPL
    :sourcetitle: Requirement
    :targettitle: Implementation
    :stats:

.. item-piechart:: Implementation coverage chart
    :id_set: REQ-CMDLINE IMPL
    :label_set: Not implemented, Implemented
    :sourcetype: fulfilled_by


.. item-matrix:: Requirements to test case description traceability
    :source: REQ-CMDLINE
    :target: [IU]TEST
    :sourcetitle: Requirements
    :targettitle: Test cases
    :sourcecolumns: status
    :group: bottom
    :stats:
