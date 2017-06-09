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

"""Top dir WAF script
"""
import os
import sys
import re
import datetime
import json
import platform
import subprocess
import ConfigParser

from waflib import Logs, Utils, Context, Options
from waflib import Task, TaskGen
from waflib.Tools.compiler_c import c_compiler

# console colors
COLOR_P = '\x1b[35m'  # pink
COLOR_N = '\x1b[0m'  # normal
COLOR_C = '\x1b[36m'  # cyan

# Boolean indicator for the project that will be built.
PRIMARY = False
SECONDARY = False
BOOTLOADER = False
SPHINX = False

# Check that only meaningful combinations of parameters are executed.
# Possible options are:
#   - TODO
if (len(sys.argv) == 2) and ('configure' in sys.argv):
    print "Configure project needs at least one more argument."
    sys.exit()
elif (len(sys.argv) > 3) and 'sphinx' in sys.argv and 'clean' not in sys.argv:
    print r"Build sphinx documentation by \"pyhton \
        foxBMS-tools\waf-1.8.12 configure sphinx\""
    sys.exit()
else:
    if ('-p' in sys.argv and '-s' in sys.argv) or \
        ('-p' in sys.argv and '-b' in sys.argv) or \
        ('-s' in sys.argv and '-b' in sys.argv):
        print "Specify one mcu (option: -p, -s, -b), not a \
            combination of these parameters."
        sys.exit()
    if ('chksum_function' in sys.argv) and not ('-p' in sys.argv \
        or '-s' in sys.argv or '-b' in sys.argv):
        print "Specfify a project to run the chksum tool on"
        sys.exit()
    if ('size_function' in sys.argv) and not ('-p' in sys.argv \
        or '-s' in sys.argv or '-b' in sys.argv):
        print "Specfify a project to run the size tool on"
        sys.exit()
    if ('doxygen' in sys.argv) and not ('-p' in sys.argv \
        or '-s' in sys.argv or '-b' in sys.argv):
        print "Specfify a project to generate the doxygen \
            documentation for"
        sys.exit()
    # all wrong input combinations should now be handeld. The task
    # of the build is now unambiguose defined.
    if '-p' in sys.argv:
        PRIMARY = True
    elif '-s' in sys.argv:
        SECONDARY = True
    elif '-b' in sys.argv:
        BOOTLOADER = True
    elif 'sphinx' in sys.argv:
        SPHINX = True
    else:
        print "Specify the mcu (option: -p, -s) to build the socures \
            or doxygen documentation"
        sys.exit()

# The top output dir is always './build/' relative to the directory
# the foxBMS-setup was configured in.
# Set sub build directory and build option as now the project goal
# is defined
TOP_BUILD_DIR = 'build'
if PRIMARY:
    BLD_OPTION = '-p'
    SUB_BUILD_DIR = 'primary'
if SECONDARY:
    BLD_OPTION = '-s'
    SUB_BUILD_DIR = 'secondary'
if BOOTLOADER:
    BLD_OPTION = '-b'
    SUB_BUILD_DIR = 'bootloader'
if SPHINX:
    BLD_OPTION = 'sphinx'
    SUB_BUILD_DIR = 'sphinx'

out = os.path.join(TOP_BUILD_DIR, SUB_BUILD_DIR)
OUT = out # !DO NOT DELETE! - NEEDED FOR CHKSUM TASK

VERSION = "0.4"
APPNAME = "foxbms"
VENDOR  = "Fraunhofer IISB"

CONFIG_HEADER = APPNAME + 'config.h'
ELF_FILE = os.path.join(APPNAME + '.elf')
HEX_FILE = os.path.join(APPNAME + '.hex')
BIN_FLASH = os.path.join(APPNAME + '_flash.bin')
BIN_FLASH_HEADER = os.path.join(APPNAME + '_flashheader.bin')

WAF_REL_PATH = os.path.join("foxBMS-tools", "waf-1.8.12")
DOC_TOOL_DIR = os.path.join("foxBMS-tools", "waftools")
CHKSUM_SCRIPT_REL_PATH = os.path.join("foxBMS-tools", "checksum", "chksum.py")
CHKSUM_INI_FILE_REL_PATH = os.path.join("foxBMS-tools", "checksum", "chksum.ini")
STYLEGUIDE_SCRIPT_REL_PATH = os.path.join("foxBMS-tools", "styleguide", "checkall.py")

