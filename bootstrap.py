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
"""string: Extension of bare git repository.
"""
FOXBMS_APPLICATION_REPOS = ["foxBMS-documentation", "foxBMS-hardware", \
    "foxBMS-primary", "foxBMS-secondary"]
"""list: Repository that are needed for foxBMS application development.
"""
DEVEL_REPOS = ["foxBMS-bootloader", "foxBMS-can-bootloader", "foxBMS-flashtool"]
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
    repository_basepath = subprocess.check_output('git config --get remote.origin.url'.split(' '))
    repository_basepath = repository_basepath.rsplit('/', 1)[0]
    return repository_basepath

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
    repos_abspath = [posixpath.join(repository_basepath, repo + BARE_EXTENSION) \
        for repo in repos]
    return repos_abspath

def print_next_steps_info(repo):
    """Prints some information about the setup process.

    Args:
        repo (string): Repository that is setup.
    """
    logging.info(" Setting up \"%s\" repository" % (repo))

def clone_or_pull_repo(repo_name, repo_path):
    """Clones or pulls specified repository, depending if it already exists or
    not.

    Args:
        repo_name (string): Repository name that is cloned/pulled.
        repo_path (string): Repository path from where the repository is
            cloned/pulled.
    """
    if os.path.isdir(repo_name):
        logging.info("Pulling foxBMS repository \"%s\" from remote %s" % (repo_name, repo_path))
        cmd = "git pull"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
            stderr=subprocess.PIPE, cwd=repo_name, shell=True)
        out, err = proc.communicate()
    else:
        logging.info(" Cloning foxBMS repository \"%s\" from remote %s" % (repo_name, repo_path))
        cmd = "git clone %s" % (repo_path)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
            stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
    if out:
        logging.info(out)
    if err:
        logging.info(err)

def setup_repo_class(repo_names, repo_paths, setup_info):
    """Helper function for nicer output while cloning/pulling the repositories

    Args:
        repo_names (list): names of the repositories that will be setup.
        repo_paths (list): paths to the repositories that will be setup.
        setup_info (string): Initial information that will be printed 
    """
    logging.info("\nSetting up the foxBMS %s dependencies" %(setup_info))
    logging.info(PRINT_MARK)
    for repo in repo_names:
        print_next_steps_info(repo)
    logging.info(PRINT_MARK)
    for repo, repo_path in zip(repo_names, repo_paths):
        clone_or_pull_repo(repo, repo_path)
    logging.info("done...\n")

def main(cmd_line_args):
    """Description of t main setup process
     - get all absolute paths of foxBMS repositories
     - clone all repositories or general and specified ones
     - build documentation (sphinx, and Doxygen for both microcontrollers) if
       not otherwise specified

    Args:
        cmd_line_args (Namespace): Arguments passed by the command line
    """
    repository_basepath = get_main_git_path()
    DEPENDENCY_REPOS_ABSPATH = set_git_paths(repository_basepath, DEPENDENCY_REPOS)
    if cmd_line_args.specfiy_repos:
        SPECIFIED_REPOS = cmd_line_args.specfiy_repos
        SPECIFIED_REPOS_ABSPATH = set_git_paths(repository_basepath, cmd_line_args.specfiy_repos)
    else:
        FOXBMS_APPLICATION_REPOS_ABSPATH = set_git_paths(repository_basepath, FOXBMS_APPLICATION_REPOS)
    DEVEL_REPOS_ABSPATH = set_git_paths(repository_basepath, DEVEL_REPOS)

    logging.info(PRINT_MARK)
    logging.info("Setting up the foxBMS project in directory")
    logging.info(os.path.dirname(os.path.realpath(__file__)))
    logging.info(PRINT_MARK)

    # setup general software dependency repositories
    info = "general software"
    setup_repo_class(DEPENDENCY_REPOS, DEPENDENCY_REPOS_ABSPATH, info)

    # setup foxBMS application development repositories
    if cmd_line_args.specfiy_repos:
        info = "specified repositories"
        setup_repo_class(SPECIFIED_REPOS, SPECIFIED_REPOS_ABSPATH, info)
    else:
        info = "application development software"
        setup_repo_class(FOXBMS_APPLICATION_REPOS, FOXBMS_APPLICATION_REPOS_ABSPATH, info)

    # setup development tools
    if cmd_line_args.development_repos:
        info = "additional development software"
        setup_repo_class(DEVEL_REPOS, DEVEL_REPOS_ABSPATH, info)

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
    opt_args.add_argument('-sr', '--specfiy-repos', nargs='+', type=str,
        required=False, help='Only the specified repository will be cloned/\
        pulled')
    opt_args.add_argument('-dbd', '--dont-build-documentation', \
        action='store_true', required=False, help='If specified the \
            documenation will not be build after the checkout process')
    opt_args.add_argument('-dev', '--development-repos', action='store_true', \
        required=False, help='If specified, additional development repositories \
        will be cloned/pulled')
    CMD_LINE_ARGS = parser.parse_args()
    main(CMD_LINE_ARGS)


