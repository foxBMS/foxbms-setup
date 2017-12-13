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
import re
import datetime
import json
import platform
import subprocess
import ConfigParser
import logging

from waflib import Logs, Utils, Context, Options
from waflib import Task, TaskGen
from waflib.Tools.compiler_c import c_compiler

__version__ = 0.1
__date__ = '2017-11-29'
__updated__ = '2017-11-29'

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
    sys.exit(1)
elif (len(sys.argv) > 3) and 'sphinx' in sys.argv and 'clean' not in sys.argv:
    print r"Build sphinx documentation by \"python tools\waf-1.9.13 configure sphinx\""
    sys.exit(1)
else:
    if ('-p' in sys.argv and '-s' in sys.argv) or \
       ('-p' in sys.argv and '-b' in sys.argv) or \
       ('-s' in sys.argv and '-b' in sys.argv):
        print "Specify one mcu (option: -p, -s, -b), not a \
            combination of these parameters."
        sys.exit(1)
    if ('chksum_function' in sys.argv) and not (
            '-p' in sys.argv or '-s' in sys.argv or '-b' in sys.argv):
        print "Specify a project to run the chksum tool on"
        sys.exit(1)
    if ('size_function' in sys.argv) and not (
            '-p' in sys.argv or '-s' in sys.argv or '-b' in sys.argv):
        print "Specify a project to run the size tool on"
        sys.exit(1)
    if ('doxygen' in sys.argv) and not (
            '-p' in sys.argv or '-s' in sys.argv or '-b' in sys.argv):
        print "Specify a project to generate the Doxygen \
            documentation for"
        sys.exit(1)
    # all wrong input combinations should now be handled. The task
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
        print "Specify the mcu (option: -p, -s) to build the sources \
            or Doxygen documentation"
        sys.exit(1)

# The top output directory is always './build/' relative to the directory
# the foxBMS-setup was configured in.
# Set sub build directory and build option as now the project goal
# is defined
TOP_BUILD_DIR = 'build'
if PRIMARY:
    BLD_OPTION = '-p'
    SUB_BUILD_DIR = 'primary'
    APPNAME = "foxbms"
    VERSION = "1.0"
    CHKSUM_INI_FILE_REL_PATH = os.path.join(
        "tools", "checksum", "chksum.ini")
elif SECONDARY:
    BLD_OPTION = '-s'
    SUB_BUILD_DIR = 'secondary'
    APPNAME = "foxbms"
    VERSION = "1.0"
    CHKSUM_INI_FILE_REL_PATH = os.path.join(
        "tools", "checksum", "chksum.ini")
elif BOOTLOADER:
    BLD_OPTION = '-b'
    SUB_BUILD_DIR = 'bootloader'
    APPNAME = "bootloader"
    VERSION = "V0.2.0"
    CHKSUM_INI_FILE_REL_PATH = os.path.join(
        "tools", "checksum", "chksum-bootloader.ini")
elif SPHINX:
    BLD_OPTION = 'sphinx'
    SUB_BUILD_DIR = 'sphinx'
    APPNAME = "foxbms"
    VERSION = "1.0"
    CHKSUM_INI_FILE_REL_PATH = ""

out = os.path.join(TOP_BUILD_DIR, SUB_BUILD_DIR)
OUT = out  # !DO NOT DELETE! - NEEDED FOR CHKSUM TASK

VENDOR = "Fraunhofer IISB"

CONFIG_HEADER = APPNAME + 'config.h'
ELF_FILE = os.path.join(APPNAME + '.elf')
HEX_FILE = os.path.join(APPNAME + '.hex')
BIN_FLASH = os.path.join(APPNAME + '_flash.bin')
BIN_FLASH_HEADER = os.path.join(APPNAME + '_flashheader.bin')

DOC_TOOL_DIR = os.path.join("tools", "waftools")

SPHINX_DOC_DIR = os.path.join("documentation", "doc", "sphinx")
DOXYGEN_DOC_DIR = os.path.join("documentation", "doc", "doxygen")