SPHINX_DOC_DIR = os.path.join("foxBMS-documentation", "doc", "sphinx")
DOXYGEN_DOC_DIR = os.path.join("foxBMS-documentation", "doc", "doxygen")


def options(opt):
    """Options that can be passed to waf
    """
    opt.load('compiler_c')
    opt.load(['doxygen', 'sphinx_build'], tooldir=DOC_TOOL_DIR)
    opt.add_option('-c', '--config', action='store', default=None, \
        help='file containing additional configuration variables', \
        dest='configfile')
    opt.add_option('-t', '--target', action='store', default='debug', \
        help='build target: debug (default)/release', dest='target')
    opt.add_option('-p', '--primary', action='store_true', \
        default=False, help='build target: debug (default)/release', \
        dest='primary')
    opt.add_option('-s', '--secondary', action='store_true', \
        default=False, help='build target: debug (default)/release', \
        dest='secondary')
    opt.add_option('-b', '--bootloader', action='store_true', \
        default=False, help='build target: debug (default)/release', \
        dest='bootloader')

def load_config_file():
    """Loads the configuration file if existing
    """
    _fname = Options.options.configfile
    if _fname is None:
        return
    json.load(_fname)

def configure(conf):
    """Waf function "configure"
    Invoked by: "python foxBMS-tools/waf-1.8.12 configure"

    Configures waf for building the sources and the documentation.
    After "configure" and the waf-lock files are generated, one is
    able to run "python foxBMS-tools/waf-1.8.12 build" or "python
    foxBMS-tools/waf-1.8.12 chksum" without calling "python
    foxBMS-tools/waf-1.8.12 configure" first.
    """
    load_config_file()
    # prefix for all gcc related tools
    pref = 'arm-none-eabi'

    if sys.platform.startswith('win'):

        conf.env.CC = pref + '-gcc.exe'
        conf.env.AR = pref + '-ar.exe'
        conf.find_program(pref + '-strip', var='STRIP')
        conf.env.LINK_CC = pref + '-g++.exe'
        conf.find_program(pref + '-objcopy', var='hexgen')
        conf.find_program(pref + '-size', var='SIZE')
        conf.find_program('python', var='PYTHON')
        conf.find_program('dot', var='dot')
    else:
        conf.env.CC = pref + '-gcc'
        conf.env.AR = pref + '-ar'
        conf.env.LINK_CC = pref + '-g++'
        conf.find_program(pref + '-strip', var='STRIP')
        conf.find_program(pref + '-objcopy', var='hexgen')
        conf.find_program(pref + '-size', var='SIZE')
        conf.find_program('python', var='PYTHON')
        conf.find_program('dot', var='dot')
    conf.env.CFLAGS = '-mcpu=cortex-m4 -mthumb -mlittle-endian -mfloat-abi=softfp -mfpu=fpv4-sp-d16 -fmessage-length=0 -fno-common -fsigned-char -ffunction-sections -fdata-sections -ffreestanding -fno-move-loop-invariants -Wall -std=c99'.split(' ')
    conf.env.CFLAGS += str('-DBUILD_VERSION=\"' + str(VERSION) + '\"').split(' ')
    conf.env.CFLAGS += str('-DBUILD_APPNAME=\"' + str(APPNAME) + '\"').split(' ')
    conf.env.CFLAGS += '-DDEBUG -DUSE_FULL_ASSERT -DTRACE -DOS_USE_TRACE_ITM -DUSE_HAL_DRIVER -DHSE_VALUE=8000000'.split(' ')
    for key in c_compiler: # force only using gcc
        c_compiler[key] = ['gcc']
    conf.load('compiler_c')
    conf.load(['doxygen', 'sphinx_build'])
    conf.find_program('git', mandatory=False)

    conf.env.version = VERSION
    conf.env.appname = APPNAME
    conf.env.vendor = VENDOR

    if PRIMARY:
        LDSCRIPT = os.path.join("foxBMS-primary","src","STM32F429ZIT6_FLASH.ld")
    elif SECONDARY:
        LDSCRIPT = os.path.join("foxBMS-secondary","src","STM32F429ZIT6_FLASH.ld")
    elif BOOTLOADER:
        LDSCRIPT = os.path.join("foxBMS-bootloader", "src", "STM32F429ZIT6_FLASH.ld")
    else:
        LDSCRIPT = ""

    conf.env.ldscript = os.path.join(conf.srcnode.abspath(), LDSCRIPT)
    try:
        conf.env.buildno = conf.cmd_and_log(conf.env.GIT[0] + ' rev-parse --short HEAD').strip()
    except:
        conf.env.buildno = 'none'
    utcnow = datetime.datetime.utcnow()
    utcnow = ''.join(utcnow.isoformat('-').split('.')[0].replace(':', '-').split('-'))
    conf.env.timestamp = utcnow
    for k in 'gcc ar cpp ranlib as'.split():
        print pref + '-' + k, k.upper()
        conf.find_program(pref + '-' + k, var=k.upper(), mandatory=True)

    conf.define('BUILD_APPNAME', APPNAME)
    conf.define('BUILD_VERSION', VERSION)
    conf.define('BUILD_VENDOR', VENDOR)
    conf.define('BUILD_LDSCRIPT', conf.env.ldscript)
    conf.define('BUILD_NUMBER', conf.env.buildno)
    conf.define('TOOLCHAIN_WAF_ENABLED', 1)
    conf.define('STM32F429xx', 1)
    conf.define('USE_DRIVER_HAL', 1)
    conf.define('INCLUDE_eTaskGetState', 1)
    conf.env.target = conf.options.target
    conf.env.EXT_CC += ['.S']

    env_debug = conf.env.derive()
    env_debug.detach()
    env_release = conf.env.derive()
    env_release.detach()

    # configuration for debug
    conf.setenv('debug', env_debug)
    conf.define('RELEASE', 1)
    conf.undefine('DEBUG')
    conf.env.CFLAGS += ['-g', '-O0']
    env_debug.basename = conf.env.appname + '-' + conf.env.version + '-' + conf.env.buildno + '-' + conf.env.timestamp + '-debug'
    env_debug.PREFIX = conf.env.appname + '-' + conf.env.version + '-' + conf.env.buildno + '-' + conf.env.timestamp

    # configuration for release
    conf.setenv('release', env_release)
    conf.env.CFLAGS += ['-O2']
    env_release.basename = conf.env.appname + '-' + conf.env.version + '-' + conf.env.buildno + '-' + conf.env.timestamp + '-release'
    env_release.PREFIX = conf.env.appname + '-' + conf.env.version + '-' + conf.env.buildno + '-' + conf.env.timestamp
    if conf.options.target == 'release':
        conf.setenv('', env_release)
    else:
        conf.setenv('', env_debug)

    env_release.store(os.path.join(out, 'env-store.log'))
    conf.write_config_header(CONFIG_HEADER)

    print 'Basename:    ', conf.env.basename
    print 'Prefix:      ', conf.env.PREFIX
    try:
        print 'CFLAGS:      ', conf.env.CFLAGS[0]
        for i, flag in enumerate(conf.env.CFLAGS):
            if i != 0:
                print '             ', flag
    except:
        print '\nno CFLAGS specified'

