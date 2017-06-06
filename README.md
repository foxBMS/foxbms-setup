# foxBMS

foxBMS is a free, open and flexible development environment for the design of
battery management systems. It is the first universal BMS development
environment.

## foxBMS Project Setup
The general setup files for the foxBMS project are found in the foxBMS-setup
repository (https://github.com/foxBMS/foxBMS-setup). It includes a setup script
(bootstrap.py) which clone all needed repositories. After cloning the
repositories all needed documentation will be generated  automatically. The
documentation is found in directory ./build. There is a help available by
"python bootstrap.py -h"

The general documentation files for the foxBMS project are found in the
foxBMS-documentation repository
(https://github.com/foxBMS/foxBMS-documentation). The sphinx documentation is
found in foxBMS-documentation/doc/sphinx while the doxygen documentation
configuration is found in foxBMS-documentation/doc/doxygen. The doxygen
documentation itself is found in the software sources of the primary and
secondary microcontroller.

foxBMS is made out of two Microcontroller Units (MCU), named primary and
secondary. The C code for the primary MCU is found in the repository
foxBMS-primary (https://github.com/foxBMS/foxBMS-primary). The C code for the
secondary MCU is found in the repository foxBMS-secondary
(https://github.com/foxBMS/foxBMS-secondary).

The layout and schematic files for the foxBMS hardware are found in the
foxBMS-hardware repository (https://github.com/foxBMS/foxBMS-hardware).

The Hardware Abstraction Layer (hal) for foxBMS is in the hal-repository
(https://github.com/foxBMS/hal.) The real time operating system (FreeRTOS) for
foxBMS is in the FreeRTOS-repository (https://github.com/foxBMS/FreeRTOS.)

The tools needed for foxBMS are in the foxBMS-tools-repository
(https://github.com/foxBMS/foxBMS-tools.)

The foxConda-installer repository contains the installer for the foxConda
environment. This environment provides all the tools necessary to generate the
documentation, compile the code for the MCUs and flash the generated binaries on
the MCUs.

A generated version of the Sphinx documentation can be found at
http://foxbms.readthedocs.io/en/latest/. It explains the structure of the
foxBMS hardware, how to install the foxConda environment and how to use foxConda
to compile and flash the sources.

## Building the Sources
For building the software open a shell and type "python build.py -h". All 
available build options will be displayed.

## Cleaning the ./build-Directory
For cleaning instructions open a shell and type "python clean.py -h". All 
available cleaning options will be displayed.