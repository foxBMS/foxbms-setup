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
@file       bootstrap.py
@date       05.05.2017 (date of creation)
@author     foxBMS Team
@ingroup    tools
@prefix     none
@brief      clean wrapper for waf

Helper script for setting up a foxBMS project
"""

import os
import sys
import subprocess
import argparse
import logging
import posixpath

sys.dont_write_bytecode = True
# "import build" after "sys.dont_write_bytecode = True" since otherwise
# bytecode would be written.
import build

SW_VERSION = "release-0.5.x"
HW_VERSION = "release-1.0.x"

PRINT_MARK = "----------------------------------------------------------------------------"
BARE_EXTENSION = ".git"
"""string: Extension of bare git repository.
"""
FOXBMS_APPLICATION_REPOS = ["foxBMS-documentation", "foxBMS-hardware",
                            "foxBMS-primary", "foxBMS-secondary"]
"""list: Repository that are needed for foxBMS application development.
"""
DEVEL_REPOS = [
    "foxBMS-bootloader",
    "foxBMS-can-bootloader",
    "foxBMS-flashtool"]
"""list: Repository that are needed for additional development.
"""
DEPENDENCY_REPOS = ["hal", "FreeRTOS", "foxBMS-tools"]
"""list: Generally needed repository that are needed to work with foxBMS hard-
and software.
"""


def get_main_git_path():
    """Gets the remote URL of the setup repository.

    Returns:
        string: remote URL of the setup-repository.
    """
    try:
        repository_basepath = subprocess.check_output(
            'git config --get remote.origin.url'.split(' '))
    except subprocess.CalledProcessError as err:
        setup_dir_path = os.path.dirname(os.path.realpath(__file__))
        err_msg = """
\"%s\" is not a git repository.
Did you download a .zip file from GitHub?

Use
    \'git clone https://github.com/foxBMS/foxBMS-setup\'
