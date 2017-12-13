# @copyright &copy; 2010 - 2017, Fraunhofer-Gesellschaft zur Foerderung der
#   angewandten Forschung e.V. All rights reserved.
#
# BSD 3-Clause License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1.  Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# 2.  Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# 3.  Neither the name of the copyright holder nor the names of its
#     contributors may be used to endorse or promote products derived from this
#     software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# We kindly request you to use one or more of the following phrases to refer to
# foxBMS in your hardware, software, documentation or advertising materials:
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
@brief      bootstrapper for foxBMS projects

Helper script for setting up a foxBMS project
"""

import argparse
import logging
import os
import posixpath
import subprocess
import sys
import yaml
sys.dont_write_bytecode = True
import build
# 'import build' after 'sys.dont_write_bytecode = True' since otherwise
# bytecode would be written.

__version__ = 1.0
__date__ = '2017-11-29'
__updated__ = '2017-12-06'

FOXBMSVERSION = 'latest'

GIT_PROGRAM = 'git'
GIT_CLONE = 'clone'

PRINT_MARK = '----------------------------------------------------------------------------'
BARE_EXTENSION = '.git'
"""string: Extension of bare git repository.
"""


def read_yaml(foxconf='.config.yaml'):
    """
    Returns:
        repos (list): List of repositories to be cloned. The list is
            structured like this:
            [ [{{repo names, ...}}, {{name of die directory to be}},
                {{some printable information about the repository}}], {{next}} ]
    """
    with open(foxconf, 'r') as stream:
        try:
            conf = yaml.load(stream)
        except yaml.YAMLError as exc:
            logging.error(exc)

    repos = []
    for key in conf:
        repo_info = key
        bootstrap_path = '.'
        if key != '.':
            if not os.path.isdir(key):
                os.mkdir(key)
            bootstrap_path = key
        else:
            repo_info = 'general'
        repos.append([conf[key], bootstrap_path, repo_info])
    return repos


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
        err_msg = '''
\'{}\' is not a git repository.
Did you download a .zip file from GitHub?

Use
    \'git clone https://github.com/foxBMS/foxBMS-setup\'
to download the foxBMS-setup repository.
        '''.format(setup_dir_path)
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
    logging.info(' Setting up \'%s\' repository', repo)


def check_subprocess_exit(program, rtn_code):
    if rtn_code == 0 or rtn_code is None:
        logging.info('Success: Process return code of \'%s\' is \'%s\'',
                     program, str(rtn_code))
    else:
        logging.error('Error: Process return code of \'%s\' is \'%s\'',
                      program, str(rtn_code))
        logging.error('Exiting...')
        sys.exit(1)


def clone_repo(repo_name, repo_path, repo_target_path):
    """Clones a specified repository

    - We clone the master branch
    - We check which branch contains the tag 'latest'
    - We checkout this branch

    Args:
        repo_name (string): Repository name that is cloned.
        repo_path (string): Repository path from where the repository is
            cloned.
    """
    version = 'master'  # fallback, as master always exists
    latest_tag_missing = True
    for _rep in ['hw', 'mcu', 'tools', 'documentation']:
        if _rep in repo_name:
            version = FOXBMSVERSION

    if os.path.isdir(os.path.join(repo_target_path, repo_name)):
        logging.error('repository \'{}\' already exists'.format(repo_name))
        pass  # we might still setup other repos
    else:
        # repository does not exist locally, therefore we clone
        logging.info('Cloning foxBMS repository \'%s\' from remote %s',
                     repo_name, repo_path)
        _action = GIT_CLONE
        _cwd = os.path.join(repo_target_path)
        # first we clone the master
        _cmd = '{} {} {}'.format(GIT_PROGRAM, _action, repo_path).strip()
        logging.info('%s', _cmd)
        rtn_code = subprocess.call(_cmd, cwd=_cwd)
        check_subprocess_exit(GIT_PROGRAM, rtn_code)
        # We start the search for the 'latest' tag and checkout the resulting
        # branch
        _cwd = os.path.join(repo_target_path, repo_name)
        logging.info('Searching tag \'%s\'', version)
        _cmd = '{} branch --all --contains {}'.format(GIT_PROGRAM, version).strip()
        logging.info('%s', _cmd)
        a = subprocess.Popen(_cmd, cwd=_cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        _out, _err = a.communicate()
        latest_branch = 'master'
        try:
            _out = _out.replace('*', '')
            _out = _out.strip()
            _out = _out.replace(' ', '')
            for line in _out.split('\n'):
                if latest_tag_missing is True:
                    b = line.split('/')[-1]
                    if b != '':
                        latest_branch = b
                        latest_tag_missing = False
                        logging.info('Found tag \'%s\' in \'%s\'', version, latest_branch)
        except IndexError as ierr:
            logging.warning('The tag \'%s\' might not exist.', version)
            logging.warning('Using \'master\' branch instead.')
        except BaseException:
            logging.error('Something undefined went wrong.')
            logging.warning('Using \'master\' branch instead.')
        if latest_tag_missing is True:
            logging.warning('The tag \'%s\' might not exist.', version)
            logging.warning('Using \'master\' branch instead.')

        _cmd = '{} checkout {}'.format(GIT_PROGRAM, latest_branch).strip()
        logging.info('%s', _cmd)
        rtn_code = subprocess.call(_cmd, cwd=_cwd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        check_subprocess_exit(GIT_PROGRAM, rtn_code)
        print '\n'


def setup_repo_class(repo_names, repo_paths, repo_target_path, setup_info):
    """Helper function for nicer output while cloning/fetching the repositories

    Args:
        repo_names (list): names of the repositories that will be setup.
        repo_paths (list): paths to the repositories that will be setup.
        setup_info (string): Initial information that will be printed
    """
    logging.info('\nSetting up the foxBMS %s dependencies', setup_info)
    logging.info(PRINT_MARK)
    for repo in repo_names:
        print_next_steps_info(repo)
    logging.info(PRINT_MARK)
    for repo, repo_path in zip(repo_names, repo_paths):
        clone_repo(repo, repo_path, repo_target_path)
    logging.info('done...\n')


def main(cmd_line_args):
    """Description of t main setup process
     - get all absolute paths of foxBMS repositories
     - clone all repositories or general and specified ones
     - build documentation (sphinx, and Doxygen for both microcontrollers) if
       not otherwise specified

    Args:
        cmd_line_args (Namespace): Arguments passed by the command line
    """
    if cmd_line_args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif cmd_line_args.verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    if cmd_line_args.specfiy_software_branch:
        global SW_VERSION
        SW_VERSION = cmd_line_args.specfiy_software_branch
    if cmd_line_args.specfiy_hardware_branch:
        global HW_VERSION
        HW_VERSION = cmd_line_args.specfiy_hardware_branch

    repository_basepath, setup_repo_name = get_main_git_path()

    logging.info(PRINT_MARK)
    logging.info('Setting up the foxBMS project in directory')
    logging.info(os.path.dirname(os.path.realpath(__file__)))
    logging.info(PRINT_MARK)

    # setup general software dependency repositories
    repo_list = read_yaml()
    for repos in repo_list:
        yaml_repos_abspath = set_git_paths(repository_basepath, repos[0])
        setup_repo_class(repos[0], yaml_repos_abspath, repos[1], repos[2])

    if cmd_line_args.specfiy_repos:
        info = 'specified repositories'
        setup_repo_class(specified_repos, specified_repos_abspath, info)

    if not cmd_line_args.dont_build_documentation:
        logging.info(PRINT_MARK)
        logging.info('Create foxBMS Documentation')
        logging.info(PRINT_MARK)
        logging.info('Create Sphinx Documentation')
        build.build(supress_output=True)
        logging.info(PRINT_MARK)
        logging.info('Create Primary MCU Doxygen Documentation')
        build.build('-p', doxygen=True, supress_output=True)
        logging.info(PRINT_MARK)
        logging.info('Create Secondary MCU Doxygen Documentation')
        build.build('-s', doxygen=True, supress_output=True)
        logging.info(PRINT_MARK)
        logging.info('done...')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    HELP_TEXT = '''Setup helper of foxBMS'''
    parser = argparse.ArgumentParser(description=HELP_TEXT, add_help=True)
    opt_args = parser.add_argument_group('optional arguments:')
    opt_args.add_argument('-sr', '--specfiy-repos', nargs='+', type=str,
                          required=False, help='Only the specified repository \
                          will be cloned/fetched')
    opt_args.add_argument('-sb', '--specfiy-software-branch', type=str,
                          required=False, help='Only the specified repository \
                          will be cloned/fetched')
    opt_args.add_argument('-hb', '--specfiy-hardware-branch', type=str,
                          required=False, help='Only the specified repository \
                          will be cloned/fetched')
    opt_args.add_argument('-dbd', '--dont-build-documentation',
                          action='store_true', required=False, help='If specified the \
            documenation will not be build after the checkout process')
    parser.add_argument(
        '--verbosity',
        '-v',
        action='count',
        default=0,
        help='increase output verbosity')
    CMD_LINE_ARGS = parser.parse_args()
    main(CMD_LINE_ARGS)
