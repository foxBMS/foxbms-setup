# @copyright &copy; 2010 - 2017, Fraunhofer-Gesellschaft zur Foerderung der angewandten Forschung e.V. All rights reserved.
#
# BSD 3-Clause License
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
# 1.  Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# 2.  Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# 3.  Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# We kindly request you to use one or more of the following phrases to refer to foxBMS in your hardware, software, documentation or advertising materials:
#
# &Prime;This product uses parts of foxBMS&reg;&Prime;
#
# &Prime;This product includes parts of foxBMS&reg;&Prime;
#
# &Prime;This product is derived from foxBMS&reg;&Prime;

"""
@file       build.py
@date       05.05.2017 (date of creation)
@author     foxBMS Team
@ingroup    tools
@prefix     none
@brief      build wrapper for waf

Helper script for building binaries and documentation of foxBMS
"""

import os
import sys
import subprocess
import argparse
import logging

sys.dont_write_bytecode = True

TOOLCHAIN_BASIC_CONFIGURE = sys.executable + ' ' + os.path.join('foxBMS-tools',
        'waf-1.8.12') + ' ' + 'configure'
TOOLCHAIN_GCC_CHECK = "--check-c-compiler=gcc"

def build_process(cmd, supress_output=False):
    logging.debug(cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
        stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    rtn_code = proc.returncode

    if supress_output is False:
        if out:
            logging.info(out)
        if err:
            logging.error(err)

    if rtn_code == 0 or rtn_code == None:
        print "Success: Process return code %s" % (str(rtn_code))
    else:
        print "Error: Process return code %s" % (str(rtn_code))
        sys.exit(1)

def build(mcu_switch=None, doxygen=False, supress_output=False):
    cmd = TOOLCHAIN_BASIC_CONFIGURE +  " "
    if mcu_switch is None:
        cmd += "sphinx"
    elif mcu_switch == "-p" or mcu_switch == "-s":
        cmd += "build" + " " + mcu_switch
        if doxygen is True:
            cmd += " " + "doxygen"
    else:
        logging.error("Invalid build argument: \"%s\"" % (mcu_switch))
        sys.exit()
    build_process(cmd, supress_output)

def main(cmd_line_args):
    if cmd_line_args.all:
        build()
        build(mcu_switch='-p')
        build(mcu_switch='-p', doxygen=True)
        build(mcu_switch='-s')
        build(mcu_switch='-s', doxygen=True)
    elif cmd_line_args.sphinx:
        build()
    elif (cmd_line_args.primary and not cmd_line_args.secondary) or \
        (not cmd_line_args.primary and cmd_line_args.secondary):
            if cmd_line_args.primary:
                mcu_switch = "-p"
            if cmd_line_args.secondary:
                mcu_switch = "-s"
            if cmd_line_args.doxygen:
                build(mcu_switch, cmd_line_args.doxygen)
            else:
                build(mcu_switch)
if __name__ == '__main__':
    HELP_TEXT = """This script builds the software and documentation
repositories based on the specified commands."""
    parser = argparse.ArgumentParser(description=HELP_TEXT, \
        formatter_class=argparse.RawTextHelpFormatter, add_help=True)
    opt_args = parser.add_argument_group('optional arguments:')
    opt_args.add_argument('-sphi', '--sphinx', action='store_true', \
        required=False, help='builds sphinx documenation')
    opt_args.add_argument('-p', '--primary', action='store_true', \
        required=False, help='builds primary binaries')
    opt_args.add_argument('-s', '--secondary', action='store_true', \
        required=False, help='builds secondary binaries')
    opt_args.add_argument('-dox', '--doxygen', action='store_true', \
        required=False, help='builds the software documentation for the specified mcu (-p, -s)')
    opt_args.add_argument('-a', '--all', action='store_true', \
        required=False, help='generates all of the above mentioned')
    opt_args.add_argument('-v', '--verbose', action='store_true', \
        required=False, help='show diagnostic output')
    CMD_LINE_ARGS = parser.parse_args()
    if CMD_LINE_ARGS.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    main(CMD_LINE_ARGS)