def cleanall(conf):
    """cleans all binary files
    """
    removed_files = 0
    if os.path.isdir(out):
        for root, directories, filenames in os.walk(out):
            clean_file_extensions = ['.a', '.o', '.h', '.elf', '.bin']
            to_clean_files = ''
            for ext in clean_file_extensions:
                to_clean_files += '\\' + ext + '|'
            to_clean_files = to_clean_files[:-1]
            del_regex = re.compile(to_clean_files)
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if del_regex.match(os.path.splitext(file_path)[1]):
                    os.remove(file_path)
                    removed_files += 1
    print COLOR_P + 'successfully cleaned all ', clean_file_extensions, \
        'files (', removed_files, ' files removed).' + COLOR_N
    print 'run "waf configure" first, to be able to build again.'

def rem(conf):
    '''Removes the build directory if it exists
    Invoked by: "python foxBMS-tools/waf-1.8.12 rem"

    rem is not feature but a function and has to be called python
    foxBMS-tools/waf-1.8.12 configure rem.
    The 'build' directory and all subfolder and files are deleted
    by "rm -rf" on *nix and "del /s /q" on Windows.
    '''
    if os.path.isdir(out):
        if sys.platform.startswith('win'):
            cmd = 'rmdir /s /q ' + out
            print cmd
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
                stderr=subprocess.PIPE, shell=True)
            out, err = proc.communicate()
            if out:
                print out
            if err:
                print err
            cmd = 'del /s /q build.log'
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
                stderr=subprocess.PIPE, shell=True)
            out, err = proc.communicate()
            if out:
                print out
            if err:
                print err
        else:
            cmd = 'rm -rf ' + out
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
                stderr=subprocess.PIPE, shell=True)
            out, err = proc.communicate()
            if out:
                print out
            if err:
                print err
            cmd = 'rm -rf build.log'
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
                stderr=subprocess.PIPE, shell=True)
            out, err = proc.communicate()
            if out:
                print out
            if err:
                print err
        print 'Successfully cleaned build dir and log files.'
    else:
        print 'Nothing to clean.'