def options(opt):
    opt.load('compiler_c')
    opt.load(['doxygen', 'sphinx_build'], tooldir=DOC_TOOL_DIR)
    opt.add_option('-c', '--config', action='store', default=None,
                   help='file containing additional configuration variables',
                   dest='configfile')
    opt.add_option('-t', '--target', action='store', default='debug',
                   help='build target: debug (default)/release', dest='target')
    opt.add_option('-p', '--primary', action='store_true',
                   default=False, help='build target: debug (default)/release',
                   dest='primary')
    opt.add_option('-s', '--secondary', action='store_true',
                   default=False, help='build target: debug (default)/release',
                   dest='secondary')
    opt.add_option('-b', '--bootloader', action='store_true',
                   default=False, help='build target: debug (default)/release',
                   dest='bootloader')


def load_config_file():
    _fname = Options.options.configfile
    if _fname is None:
        return
    json.load(_fname)


def configure(conf):
    load_config_file()
    # prefix for all gcc related tools
    pref = 'arm-none-eabi'

    if sys.platform.startswith('win'):

        conf.env.CC = pref + '-gcc.exe'
        conf.env.AR = pref + '-ar.exe'
        conf.env.LINK_CC = pref + '-g++.exe'
        conf.find_program(pref + '-strip', var='STRIP')
        conf.find_program(pref + '-objcopy', var='OBJCOPY')
        conf.find_program(pref + '-size', var='SIZE')
        conf.find_program(pref + '-gdb', var='GDB')
        conf.find_program('python', var='PYTHON')
        conf.find_program('dot', var='dot')
    else:
        conf.env.CC = pref + '-gcc'
        conf.env.AR = pref + '-ar'
        conf.env.LINK_CC = pref + '-g++'
        conf.find_program(pref + '-strip', var='STRIP')
        conf.find_program(pref + '-objcopy', var='OBJCOPY')
        conf.find_program(pref + '-size', var='SIZE')
        conf.find_program(pref + '-gdb', var='GDB')
        conf.find_program('python', var='PYTHON')
        conf.find_program('dot', var='dot')
    conf.env.CFLAGS = '-mcpu=cortex-m4 -mthumb -mlittle-endian -mfloat-abi=softfp -mfpu=fpv4-sp-d16 -fmessage-length=0 -fno-common -fsigned-char -ffunction-sections -fdata-sections -ffreestanding -fno-move-loop-invariants -Wall -std=c99'.split(
        ' ')
    # change for STM32F7 CPU
    # conf.env.CFLAGS = '-mcpu=cortex-m7 -mthumb -mlittle-endian -mfloat-abi=hard -mfpu=fpv5-sp-d16 -fmessage-length=0 -fno-common -fsigned-char -ffunction-sections -fdata-sections -ffreestanding -fno-move-loop-invariants -Wall -std=c99'.split(' ')
    conf.env.CFLAGS += str('-DBUILD_VERSION=\"' +
                           str(VERSION) + '\"').split(' ')
    conf.env.CFLAGS += str('-DBUILD_APPNAME=\"' +
                           str(APPNAME) + '\"').split(' ')
    conf.env.CFLAGS += '-DDEBUG -DUSE_FULL_ASSERT -DTRACE -DOS_USE_TRACE_ITM -DUSE_HAL_DRIVER -DHSE_VALUE=8000000'.split(
        ' ')
    for key in c_compiler:  # force only using gcc
        c_compiler[key] = ['gcc']
        

    # get HAL version based on compiler define
    try:
        stm32f_version = filter(lambda x: '-mcpu' in x, conf.env.CFLAGS)[0]
    except IndexError as e:
        print "Error: %s " % (e)
        print "Could not find \"-mcpu\" in compiler flags"
        sys.exit(1)
    cdef, cpu = stm32f_version.split('=')
    if cpu == "cortex-m4":
        conf.env.CPU_MAJOR = 'STM32F4xx'
    elif cpu == "cortex-m7":
        conf.env.CPU_MAJOR = 'STM32F7xx'
    else:
        print "\"%s\" is not a valid cpu version" % (cpu)
        sys.exit(1)

    # get floating point version based on compiler define and check
    # if compatible with cpu
    try:
        floating_point_unit_version = filter(lambda x: '-mfpu' in x, conf.env.CFLAGS)[0]
    except IndexError as e:
        print "Error: %s " % (e)
        print "Could not find \"-mcpu\" in compiler flags"
        sys.exit(1)
    cdef, floating_point_version = floating_point_unit_version.split('=')
    if cpu == "cortex-m4":
        if floating_point_version != 'fpv4-sp-d16':
            print "Error: floating point unit flag not compatible with cpu"
            sys.exit(1)
    if cpu == 'cortex-m7':
        if floating_point_version != 'fpv5-sp-d16':
            print "Error: floating point unit flag not compatible with cpu"
            sys.exit(1)
    # check done
    conf.load('compiler_c')
    conf.load(['doxygen', 'sphinx_build'])
    conf.find_program('git', mandatory=False)

    conf.env.version = VERSION
    conf.env.appname = APPNAME
    conf.env.vendor = VENDOR
    
    if conf.env.CPU_MAJOR == "STM32F4xx":
        conf.define('STM32F429xx', 1)
        LDSCRIPT_FILENAME = "STM32F429ZIT6_FLASH.ld"
    elif conf.env.CPU_MAJOR == "STM32F7xx":
        conf.define('STM32F767xx', 1)
        LDSCRIPT_FILENAME = "STM32F767IGTx_EXTRAM.ld"
    if PRIMARY:
        LDSCRIPT = os.path.join(
            'embedded-software',
            "mcu-primary",
            "src",
            LDSCRIPT_FILENAME)
    elif SECONDARY:
        LDSCRIPT = os.path.join(
            'embedded-software',
            "mcu-secondary",
            "src",
            LDSCRIPT_FILENAME)
    elif BOOTLOADER:
        LDSCRIPT = os.path.join(
            'embedded-software',
            "mcu-bootloader",
            "src",
            LDSCRIPT_FILENAME)
    else:
        LDSCRIPT = ""

    conf.env.ldscript = os.path.join(conf.srcnode.abspath(), LDSCRIPT)
    try:
        conf.env.buildno = conf.cmd_and_log(
            conf.env.GIT[0] + ' rev-parse --short HEAD').strip()
    except:
        conf.env.buildno = 'none'
    utcnow = datetime.datetime.utcnow()
    utcnow = ''.join(utcnow.isoformat('-').split('.')
                     [0].replace(':', '-').split('-'))
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
    env_debug.basename = conf.env.appname + '-' + conf.env.version + \
        '-' + conf.env.buildno + '-' + conf.env.timestamp + '-debug'
    env_debug.PREFIX = conf.env.appname + '-' + conf.env.version + \
        '-' + conf.env.buildno + '-' + conf.env.timestamp

    # configuration for release
    conf.setenv('release', env_release)
    conf.env.CFLAGS += ['-O2']
    env_release.basename = conf.env.appname + '-' + conf.env.version + \
        '-' + conf.env.buildno + '-' + conf.env.timestamp + '-release'
    env_release.PREFIX = conf.env.appname + '-' + conf.env.version + \
        '-' + conf.env.buildno + '-' + conf.env.timestamp
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