to download the foxBMS-setup repository.
        """ % (setup_dir_path)
        logging.error(err_msg)
        sys.exit(1)
    repository_basepath, repository_name = repository_basepath.rsplit('/', 1)
    return repository_basepath, repository_name


def set_git_paths(repository_basepath, repos):
    """Generates the remote URL of specified repositories.

    Args:
        repository_basepath (string): base path that should be prepend to the
            repository names.
        repos (string): names of the repositories to which their absolute path
            should be generated.
    Returns:
        list: All repositories with their absolute path.
    """
    repos_abspath = [posixpath.join(repository_basepath, repo + BARE_EXTENSION)
                     for repo in repos]
    return repos_abspath


def print_next_steps_info(repo):
    """Prints some information about the setup process.

    Args:
        repo (string): Repository that is setup.
    """
    logging.info(" Setting up \"%s\" repository", repo)

def check_subprocess_exit(program, rtn_code):
    if rtn_code == 0 or rtn_code is None:
        logging.info("Success: Process return code of \'%s\' is \'%s\'",
                          program, str(rtn_code))
    else:
        logging.error("Error: Process return code of \'%s\' is \'%s\'",
                       program, str(rtn_code))
        logging.error("Exiting...")
        sys.exit(1)

def clone_or_pull_repo(repo_name, repo_path):
    """Clones or pulls specified repository, depending if it already exists or
    not.

    Args:
        repo_name (string): Repository name that is cloned/pulled.
        repo_path (string): Repository path from where the repository is
            cloned/pulled.
    """
    if "hardware" in repo_name:
        version = HW_VERSION
    elif "primary" in repo_name or "secondary" in repo_name \
        or "tools" in repo_name or "documentation" in repo_name:
        version = SW_VERSION
    else:
        version = SW_VERSION
    program = "git"
    if os.path.isdir(repo_name):
        logging.info("Pulling foxBMS repository \"%s\" from remote %s",
                     repo_name, repo_path)
        cmd = "%s pull %s %s" % (program, repo_path, version)
        logging.info("%s", cmd)
        rtn_code = subprocess.call(cmd, cwd=repo_name)
    else:
        logging.info("Cloning foxBMS repository \"%s\" from remote %s",
                     repo_name, repo_path)
        cmd = "%s clone %s --branch %s" % (program, repo_path, version)
        logging.info("%s", cmd)
        rtn_code = subprocess.call(cmd)
    check_subprocess_exit(program, rtn_code)


def setup_repo_class(repo_names, repo_paths, setup_info):
    """Helper function for nicer output while cloning/pulling the repositories

    Args:
        repo_names (list): names of the repositories that will be setup.
        repo_paths (list): paths to the repositories that will be setup.
        setup_info (string): Initial information that will be printed
    """
    logging.info("\nSetting up the foxBMS %s dependencies", setup_info)
    logging.info(PRINT_MARK)
    for repo in repo_names:
        print_next_steps_info(repo)
    logging.info(PRINT_MARK)
    for repo, repo_path in zip(repo_names, repo_paths):
        clone_or_pull_repo(repo, repo_path)
    logging.info("done...\n")

def update():
    program = "git"
    cmd = "%s pull" % (program)
    rtn_code = subprocess.call(cmd)
    check_subprocess_exit(program, rtn_code)

def main(cmd_line_args):
    """Description of t main setup process
     - get all absolute paths of foxBMS repositories
     - clone all repositories or general and specified ones
     - build documentation (sphinx, and Doxygen for both microcontrollers) if
       not otherwise specified

    Args:
        cmd_line_args (Namespace): Arguments passed by the command line
    """
    if cmd_line_args.specfiy_software_branch:
        global SW_VERSION
        SW_VERSION = cmd_line_args.specfiy_software_branch
    if cmd_line_args.specfiy_hardware_branch:
        global HW_VERSION
        HW_VERSION = cmd_line_args.specfiy_hardware_branch

    repository_basepath, setup_repo_name = get_main_git_path()
    if cmd_line_args.update:
        update()
        logging.info("\nSuccessfully updated %s", setup_repo_name)
        logging.info("Run \'%s\' again to update the other repositories", __file__)
        sys.exit(0)
    dependency_repos_abspath = set_git_paths(
        repository_basepath, DEPENDENCY_REPOS)
    if cmd_line_args.specfiy_repos:
        specified_repos = cmd_line_args.specfiy_repos
        specified_repos_abspath = set_git_paths(
            repository_basepath, cmd_line_args.specfiy_repos)
    else:
        foxbms_application_repos_abspath = set_git_paths(
            repository_basepath, FOXBMS_APPLICATION_REPOS)
    devel_repos_abspath = set_git_paths(repository_basepath, DEVEL_REPOS)

    logging.info(PRINT_MARK)
    logging.info("Setting up the foxBMS project in directory")
    logging.info(os.path.dirname(os.path.realpath(__file__)))
    logging.info(PRINT_MARK)

    # setup general software dependency repositories
    info = "general software"
    setup_repo_class(DEPENDENCY_REPOS, dependency_repos_abspath, info)

    # setup foxBMS application development repositories
    if cmd_line_args.specfiy_repos:
        info = "specified repositories"
        setup_repo_class(specified_repos, specified_repos_abspath, info)
    else:
        info = "application development software"
        setup_repo_class(
            FOXBMS_APPLICATION_REPOS,
            foxbms_application_repos_abspath,
            info)

    # setup development tools
    if cmd_line_args.development_repos:
        info = "additional development software"
        setup_repo_class(DEVEL_REPOS, devel_repos_abspath, info)

    if not cmd_line_args.dont_build_documentation:
        # create documentation
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
    opt_args.add_argument('-u', '--update', action='store_true',
                          required=False, help='If specified, the setup \
        repository will be updated')
    opt_args.add_argument('-sr', '--specfiy-repos', nargs='+', type=str,
                          required=False, help='Only the specified repository \
                          will be cloned/pulled')
    opt_args.add_argument('-sb', '--specfiy-software-branch', type=str,
                          required=False, help='Only the specified repository \
                          will be cloned/pulled')
    opt_args.add_argument('-hb', '--specfiy-hardware-branch', type=str,
                          required=False, help='Only the specified repository \
                          will be cloned/pulled')
    opt_args.add_argument('-dbd', '--dont-build-documentation',
                          action='store_true', required=False, help='If specified the \
            documenation will not be build after the checkout process')
    opt_args.add_argument('-dev', '--development-repos', action='store_true',
                          required=False, help='If specified, additional development repositories \
        will be cloned/pulled')
    CMD_LINE_ARGS = parser.parse_args()
    main(CMD_LINE_ARGS)
