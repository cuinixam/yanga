.. _arduino-platform:

Arduino Platform
================

Configuration
-------------

.. literalinclude:: platform.yaml

Overview
--------

The Arduino platform configuration is designed to build the application for Arduino boards, specifically targeting the Arduino Uno.

Compile and Link Options
------------------------

- Compile Options: -Os, -Wall
- Link Options: -mmcu=atmega328p

Required Headers and Libraries
------------------------------

- Headers: Arduino.h
- Libraries: core, wire