def build(bld):
    import sys
    import logging
    from waflib import Logs
    log_file_prefix = 'build'
    log_file_extentsion = '.log'
    log_file = 'build.log'
    src_file_build = False
    # Sets the source directory of the project and enables the build logging
    # routine
    bld.env.__sw_dir = os.path.normpath('embedded-software')
    bld.env.__bld_common = os.path.normpath('mcu-common')
    bld.env.__inc_FreeRTOS = ' '.join([
        os.path.join(bld.top_dir, bld.env.__sw_dir, 'mcu-freertos', 'Source'),
        os.path.join(bld.top_dir, bld.env.__sw_dir, 'mcu-freertos', 'Source', 'CMSIS_RTOS'),
        os.path.join(bld.top_dir, bld.env.__sw_dir, 'mcu-freertos', 'Source', 'include'),
        os.path.join(bld.top_dir, bld.env.__sw_dir, 'mcu-freertos', 'Source', 'portable', 'GCC', 'ARM_CM4F'),
        ])
    bld.env.__inc_hal = ' '.join([
        os.path.join(bld.top_dir, bld.env.__sw_dir, 'mcu-hal', 'CMSIS', 'Device', 'ST', bld.env.CPU_MAJOR, 'Include'),
        os.path.join(bld.top_dir, bld.env.__sw_dir, 'mcu-hal', 'CMSIS', 'Include'),
        os.path.join(bld.top_dir, bld.env.__sw_dir, 'mcu-hal', bld.env.CPU_MAJOR + '_HAL_Driver', 'Inc'),
        os.path.join(bld.top_dir, bld.env.__sw_dir, 'mcu-hal', bld.env.CPU_MAJOR + '_HAL_Driver', 'Inc', 'Legacy'),
        ])
    if bld.options.primary:
        __src_dir = os.path.normpath('mcu-primary')
        bld.env.__bld_project = __src_dir
        log_file_name = 'primary'
    elif bld.options.secondary:
        __src_dir = os.path.normpath('mcu-secondary')
        bld.env.__bld_project = __src_dir
        log_file_name = 'secondary'
    elif bld.options.bootloader:
        __src_dir = os.path.normpath('mcu-bootloader')
        bld.env.__bld_project = __src_dir
        log_file_name = 'bootloader'
    else:
        logging.error('No valid target specified')
        sys.exit(1)

    log_file = log_file_prefix + '_' + log_file_name + log_file_extentsion
    log_file = os.path.join(TOP_BUILD_DIR, log_file)
    bld.logger = Logs.make_logger(log_file, out)
    hdlr = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    hdlr.setFormatter(formatter)
    bld.logger.addHandler(hdlr)
    bld.recurse(os.path.join(bld.env.__sw_dir, __src_dir))
    bld.add_post_fun(size)

