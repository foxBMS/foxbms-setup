"""Helper script for cleaning binaries and documentation of foxBMS
"""
import os
import sys
import subprocess
import argparse

sys.dont_write_bytecode = True

TOOLCHAIN_BASIC_CONFIGURE = 'python ' + os.path.join('foxBMS-tools',
        'waf-1.8.12') + ' configure'

def clean_prcoess(cmd, supress_output=False):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
        stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    if supress_output is False:
        if out:
            print out
        if err:
            print err

def clean(mcu_switch=None, supress_output=False):
    cmd = TOOLCHAIN_BASIC_CONFIGURE +  " "
    if mcu_switch is None:
        sphinx_build_dir = os.path.join("build", "sphinx")
        if sys.platform.startswith('win'):
            cmd = "del /s /q" + " " + sphinx_build_dir
        else:
            cmd = "find " + sphinx_build_dir + " -f -type f -delete"
    elif mcu_switch == "-p" or mcu_switch == "-s":
        cmd += " " + mcu_switch + " " + "clean"
    else:
        print "Invalid clean argument: \"%s\"" % (mcu_switch)
        sys.exit()
    clean_prcoess(cmd, supress_output)

def main(cmd_line_args):
    if cmd_line_args.all:
        clean()
        clean(mcu_switch='-p')
        clean(mcu_switch='-s')
    elif cmd_line_args.sphinx:
        clean()
    elif (cmd_line_args.primary and not cmd_line_args.secondary) or \
        (not cmd_line_args.primary and cmd_line_args.secondary):
            if cmd_line_args.primary:
                mcu_switch = "-p"
            if cmd_line_args.secondary:
                mcu_switch = "-s"
            clean(mcu_switch)
if __name__ == '__main__':
    HELP_TEXT = """This script cleans the software and documentation repositories
based on the specified commands."""
    parser = argparse.ArgumentParser(description=HELP_TEXT, \
        formatter_class=argparse.RawTextHelpFormatter, add_help=True)
    opt_args = parser.add_argument_group('optional arguments:')
    opt_args.add_argument('-sphi', '--sphinx', action='store_true', \
        required=False, help='cleans sphinx documenation')
    opt_args.add_argument('-p', '--primary', action='store_true', \
        required=False, help='cleans primary binaries and documentation')
    opt_args.add_argument('-s', '--secondary', action='store_true', \
        required=False, help='cleans secondary binaries and documentation')
    opt_args.add_argument('-dox', '--doxygen', action='store_true', \
        required=False, help='cleans the software documentation for the specified mcu (-p, -s)')
    opt_args.add_argument('-a', '--all', action='store_true', \
        required=False, help='cleans all of the above mentioned')
    CMD_LINE_ARGS = parser.parse_args()

    main(CMD_LINE_ARGS)
