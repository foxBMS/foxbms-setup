"""
:since:     Thu May 18 16:03:02 2017
:author:    Stefan Waldhoer <stefan.waldhoer@iisb.franhofer.de
$Id$

Helper script for cloning and pulling all needed foxBMS repositories
"""

import os
import sys
import subprocess
import argparse
import posixpath

sys.dont_write_bytecode = True

import build
import logging



PRINT_MARK = "----------------------------------------------------------------------------"
BARE_EXTENSION = ".git"
REPOSITORY_BASEPATH = ""
FOXBMS_APPLICATION_REPOS = ["foxBMS-documentation", "foxBMS-hardware", \
    "foxBMS-primary", "foxBMS-secondary", "foxBMS-tools"]
DEVEL_REPOS = ["foxBMS-bootloader", "foxBMS-can-bootloader", "foxBMS-flashtool"]
DEPENDENCY_REPOS = ["hal", "FreeRTOS"]

def set_git_paths():
    global DEPENDENCY_REPOS_ABSPATH
    global DEVEL_REPOS_ABSPATH
    global FOXBMS_APPLICATION_REPOS_ABSPATH

    REPOSITORY_BASEPATH = subprocess.check_output('git config --get remote.origin.url'.split(' '))
    REPOSITORY_BASEPATH = REPOSITORY_BASEPATH.rsplit('/', 1)[0]
    FOXBMS_APPLICATION_REPOS_ABSPATH = [posixpath.join(REPOSITORY_BASEPATH, \
        repo+BARE_EXTENSION) for repo in FOXBMS_APPLICATION_REPOS]
    DEVEL_REPOS_ABSPATH = [posixpath.join(REPOSITORY_BASEPATH, repo + BARE_EXTENSION) \
        for repo in DEVEL_REPOS]
    DEPENDENCY_REPOS_ABSPATH = [posixpath.join(REPOSITORY_BASEPATH, repo + BARE_EXTENSION) \
        for repo in DEPENDENCY_REPOS]

def print_next_steps_info(repo):
    logging.info(" Setting up \"%s\" repository" % (repo))

def clone_or_pull_repo(repo_name, repo_path):
    if os.path.isdir(repo_name):
        logging.info("Pulling foxbms repository \"%s\" from remote %s" % (repo_name, repo_path))
        cmd = "git pull"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
            stderr=subprocess.PIPE, cwd=repo_name, shell=True)
        out, err = proc.communicate()
    else:
        logging.info(" Cloning foxbms repository \"%s\" from remote %s" % (repo_name, repo_path))
        cmd = "git clone %s" % (repo_path)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
            stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
    if out:
        logging.info(out)
    if err:
        logging.info(err)

def setup_repo_class(repo_names, repo_paths, setup_info):
    logging.info("\nSetting up the foxbms %s dependencies" %(setup_info))
    logging.info(PRINT_MARK)
    for repo in repo_names:
        print_next_steps_info(repo)
    logging.info(PRINT_MARK)
    for repo, repo_path in zip(repo_names, repo_paths):
        clone_or_pull_repo(repo, repo_path)
    logging.info("done...\n")

def main(cmd_line_args):

    set_git_paths()
    print DEPENDENCY_REPOS, DEPENDENCY_REPOS_ABSPATH

    logging.info(PRINT_MARK)
    logging.info("Setting up the foxbms project in directory")
    logging.info(os.path.dirname(os.path.realpath(__file__)))
    logging.info(PRINT_MARK)

    # setup general software dependency repos
    info = "general software"
    setup_repo_class(DEPENDENCY_REPOS, DEPENDENCY_REPOS_ABSPATH, info)

    # setup foxBMS application development repos
    info = "application development software"
    setup_repo_class(FOXBMS_APPLICATION_REPOS, FOXBMS_APPLICATION_REPOS_ABSPATH, info)

    # setup develtools
    if cmd_line_args.development_repos:
        info = "additional development software"
        setup_repo_class(DEVEL_REPOS, DEVEL_REPOS_ABSPATH, info)

    # create documenation
    logging.info(PRINT_MARK)
    logging.info("Create foxBMS Documentation")
    logging.info(PRINT_MARK)
    logging.info("Create Sphinx Documentation")
    build.build(supress_output=True)
    logging.info(PRINT_MARK)
    logging.info("Create Primary MCU Doxygen Documentation")
    build.build('-p', doxygen=True, supress_output=True)
    logging.info(PRINT_MARK)
    logging.info("Create Secondary MCU Doxygen Documentation")
    build.build('-s', doxygen=True, supress_output=True)
    logging.info(PRINT_MARK)
    logging.info("done...")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    HELP_TEXT = """Setup helper of foxBMS"""
    parser = argparse.ArgumentParser(description=HELP_TEXT, add_help=True)
    opt_args = parser.add_argument_group('optional arguments:')
    opt_args.add_argument('-dev', '--development-repos', action='store_true', \
        required=False, help='If specified, additional development repositories \
        will be cloned/pulled')
    CMD_LINE_ARGS = parser.parse_args()
    main(CMD_LINE_ARGS)