def size(bld):
    print 'Running: \'arm-none-eabi-size --format=berkley\' on all binaries.'
    objlist = []
    for _ext in ['.elf', '.a', '.o']:
        for root, dirs, files in os.walk(bld.out_dir):
            for file in files:
                if file.endswith(_ext):
                    bpath = os.path.join(root, file)
                    objlist.append(os.path.join(bpath))
    _out = '\n'
    for _file in objlist:
        cmd = 'arm-none-eabi-size --format=berkley ' + _file
        proc_get_size = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
        _std_out, _std_err = proc_get_size.communicate()
        rtn_code = proc_get_size.returncode
        _out += '{}\n'.format(cmd)
        if _std_out:
            _out += '\n {}'.format(_std_out)
        if _std_err:
            _out += '\n {}'.format(_std_err)
    size_log_file = os.path.join(bld.out_dir, 'size.log')
    with open(size_log_file, 'w') as f:
        f.write(_out)


def dist(conf):
    conf.base_name = 'foxbms'
    conf.algo = 'tar.gz'
    conf.excl = ' Packages workspace **/.waf-1* **/*~ **/*.pyc **/*.swp **/.lock-w* **/env.txt **/log.txt **/.git **/build **/*.tar.gz **/.gitignore **/tools/waf-1.9.13-*'


class chksum(Task.Task):
    chksum_script = os.path.abspath(os.path.join('tools', 'checksum', 'chksum.py'))
    writeback_script = os.path.abspath(os.path.join('tools', 'checksum', 'writeback.py'))
    mcu_config_file = os.path.abspath(CHKSUM_INI_FILE_REL_PATH)
    cs_out_dir = 'chk5um'
    cs_out_file = os.path.join(cs_out_dir, 'chksum.log')
    always_run = True
    calculate_checksum = 'python ' + chksum_script + ' ' + mcu_config_file + ' -bd=' + cs_out_dir + ' -hf=${SRC[0].relpath().replace(\".elf\",\".hex\")}'
    writeback_command = '${PYTHON} ' + writeback_script + ' --conffile ' +  cs_out_file + ' --elffile ${SRC[0].relpath()} --tool ${GDB}'
    run_str = (calculate_checksum, writeback_command)
    color = 'RED'

@TaskGen.feature('chksum')
@TaskGen.before('bingen')
@TaskGen.after('apply_link', 'hexgen')
def add_chksum_task(self):
    try:
        link_task = self.link_task
    except AttributeError:
        return
    self.create_task('chksum', src=link_task.outputs[0])


