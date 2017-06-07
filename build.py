"""Helper script for building binaries and documentation of foxBMS
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
    proc = subprocess.call(cmd, shell=True)

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
    HELP_TEXT = """This script builds the software and documentation repositories
based on the specified commands."""
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