def build(bld):
    """Waf function "rem"
    Invoked by: "python foxBMS-tools/waf-1.8.12 build"

    A wscript with a function "build" must exists in every sub-directory that
    is built. The build instructions for the sub-directories have to be
    specified in the wscripts in the subdirectories.
    """
    import sys
    import logging
    from waflib import Logs
    log_file_prefix = 'build'
    log_file_extentsion = '.log'
    log_file = 'build.log'
    src_file_build = False
    # enables logging for build routine
    if bld.options.primary:
        bld_recurse_directory = os.path.normpath('foxBMS-primary')
        log_file_name = 'primary'
        src_file_build = True
    elif bld.options.secondary:
        bld_recurse_directory = os.path.normpath('foxBMS-secondary')
        log_file_name = 'secondary'
        src_file_build = True
    elif bld.options.bootloader:
        bld_recurse_directory = os.path.normpath('foxBMS-bootloader')
        log_file_name = 'bootloader'
        src_file_build = True
    else:
        log_file_name = 'default'
    if src_file_build:
        log_file = log_file_prefix + '_' + log_file_name + log_file_extentsion
        log_file = os.path.join(TOP_BUILD_DIR, log_file)
        bld.logger = Logs.make_logger(log_file, out)
        hdlr = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(message)s')
        hdlr.setFormatter(formatter)
        bld.logger.addHandler(hdlr)
        bld.recurse(bld_recurse_directory)

def dist(conf):
    """Waf function "rem"
    Invoked by: "python foxBMS-tools/waf-1.8.12 dist"

    Packs the current status of the project in a tar.gz file
    """
    conf.base_name = 'foxbms'
    conf.algo = 'tar.gz'
    conf.excl = ' Packages workspace **/.waf-1* **/*~ **/*.pyc **/*.swp **/.lock-w* **/env.txt **/log.txt **/.git **/build **/*.tar.gz **/.gitignore **/tools/waf-1.8.12-*'

# START CHKSUM TASK DESCRIPTION
class chksum(Task.Task):
    """Waf function "size"
    Invoked by: "python foxBMS-tools/waf-1.8.12 size"

    Calculates the size of all libraries the foxbms.elf file.

    Gets all object files in the build directory (by file extension *.o) and the main foxbms.elf binary and processes
    the object with size in berkley format.
    """
    cmd = os.path.join(os.getcwd(), WAF_REL_PATH)
    _temp = ''
    if not SPHINX:
        if PRIMARY:
            _temp = '-p'
        elif SECONDARY:
            _temp = '-s'
        elif BOOTLOADER:
            _temp = '-b'
        run_str = '${PYTHON} ' + cmd + ' chksum_function ' + _temp
        color = 'CYAN'