def doxygen(bld):
    import sys
    import logging
    from waflib import Logs
    if bld.env.DOXYGEN:
        _docbuilddir = os.path.normpath(bld.bldnode.abspath())
        if not os.path.exists(_docbuilddir):
            os.makedirs(_docbuilddir)
        if bld.options.primary:
            doxygenconf = os.path.join(DOXYGEN_DOC_DIR, 'doxygen-p.conf')
            d = "primary"
        elif bld.options.secondary:
            doxygenconf = os.path.join(DOXYGEN_DOC_DIR, 'doxygen-s.conf')
            d = "secondary"
        elif bld.options.bootloader:
            doxygenconf = os.path.join(DOXYGEN_DOC_DIR, 'doxygen-bootloader.conf')
            d = "bootloader"
        log_file_prefix = 'doc'
        log_file_extentsion = '.log'
        log_file = 'build.log'
        log_file_name = 'doxygen_' + d
        log_file = log_file_prefix + '_' + log_file_name + log_file_extentsion
        log_file = os.path.join(TOP_BUILD_DIR, log_file)
        bld.logger = Logs.make_logger(log_file, out)
        hdlr = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(message)s')
        hdlr.setFormatter(formatter)
        bld.logger.addHandler(hdlr)
        bld(features="doxygen", doxyfile=doxygenconf)


def sphinx(bld):
    import sys
    import logging
    from waflib import Logs
    log_file_prefix = 'doc'
    log_file_extentsion = '.log'
    log_file = 'build.log'
    log_file_name = 'sphinx'
    log_file = log_file_prefix + '_' + log_file_name + log_file_extentsion
    log_file = os.path.join(TOP_BUILD_DIR, log_file)
    bld.logger = Logs.make_logger(log_file, out)
    hdlr = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    hdlr.setFormatter(formatter)
    bld.logger.addHandler(hdlr)
    bld.recurse(SPHINX_DOC_DIR)


class strip(Task.Task):
    run_str = '${STRIP} ${SRC}'
    color = 'BLUE'


@TaskGen.feature('strip')
@TaskGen.after('apply_link')
def add_strip_task(self):
    try:
        link_task = self.link_task
    except AttributeError:
        return
    self.create_task('strip', link_task.outputs[0])


class hexgen(Task.Task):
    always_run = True
    run_str = '${OBJCOPY} -O ihex ${SRC} ${TGT}'
    color = 'CYAN'


@TaskGen.feature('hexgen')
@TaskGen.after('apply_link')
def add_hexgen_task(self):
    try:
        link_task = self.link_task
    except AttributeError:
        return
    self.create_task('hexgen', src=link_task.outputs[0], tgt=link_task.outputs[0].change_ext('.hex'))


class binflashheadergen(Task.Task):
    always_run = True
    after = ['chksum']
    run_str = '${OBJCOPY} -j .flashheader -O binary ${SRC} ${TGT}'
    color = 'RED'


class binflashgen(Task.Task):
    always_run = True
    after = ['chksum']
    run_str = '${OBJCOPY} -R .bkp_ramsect -R .flashheader -O binary ${SRC} ${TGT}'
    color = 'RED'


@TaskGen.feature('bingen')
@TaskGen.after('apply_link')
@TaskGen.after('chksum')
def add_bingen_task(self):
    try:
        link_task = self.link_task
    except AttributeError:
        return
    self.create_task('binflashgen', src=link_task.outputs[0], tgt=link_task.outputs[0].change_ext('_flash.bin'))
    self.create_task('binflashheadergen', src=link_task.outputs[0], tgt=link_task.outputs[0].change_ext('_flashheader.bin'))


import waflib.Tools.asm  # import before redefining
from waflib.TaskGen import extension


@extension('.S')
def asm_hook(self, node):
    name = 'Sasm'
    out = node.change_ext('.o')
    task = self.create_task(name, node, out)
    try:
        self.compiled_tasks.append(task)
    except AttributeError:
        self.compiled_tasks = [task]
    return task


class Sasm(Task.Task):
    color = 'BLUE'
    run_str = '${CC} ${CFLAGS} ${CPPPATH_ST:INCPATHS} -DHSE_VALUE=8000000 -MMD -MP -MT${TGT} -c -x assembler -o ${TGT} ${SRC}'


def check_subprocess(prg, rtn_code, std_out=None, std_err=None):
    if rtn_code == 0:
        if std_out:
            print std_out
        print 'Success: Process return code from program {} code: {}'.format(prg, str(rtn_code))
    else:
        if std_err:
            print std_err
        print 'Error: Process return code from program {} code: {}'.format(prg, str(rtn_code))
        sys.exit(1)

# vim: set ft=python :
