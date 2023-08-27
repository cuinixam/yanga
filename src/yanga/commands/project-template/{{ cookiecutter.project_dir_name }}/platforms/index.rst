Supported Platforms
===================

In the context of a build system, the term "platform" generally refers to the combination of hardware architecture and operating system for which the code is being compiled and linked. The platform defines certain characteristics and constraints that the build system must consider, such as:

* Operating System (OS): Different operating systems have different system libraries, system calls, and APIs. This can affect how the code is compiled and what libraries it can link against.
* Processor Architecture: This refers to the instruction set architecture (ISA) of the CPU, such as x86, x86_64, ARM, etc. Different architectures have different instructions, alignment requirements, and calling conventions, all of which must be considered by the compiler.
* Toolchain: The toolchain includes the compiler, linker, and other tools used to build the software. Different platforms might require different toolchains or different versions of the same toolchain.
* Standard Libraries and Dependencies: Different platforms might have different versions or even entirely different sets of standard libraries and other dependencies.
* Build Options and Flags: Certain compiler or linker flags may be specific to or have different effects on different platforms.
* Runtime Environment: The environment in which the program will run, including the presence or absence of certain system services or hardware features, may differ across platforms.

In practice, when working with a build system, one might have to provide platform-specific configurations or code paths. For example, you might need to link against different libraries, include different header files, or even use different source files entirely, depending on the target platform.
Modern build systems often provide mechanisms to handle platform-specific configurations more easily. This might include specifying platform-dependent compile flags, linking options, or even entirely separate build targets for different platforms.
The concept of a "platform" in this context is a way to encapsulate all these considerations, providing a shorthand for the complex combination of hardware, operating system, toolchain, and other factors that together define the environment for building and running a piece of software.

.. toctree::
   :maxdepth: 2

   windows_app/index.rst
   arduino/index.rst