def chksum_function(conf):
    """Waf function "chksum"
    Invoked by: "python foxBMS-tools/waf-1.8.12 chksum"

    Calculates the checksum of HEX_FILE generated by the build process.
    This process needs to be called after "build".
    Calls the checksum with tool stored in
    foxBMS-tools/checksum/chksum.py with the configuration stored in
    foxBMS-tools/checksum/chksum.ini.

    Reads the returned checksum from the piped shell output.
    Writes the checksum back to the following files:
     - foxbms.hex,
     - foxbms.elf and
     - foxbms_flashheader.bin.
    """
    # Calculate checksum and write it back into foxbms.hex file
    tgt = os.path.join('src', 'general', os.path.normpath(HEX_FILE))
    if PRIMARY:
        tgt = os.path.join('foxBMS-primary', tgt)
    if SECONDARY:
        tgt = os.path.join('foxBMS-secondary', tgt)

    tgt = os.path.join(OUT, tgt)
    tool = 'python'
    cmd = ' '.join([tool, CHKSUM_SCRIPT_REL_PATH, CHKSUM_INI_FILE_REL_PATH, \
        '-bd='+OUT, '-hf='+tgt])
    print COLOR_P + 'Subprocess: Calculating checksum from \
        foxbms.hex\n' + COLOR_C + cmd + COLOR_N + '\n'
    proc_chksum = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
        stderr=subprocess.PIPE, shell=True)
    rtn_code = proc_chksum.returncode
    std_out, std_err = proc_chksum.communicate()
    if rtn_code == 0 or rtn_code == None:
        print "Success: Process return code from tool %s code: %s" % (tool, str(rtn_code))
    else:
        print "Error: Process return code from tool %s code: %s" % (tool, str(rtn_code))
        sys.exit(1)
    checksum = (((std_out.split('* 32-bit SW-Chksum:     ')[1]).split('*'))[0].strip())
    print 'checksum output:\n----------------\n', std_out
    if std_err:
        print 'Err:', std_err, '\n'

    # write checksum into foxbms.elf file
    tgt = os.path.join('src', 'general', os.path.normpath(ELF_FILE))
    if PRIMARY:
        tgt = os.path.join('foxBMS-primary', tgt)
    if SECONDARY:
        tgt = os.path.join('foxBMS-secondary', tgt)
    tgt = os.path.join(OUT, tgt)

    tool = 'arm-none-eabi-gdb'
    cmd = '%s -q -se=%s --write -ex="set var ver_sw_validation.Checksum_u32 =%s" \
        -ex="print ver_sw_validation.Checksum_u32" -ex="quit"' % (tool, tgt, checksum)
    print COLOR_P + 'Subprocess: Writing into foxbms.elf\n' + COLOR_C + cmd + COLOR_N + '\n'
    print 'gdb output:\n-----------'
    proc_write_to_elf = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
        stderr=subprocess.PIPE, shell=True)
    rtn_code = proc_write_to_elf.returncode
    std_out, std_err = proc_write_to_elf.communicate()
    if rtn_code == 0 or rtn_code == None:
        print std_out
        print "Success: Process return code from tool %s code: %s" % (tool, str(rtn_code))
    else:
        print std_err
        print "Error: Process return code from tool %s code: %s" % (tool, str(rtn_code))
        #sys.exit(1)

    # write checksum into <APPNAME>_flashheader.bin file
    SRC = tgt
    tgt = os.path.join('src', 'general', os.path.normpath(BIN_FLASH_HEADER))
    if PRIMARY:
        tgt = os.path.join('foxBMS-primary', tgt)
    if SECONDARY:
        tgt = os.path.join('foxBMS-secondary', tgt)
    tgt = os.path.join(OUT, tgt)
    tool = 'arm-none-eabi-objcopy -v'
    cmd = ' '.join([tool, '-j', '.flashheader', '-O', 'binary', SRC, tgt])
    print '\n' + COLOR_P + 'Subprocess: Writing into \
        foxbms_flashheader.bin\n' + COLOR_C + cmd + COLOR_N + '\n'
    print 'objcopy output:\n---------------'
    proc_write_to_bin = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
        stderr=subprocess.PIPE, shell=True)
    rtn_code = proc_write_to_bin.returncode
    std_out, std_err = proc_write_to_bin.communicate()
    if rtn_code == 0 or rtn_code == None:
        print std_out
        print "Success: Process return code from tool %s code: %s" % (tool, str(rtn_code))
    else:
        print std_err
        print "Error: Process return code from tool %s code: %s" % (tool, str(rtn_code))
        sys.exit(1)

@TaskGen.feature('chksum')
@TaskGen.after('hexgen')
def add_chksum_task(self):
    """Adds the chksum task as waf feature to the build process. This
    step is applied after hex file generation.
    """
    try:
        link_task = self.link_task
    except AttributeError:
        return
    self.create_task('chksum', link_task.outputs[0])
