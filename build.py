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
import shutil


sys.dont_write_bytecode = True

__version__ = 0.1
__date__ = '2017-11-29'
__updated__ = '2017-11-29'

TOOLCHAIN_BASIC_CONFIGURE = sys.executable + ' ' + \
    os.path.join('tools', 'waf-1.9.13') + ' ' + 'configure'
TOOLCHAIN_GCC_CHECK = '--check-c-compiler=gcc'


def start_process(cmd, supress_output=False):
    """Starts the build process by passing the command string to the
    command line

    Args:
        cmd (string): command for the build process.
        supress_output (bool): Indicates if logging is active for the build .
    """
    logging.debug(cmd)
    proc = subprocess.Popen(cmd, stdout=None, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    rtn_code = proc.returncode

    if supress_output is False:
        if out:
            logging.info(out)
        if err:
            logging.error(err)

    if rtn_code == 0 or rtn_code is None:
        logging.info('Success: Process return code %s', str(rtn_code))
    else:
        logging.error('Error: Process return code %s', str(rtn_code))
        sys.exit(1)


def build(mcu_switch=None, doxygen=False, supress_output=False):
    """Creates the build command string for the specified build and passes the
    build command string to `start_process` which actually starts the build
    process.

    Args:
        mcu_switch (string): specifies what will be built.
        doxygen (bool): specifies if the doxygen documentation to a mcu should
            be built.
        supress_output (bool): indicates if the output should appear on the
            command line.
    """
    cmd = TOOLCHAIN_BASIC_CONFIGURE + ' '
    if mcu_switch is None:
        cmd += 'sphinx'
    elif mcu_switch == '-p' or mcu_switch == '-s' or mcu_switch == '-b':
        cmd += 'build' + ' ' + mcu_switch
        if doxygen is True:
            cmd += ' ' + 'doxygen'
    else:
        logging.error('Invalid build argument: \'%s\'', mcu_switch)
        sys.exit(1)
    start_process(cmd, supress_output)

def styleguide(mcu_switch, supress_output=False):
    cmd = '{} {} styleguide_function'.format(TOOLCHAIN_BASIC_CONFIGURE, mcu_switch)
    start_process(cmd, supress_output=False)

def build_wrapper(cmd_line_args):
    b_pr = cmd_line_args.primary
    b_se = cmd_line_args.secondary
    b_bo = cmd_line_args.bootloader

    if cmd_line_args.all:
        build()
        build(mcu_switch='-p')
        build(mcu_switch='-p', doxygen=True)
        build(mcu_switch='-s')
        build(mcu_switch='-s', doxygen=True)
        build(mcu_switch='-b')
        build(mcu_switch='-b', doxygen=True)
    elif cmd_line_args.sphinx:
        build()
    elif (b_pr and not b_se and not b_bo) or \
         (not b_pr and b_se and not b_bo) or \
         (not b_pr and not b_se and b_bo):
        if cmd_line_args.primary:
            mcu_switch = '-p'
        elif cmd_line_args.secondary:
            mcu_switch = '-s'
        elif cmd_line_args.bootloader:
            mcu_switch = '-b'
        if cmd_line_args.doxygen:
            build(mcu_switch, cmd_line_args.doxygen)
        elif cmd_line_args.styleguide:
            styleguide(mcu_switch)
        else:
            build(mcu_switch)
    else:
        logging.error('Build combination not valid')

def clean_wrapper(cmd_line_args):
    c_pr = cmd_line_args.primary
    c_se = cmd_line_args.secondary
    c_bo = cmd_line_args.bootloader
    if cmd_line_args.all:
        clean()
        clean(mcu_switch='-p')
        clean(mcu_switch='-s')
        clean(mcu_switch='-b')
    elif cmd_line_args.sphinx:
        clean()
    elif (c_pr and not c_se and not c_bo) or \
         (not c_pr and c_se and not c_bo) or \
         (not c_pr and not c_se and c_bo):
            if cmd_line_args.primary:
                mcu_switch = '-p'
            if cmd_line_args.secondary:
                mcu_switch = '-s'
            if cmd_line_args.bootloader:
                mcu_switch = '-b'
            clean(mcu_switch)

def clean(mcu_switch=None, supress_output=False):
    cmd = TOOLCHAIN_BASIC_CONFIGURE +  ' '
    if mcu_switch is None:
        sphinx_build_dir = os.path.join('build', 'sphinx')
        if os.path.isdir(sphinx_build_dir):
            shutil.rmtree(sphinx_build_dir)
            print "Successfully removed sphinx documentation"
        else:
            print 'Nothing to clean...'
        return
    elif mcu_switch == '-p' or mcu_switch == '-s' or  mcu_switch == '-b' :
        cmd += ' ' + mcu_switch + ' ' + 'clean'
    else:
        print 'Invalid clean argument: \'{}\''.format(mcu_switch)
        sys.exit(1)
    start_process(cmd, supress_output)


def main(cmd_line_args):
    """Based on the input form command line the specified build string is
    passed to the build/clean wrapper function.

    Args:
        cmd_line_args (Namespace): command line arguments
    """
    if cmd_line_args.clean:
        clean_wrapper(cmd_line_args)
    if cmd_line_args.nobuild == False:
        build_wrapper(cmd_line_args)

if __name__ == '__main__':
    HELP_TEXT = """This script builds the software and documentation
repositories based on the specified commands."""
    parser = argparse.ArgumentParser(
        description=HELP_TEXT,
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=True)
    opt_args = parser.add_argument_group('optional arguments:')
    opt_args.add_argument('-nobld', '--nobuild', default=False,
                          action='store_true', required=False)
    opt_args.add_argument('-sphi', '--sphinx', action='store_true',
                          required=False, help='builds sphinx documenation')
    opt_args.add_argument('-p', '--primary', action='store_true',
                          required=False, help='builds primary binaries')
    opt_args.add_argument('-s', '--secondary', action='store_true',
                          required=False, help='builds secondary binaries')
    opt_args.add_argument('-b', '--bootloader', action='store_true',
                          required=False, help='builds bootloader binaries')
    opt_args.add_argument(
        '-dox',
        '--doxygen',
        action='store_true',
        required=False,
        help='builds the software documentation for the specified mcu (\'-p\'\
        ,\'-s\') of the bootloader (\'-b\')')
    opt_args.add_argument(
        '-a',
        '--all',
        action='store_true',
        required=False,
        help='generates all of the above mentioned')
    opt_args.add_argument('-v', '--verbose', action='store_true',
                          required=False, help='show diagnostic output')
    opt_args.add_argument('-sg', '--styleguide', action='store_true',
                          required=False, help='run styleguide function only')
    opt_args.add_argument('--clean', action='store_true',
                          required=False, help='cleans the specified option')
    CMD_LINE_ARGS = parser.parse_args()
    if CMD_LINE_ARGS.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    main(CMD_LINE_ARGS)