# END CHKSUM TASK DESCRIPTION

def flash(bld):
    """Waf function "flash"
    Invoked by: "python foxBMS-tools/waf-1.8.12 flash"
    """
    subprocess.call("python tools/flashtool/stm32_loader.py -p COM10 -e -w -v -a 0x08000000 " + bld.path.abspath() + ("/build/src/general/foxbms_flash.bin"), shell=True)
    subprocess.call("python tools/flashtool/stm32_loader.py -p COM10 -w -v -a 0x080FFF00 " + bld.path.abspath() + ("/build/src/general/foxbms_flashheader.bin"), shell=True)


def styleguide(conf):
    """Waf function "styleguide"
    Invoked by: "python foxBMS-tools/waf-1.8.12 styleguide"

    Checks  *.c *.h files of the foxBMS project located in src/
    The output of the styleguide is put into build/styleguide.log
    """
    tool = 'python'
    cmd = ' '.join([tool, STYLEGUIDE_SCRIPT_REL_PATH])
    print '\n' + COLOR_P + 'Subprocess: Checking foxBMS codestlye \
        guidelines\n' + COLOR_C + cmd + COLOR_N + '\n'
    print 'styleguide output:\n---------------'
    p = subprocess.Popen(cmd, shell=True)
    p.wait()


def doxygen(bld):
    """Waf function "doxygen"
    Invoked by: "python foxBMS-tools/waf-1.8.12 doxygen"

    Builds the sphinx documentation defined in src/. For configuration
    (e.g., exlcuded files) see doc/doxygen/doxygen.conf.
    """
    if bld.env.DOXYGEN:
        _docbuilddir = os.path.normpath(bld.bldnode.abspath())
        if not os.path.exists(_docbuilddir):
            os.makedirs(_docbuilddir)
        if bld.options.primary:
            doxygenconf = os.path.join(DOXYGEN_DOC_DIR, 'doxygen-p.conf')
        if bld.options.secondary:
            doxygenconf = os.path.join(DOXYGEN_DOC_DIR, 'doxygen-s.conf')
        bld(features="doxygen", doxyfile=doxygenconf)


def sphinx(bld):
    """Waf function "sphinx"
    Invoked by: "python foxBMS-tools/waf-1.8.12 sphinx"

    Builds the sphinx documentation defined in doc/sphinx.
    For configuration see doc/sphinx/conf.py.
    """
    bld.recurse(SPHINX_DOC_DIR)

# START SIZE TASK DESCRIPTION
class size(Task.Task):
    """Waf function "size"
    Invoked by: "python foxBMS-tools/waf-1.8.12 size"

    Calculates the size of all libraries the foxbms.elf file.

    Gets all object files in the build directory (by file extension
    *.o) and the main foxbms.elf binary and processes the object with
    size in berkley format.
    """
    cmd = os.path.join(os.getcwd(), WAF_REL_PATH)
    _temp = ''
    if PRIMARY:
        _temp = '-p'
    elif SECONDARY:
        _temp = '-s'
    elif BOOTLOADER:
        _temp = '-b'
    else:
        _temp = ''
    run_str = '${PYTHON} ' + cmd + ' size_function ' + _temp
    color = 'CYAN'

def size_function(conf):
    """Runs a arm-none-eabi-size in Berkley format on all binaries.
    """
    objlist = ''
    for root, dirs, files in os.walk(out):
        for file in files:
            if file.endswith('.elf'):
                bpath = os.path.join(root, file)
                objlist += " " + os.path.join(bpath)
    for root, dirs, files in os.walk(os.path.join(out)):
        for file in files:
            if file.endswith('.a'):
                bpath = os.path.join(root, file)
                objlist += " " + os.path.join(bpath)
    for root, dirs, files in os.walk(os.path.join(out)):
        for file in files:
            if file.endswith('.o'):
                bpath = os.path.join(root, file)
                objlist += " " + os.path.join(bpath)
    size_log_file = os.path.join(out, 'size.log')
    cmd = 'arm-none-eabi-size --format=berkley ' + objlist + ' > ' + \
        size_log_file
    print COLOR_C + cmd + COLOR_N
    proc_get_size = subprocess.Popen(cmd, shell=True)
    proc_get_size.wait()
    with open(size_log_file, 'r') as f:
        print f.read()

    '''
    cmd = 'type ' + size_log_file
    proc_write_to_logfile = subprocess.Popen(cmd, shell=True)
    proc_write_to_logfile.wait()
    '''

@TaskGen.feature('size')
@TaskGen.after('hexgen')
def add_size_task(self):
    """Adds the size task as waf feature to the build process. This
    step is applied after hex file generation.
    """
    try:
        link_task = self.link_task
    except AttributeError:
        return
    self.create_task('size', link_task.outputs[0])
# END SIZE TASK DESCRIPTION

class strip(Task.Task):
    """Task generation: waf instructions for running
    arm-none-eabi-strip during release build
    """
    run_str = '${STRIP} ${SRC}'
    color = 'BLUE'


@TaskGen.feature('strip')
@TaskGen.after('apply_link')
def add_strip_task(self):
    """Adds the strip task as waf feature to the build process. This
    step is applied after binary link.
    """
    try:
        link_task = self.link_task
    except AttributeError:
        return
    self.create_task('strip', link_task.outputs[0])


class hexgen(Task.Task):
    """Task generation: waf instructions for generating the
    *.hex file
    """
    tgt = os.path.join('src', 'general', os.path.normpath(HEX_FILE))
    if PRIMARY:
        tgt = os.path.join('foxBMS-primary', tgt)
    if SECONDARY:
        tgt = os.path.join('foxBMS-secondary', tgt)
    run_str = '${hexgen} -O ihex ${SRC} '
    run_str += tgt
    color = 'CYAN'


@TaskGen.feature('hexgen')
@TaskGen.after('apply_link')
def add_hexgen_task(self):
    """Adds the hexgen task as waf feature to the build process. This
    step is applied after binary link. This is defined as the FIRST
    after build step in src/general/wscript.
    """
    try:
        link_task = self.link_task
    except AttributeError:
        return
    self.create_task('hexgen', link_task.outputs[0])

class binflashheadergen(Task.Task):
    """Task generation: converts .elf to .bin
    only flashheader
    """
    tgt = os.path.join('src', 'general', os.path.normpath(BIN_FLASH_HEADER))
    if PRIMARY:
        tgt = os.path.join('foxBMS-primary', tgt)
    if SECONDARY:
        tgt = os.path.join('foxBMS-secondary', tgt)
    run_str = '${hexgen} -j .flashheader -O binary ${SRC} '
    run_str += tgt
    color = 'RED'


class binflashgen(Task.Task):
    """Task generation: converts .elf to .bin
    only flash
    """
    tgt = os.path.join('src', 'general', os.path.normpath(BIN_FLASH))
    if PRIMARY:
        tgt = os.path.join('foxBMS-primary', tgt)
    if SECONDARY:
        tgt = os.path.join('foxBMS-secondary', tgt)
    run_str = '${hexgen} -R .bkp_ramsect -R .flashheader -O binary ${SRC} '
    run_str += tgt
    color = 'RED'


@TaskGen.feature('bingen')
@TaskGen.after('apply_link')
def add_bingen_task(self):
    """Adds the bingen task as waf feature to the build process. This
    step is applied after binary link.
    """
    try:
        link_task = self.link_task
    except AttributeError:
        return
    self.create_task('binflashgen', link_task.outputs[0])
    self.create_task('binflashheadergen', link_task.outputs[0])


import waflib.Tools.asm  # import before redefining
from waflib.TaskGen import extension


@extension('.S')
def asm_hook(self, node):
    """ Task generation: waf instructions for startup script compile
    routine
    """
    name = 'Sasm'
    out = node.change_ext('.o')
    task = self.create_task(name, node, out)
    try:
        self.compiled_tasks.append(task)
    except AttributeError:
        self.compiled_tasks = [task]
    return task


class Sasm(Task.Task):
    """ Task generation: waf instructions for startup script compile
    routine
    """
    color = 'BLUE'
    run_str = '${CC} ${CFLAGS} ${CPPPATH_ST:INCPATHS} -DHSE_VALUE=8000000 -MMD -MP -MT${TGT} -c -x assembler -o ${TGT} ${SRC}'

# vim: set ft=python :
