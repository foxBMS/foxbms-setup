# @copyright &copy; 2010 - 2018, Fraunhofer-Gesellschaft zur Foerderung der
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


import os
import errno
import sys
import datetime
import platform
import subprocess
import logging

from waflib import Logs, Utils, Context, Options, Scripting
from waflib import Task, TaskGen
from waflib.Tools.compiler_c import c_compiler

__version__ = '0.2'
__date__ = '2017-11-29'
__updated__ = '2018-02-07'

out = 'build'
variants = ['primary', 'secondary', 'bootloader']
from waflib.Build import BuildContext, CleanContext, ListContext, StepContext
for x in variants:
    for y in (
        BuildContext,
        CleanContext,
        ListContext,
        StepContext
        ):
        name = y.__name__.replace('Context','').lower()
        class tmp(y):
            if name == 'build':
                __doc__ = '''executes the {} of {}'''.format(name, x)
            elif name == 'clean':
                __doc__ = '''cleans the project {}'''.format(x)
            elif name == 'list':
                __doc__ = '''lists the targets to execute for {}'''.format(x)
            elif name == 'step':
                __doc__ = '''executes tasks in a step-by-step fashion, for \
debugging of {}'''.format(x)
            cmd = name + '_' + x
            variant = x

    dox = 'doxygen'
    class tmp(BuildContext):
        __doc__ = '''creates the {} documentation of {}'''.format(dox, x)
        cmd = dox + '_' + x
        fun = dox
        variant = x

# for future compatibility
VENDOR = 'Fraunhofer IISB'
APPNAME_PREFIX = 'foxbms'
VERSION_PRIMARY = '1.0.0'
VERSION_SECONDARY = '1.0.0'
VERSION_BOOTLOADER = '0.2.0'
VERSION_BOOTLOADER_MAJOR = VERSION_BOOTLOADER.split('.')[0]
VERSION_BOOTLOADER_MINOR = VERSION_BOOTLOADER.split('.')[1]
VERSION_BOOTLOADER_BUGFIX = VERSION_BOOTLOADER.split('.')[2]

def options(opt):
    opt.load('compiler_c')
    opt.load(['doxygen', 'sphinx_build'], tooldir=os.path.join('tools',
             'waftools'))
    opt.add_option('-t', '--target', action='store', default='debug',
                   help='build target: debug (default)/release', dest='target')

    for k in (
        '--keep',
        '--targets',
        '--out',
        '--top',
        '--prefix',
        '--destdir',
        '--bindir',
        '--libdir',
        '--msvc_version',
        '--msvc_targets',
        '--no-msvc-lazy',
        '--zones',
        '--force',
        '--check-c-compiler'):
        option = opt.parser.get_option(k)
        if option:
            opt.parser.remove_option(k)

    mctx = waflib.Context.classes
    mctx.remove(waflib.Build.InstallContext)
    mctx.remove(waflib.Build.UninstallContext)


def configure(conf):
    # prefix for all gcc related tools
    pref = 'arm-none-eabi-'
    if sys.platform.startswith('win'):
        conf.env.CC = pref + 'gcc.exe'
        conf.env.AR = pref + 'ar.exe'
        conf.env.LINK_CC = pref + 'g++.exe'
    else:
        conf.env.CC = pref + 'gcc'
        conf.env.AR = pref + 'ar'
        conf.env.LINK_CC = pref + 'g++'
    for k in 'cpp ranlib as strip objcopy objdump size gdb'.split():
        conf.find_program(pref + k, var=k.upper(), mandatory=True)
    conf.find_program('python', var='PYTHON', mandatory=True)
    conf.find_program('dot', var='dot', mandatory=True)
    conf.find_program('git', mandatory=False)

    conf.env.CFLAGS = '-mcpu=cortex-m4 -mthumb -mlittle-endian -mfloat-abi=softfp -mfpu=fpv4-sp-d16 -fmessage-length=0 -fno-common -fsigned-char -ffunction-sections -fdata-sections -ffreestanding -fno-move-loop-invariants -Wall -std=c99'.split(
        ' ')
    # change for STM32F7 CPU
    # conf.env.CFLAGS = '-mcpu=cortex-m7 -mthumb -mlittle-endian -mfloat-abi=hard -mfpu=fpv5-sp-d16 -fmessage-length=0 -fno-common -fsigned-char -ffunction-sections -fdata-sections -ffreestanding -fno-move-loop-invariants -Wall -std=c99'.split(' ')
    conf.env.CFLAGS += '-DDEBUG -DUSE_FULL_ASSERT -DTRACE -DOS_USE_TRACE_ITM -DUSE_HAL_DRIVER -DHSE_VALUE=8000000'.split(' ')
    for key in c_compiler:  # force only using gcc
        c_compiler[key] = ['gcc']

    # get HAL version and floating point version based on compiler define and
    # check if cpu and floating point version  are fitting together
    cpu = None
    floating_point_version = None
    for _cflag in conf.env.CFLAGS:
        if 'mcpu' in _cflag:
            cdef, cpu = _cflag.split('=')
        if 'mfpu' in _cflag:
            cdef, floating_point_version = _cflag.split('=')

    if not cpu:
        logging.error('Error: Could not find \'-mcpu\' in compiler flags')
        sys.exit(1)
    if not floating_point_version:
        logging.error('Error: Floating point version not specified')
        sys.exit(1)

    if cpu == 'cortex-m4':
        conf.env.CPU_MAJOR = 'STM32F4xx'
        if floating_point_version != 'fpv4-sp-d16':
            logging.error('Error: floating point unit flag not compatible with cpu')
            sys.exit(1)
    elif cpu == 'cortex-m7':
        conf.env.CPU_MAJOR = 'STM32F7xx'
        if floating_point_version != 'fpv5-sp-d16':
            logging.error('Error: floating point unit flag not compatible with cpu')
            sys.exit(1)
    else:
        logging.error('\'%s\' is not a valid cpu version', cpu)
        sys.exit(1)

    # check done
    conf.load('compiler_c')
    conf.load(['doxygen', 'sphinx_build'])

    # checksum
    conf.env.chksum_script = os.path.abspath(os.path.join('tools', 'checksum', 'chksum.py'))
    conf.env.writeback_script = os.path.abspath(os.path.join('tools', 'checksum', 'writeback.py'))
    conf.env.cs_out_dir = os.path.normpath('chk5um')
    conf.env.cs_out_file = os.path.join('chk5um', 'chksum.log')

    conf.env.version_primary = VERSION_PRIMARY
    conf.env.version_secondary = VERSION_SECONDARY
    conf.env.version_bootloader = VERSION_BOOTLOADER
    conf.env.appname_prefix = APPNAME_PREFIX
    conf.env.appname = APPNAME_PREFIX # backwards compatibility
    conf.env.vendor = VENDOR

    conf.env.linkflags = ['-mthumb', '-mlittle-endian', '-fsigned-char',
        '-ffreestanding', '-fno-move-loop-invariants', '-fmessage-length=0',
        '-fsigned-char', '-std=c99', '-ffunction-sections', '-fdata-sections',
        '-Wall']
    if conf.env.CPU_MAJOR == 'STM32F4xx':
        conf.env.linkflags.extend(['-mcpu=cortex-m4', '-mfpu=fpv4-sp-d16',
            '-mfloat-abi=softfp'])
        conf.env.ldscript_filename = 'STM32F429ZIT6_FLASH.ld'
        conf.env.startupscript_filename = 'startup_stm32f429xx.S'
    elif conf.env.CPU_MAJOR == 'STM32F7xx':
        conf.env.linkflags.extend(['-mcpu=cortex-m7', '-mfpu=fpv5-sp-d16',
            '-mfloat-abi=hard'])
        conf.env.ldscript_filename = 'STM32F767IGTx_EXTRAM.ld'
        conf.env.startupscript_filename = 'startup_stm32f767xx.S'

    try:
        conf.env.buildno = conf.cmd_and_log(
            conf.env.GIT[0] + ' rev-parse --short HEAD').strip()
    except:
        conf.env.buildno = 'none'
    utcnow = datetime.datetime.utcnow()
    utcnow = ''.join(utcnow.isoformat('-').split('.')
                     [0].replace(':', '-').split('-'))
    conf.env.timestamp = utcnow

    # for future compatibility
    conf.define('BUILD_APPNAME_PREFIX', APPNAME_PREFIX)
    for x in variants:
        conf.define(('BUILD_APPNAME_{}'.format(x)).upper(),
                    '{}_{}'.format(APPNAME_PREFIX, x)[:14],
                    comment='Define is trimmed to max. 14 characters'.format(x))
    conf.define('BUILD_VERSION_PRIMARY', VERSION_PRIMARY)
    conf.define('BUILD_VERSION_SECONDARY', VERSION_SECONDARY)
    conf.define('BUILD_VERSION_BOOLOADER', VERSION_BOOTLOADER)
    conf.define('BUILD_VERSION_BOOLOADER_MAJOR',
                VERSION_BOOTLOADER_MAJOR,
                quote=False)
    conf.define('BUILD_VERSION_BOOLOADER_MINOR',
                VERSION_BOOTLOADER_MINOR,
                quote=False)
    conf.define('BUILD_VERSION_BOOLOADER_BUGFIX',
                VERSION_BOOTLOADER_BUGFIX,
                quote=False)

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

    # configuration for release
    conf.setenv('release', env_release)
    conf.env.CFLAGS += ['-O2']

    if conf.options.target == 'release':
        conf.setenv('', env_release)
    else:
        conf.setenv('', env_debug)

    env_release.store(os.path.join(out, 'env-store.log'))

    config_dir = 'config'
    try:
        os.makedirs(os.path.join(out, config_dir))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    header_file_name = conf.env.appname_prefix + 'config.h'
    header_file_path = os.path.join(config_dir, header_file_name),
    def_guard = header_file_name.upper().replace('.H', '_H_')
    conf.write_config_header(header_file_path, guard=def_guard)
    print('---')
    print('Vendor:              {}'.format(conf.env.vendor))
    print('Appname prefix:      {}'.format(conf.env.appname_prefix))
    print('Applications:        {}'.format(', '.join(variants)))
    print('Version primary:     {}'.format(conf.env.version_primary))
    print('Version secondary:   {}'.format(conf.env.version_secondary))
    print('Version bootloader:  {}'.format(conf.env.version_bootloader))
    print('---')
    print('Config header:       {}'.format(conf.env.cfg_files[0]))
    print('---')
    try:
        print('LINKFLAGS:      ' + conf.env.linkflags[0])
        for i, flag in enumerate(conf.env.linkflags):
            if i != 0:
                print('                ' + flag)
    except BaseException as e:
        print e
        print('\nno LINKFLAGS specified')
    try:
        print('CFLAGS:         ' + conf.env.CFLAGS[0])
        for i, flag in enumerate(conf.env.CFLAGS):
            if i != 0:
                print('                ' + flag)
    except:
        print('\nno CFLAGS specified')
    print('---')


def build(bld):
    import sys
    import logging
    from waflib import Logs
    if not bld.variant:
        bld.fatal('A {} variant must be specified, run \'python {} --help\'\
'.format(bld.cmd, sys.argv[0]))

    bld.env.__sw_dir = os.path.normpath('embedded-software')

    if bld.variant == 'primary':
        src_dir = os.path.normpath('mcu-primary')
        ldscript = os.path.join(bld.env.__sw_dir, src_dir, 'src', bld.env.ldscript_filename)
        chksum_ini_file_rel_path = os.path.join('tools', 'checksum', 'chksum.ini')
    elif bld.variant == 'secondary':
        src_dir = os.path.normpath('mcu-secondary')
        ldscript = os.path.join(bld.env.__sw_dir, src_dir, 'src', bld.env.ldscript_filename)
        chksum_ini_file_rel_path = os.path.join('tools', 'checksum', 'chksum.ini')
    elif bld.variant == 'bootloader':
        src_dir = os.path.normpath('mcu-bootloader')
        ldscript = os.path.join(bld.env.__sw_dir, src_dir, 'src', bld.env.ldscript_filename)
        chksum_ini_file_rel_path = os.path.join('tools', 'checksum', 'chksum-bootloader.ini')
    else:
        logging.error('Something went wrong')

    bld.env.ldscript = os.path.join(bld.srcnode.abspath(), ldscript)
    bld.env.stscript = bld.env.startupscript_filename
    bld.env.chksum_ini_file_rel_path = chksum_ini_file_rel_path
    bld.env.chksum_ini_file_abs_path = os.path.abspath(chksum_ini_file_rel_path)
    bld.env.__bld_project = src_dir

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

    log_file = os.path.join(out, 'build_' + bld.variant + '.log')
    bld.logger = Logs.make_logger(log_file, out)
    hdlr = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    hdlr.setFormatter(formatter)
    bld.logger.addHandler(hdlr)
    t = os.path.dirname(bld.env.cfg_files[0])
    bld.env.append_value('INCLUDES', t)
    bld.recurse(os.path.join(bld.env.__sw_dir, src_dir))
    bld.add_post_fun(size)

def size(bld):
    #print "bld.bldnode", bld.bldnode
    #print "bld.out_dir", bld.out_dir
    base_cmd = '{} --format=berkley'.format(bld.env.SIZE[0])
    print('Running: \'{}\' on all binaries.'.format(base_cmd))
    objlist = []
    for _ext in ['.elf', '.a', '.o']:
        for root, dirs, files in os.walk(bld.bldnode.abspath()):
            for file in files:
                if file.endswith(_ext):
                    bpath = os.path.join(root, file)
                    objlist.append(os.path.join(bpath))
    _out = '\n'
    for _file in objlist:
        cmd = '{} {}'.format(base_cmd, _file)
        proc_get_size = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
        _std_out, _std_err = proc_get_size.communicate()
        rtn_code = proc_get_size.returncode
        _out += '{}\n'.format(cmd)
        if _std_out:
            _out += '\n{}'.format(_std_out)
        if _std_err:
            _out += '\n{}'.format(_std_err)
    size_log_file = os.path.join(bld.bldnode.abspath(),
                                'size_' + bld.variant + '.log')
    with open(size_log_file, 'w') as f:
        f.write(_out)

def dist(conf):
    conf.base_name = APPNAME_PREFIX
    conf.algo = 'tar.gz'
    conf.excl = out
    conf.excl += ' .ws **/tools/waf-*.*.**-* .lock-*'
    conf.excl += ' **/.git **/.gitignore **/.gitattributes '
    conf.excl += ' **/*.tar.gz **/*.pyc '

def distcheck_cmd(self):
    cfg = []
    if Options.options.distcheck_args:
        cfg=shlex.split(Options.options.distcheck_args)
    else:
        cfg = [x for x in sys.argv if x.startswith('-')]
    cmd = [sys.executable, sys.argv[0], 'configure', 'build_primary', 'build_secondary', 'doxygen_primary', 'doxygen_secondary', 'sphinx'] + cfg
    return cmd

def check_cmd(self):
    import tarfile
    try:
        t = tarfile.open(self.get_arch_name())
        for x in t:
            t.extract(x)
    finally:
        t.close()
    cmd = self.make_distcheck_cmd()
    ret = Utils.subprocess.Popen(cmd,cwd=self.get_base_name()).wait()
    if ret:
        raise Errors.WafError('distcheck failed with code %r'%ret)

def distcheck(conf):
    """Creates tar.bz form the source directory and tries to run a build"""
    from waflib import Scripting
    Scripting.DistCheck.make_distcheck_cmd = distcheck_cmd
    Scripting.DistCheck.check = check_cmd
    conf.base_name = APPNAME_PREFIX
    conf.excl = out
    conf.excl += ' .ws **/tools/waf-*.*.**-* .lock-*'
    conf.excl += ' **/.git **/.gitignore **/.gitattributes '
    conf.excl += ' **/*.tar.gz **/*.pyc '

class chksum(Task.Task):
    always_run = True
    after = ['hexgen']
    calculate_checksum = '${PYTHON} ${chksum_script} ${chksum_ini_file_abs_path} -bd=${cs_out_dir} -hf=${SRC[0].relpath()}'
    writeback_command = '${PYTHON} ${writeback_script} --conffile ${cs_out_file} --elffile ${SRC[1].relpath()} --tool ${OBJDUMP}'
    run_str = (calculate_checksum, writeback_command)
    color = 'RED'

@TaskGen.feature('chksum')
@TaskGen.before('add_bingen_task')
@TaskGen.after('apply_link', 'add_hexgen_task')
def add_chksum_task(self):
    try:
        link_task = self.link_task
        hexgen = self.hexgen
    except AttributeError:
        return
    self.create_task('chksum', src=[hexgen.outputs[0], link_task.outputs[0]])


def doxygen(bld):
    import sys
    import logging
    from waflib import Logs

    if not bld.variant:
        bld.fatal('A build variant must be specified, run \'python {} --help\'\
'.format(sys.argv[0]))

    if not bld.env.DOXYGEN:
        bld.fatal('Doxygen was not configured. Run \'python {} --help\'\
'.format(sys.argv[0]))

    _docbuilddir = os.path.normpath(bld.bldnode.abspath())
    doxygen_conf_dir = os.path.join('documentation', 'doc', 'doxygen')
    if not os.path.exists(_docbuilddir):
        os.makedirs(_docbuilddir)
    if bld.variant == 'primary':
        doxygenconf = os.path.join(doxygen_conf_dir, 'doxygen-p.conf')
    elif bld.variant == 'secondary':
        doxygenconf = os.path.join(doxygen_conf_dir, 'doxygen-s.conf')
    elif bld.variant == 'bootloader':
        doxygenconf = os.path.join(doxygen_conf_dir, 'doxygen-bootloader.conf')

    log_file = os.path.join(bld.bldnode.abspath(), 'doxygen_' + \
                            bld.variant + '.log')
    bld.logger = Logs.make_logger(log_file, out)
    hdlr = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    hdlr.setFormatter(formatter)
    bld.logger.addHandler(hdlr)

    bld(features='doxygen', doxyfile=doxygenconf)


def sphinx(bld):
    import sys
    import logging
    from waflib import Logs
    log_file = os.path.join(bld.bldnode.abspath(), 'sphinx.log')
    bld.logger = Logs.make_logger(log_file, out)
    hdlr = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    hdlr.setFormatter(formatter)
    bld.logger.addHandler(hdlr)
    bld.recurse(os.path.join('documentation', 'doc', 'sphinx'))


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
    self.hexgen = self.create_task('hexgen', src=link_task.outputs[0], tgt=link_task.outputs[0].change_ext('.hex'))


class binflashheadergen(Task.Task):
    always_run = True
    after = ['chksum']
    run_str = '${OBJCOPY} -j .flashheader -O binary ${SRC} ${TGT}'
    color = 'RED'


class binflashgen(Task.Task):
    always_run = True
    after = ['chksum']
    run_str = '${OBJCOPY} -R .ext_sdramsect_bss -R .bkp_ramsect -R .flashheader -O binary ${SRC} ${TGT}'
    color = 'RED'


@TaskGen.feature('bingen')
@TaskGen.after('apply_link', 'add_chksum_task')
def add_bingen_task(self):
    try:
        link_task = self.link_task
    except AttributeError:
        return
    self.create_task('binflashgen', src=link_task.outputs[0], tgt=link_task.outputs[0].change_ext('_flash.bin'))
    self.create_task('binflashheadergen', src=link_task.outputs[0], tgt=link_task.outputs[0].change_ext('_flashheader.bin'))


import waflib.Tools.asm  # import before redefining
from waflib.TaskGen import extension


class Sasm(Task.Task):
    color = 'BLUE'
    run_str = '${CC} ${CFLAGS} ${CPPPATH_ST:INCPATHS} -DHSE_VALUE=8000000 -MMD -MP -MT${TGT} -c -x assembler -o ${TGT} ${SRC}'


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


def check_subprocess(prg, rtn_code, std_out=None, std_err=None):
    if rtn_code == 0:
        if std_out:
            print(std_out)
        print('Success: Process return code from program {} code: {}'.format(prg, str(rtn_code)))
    else:
        if std_err:
            print(std_err)
        print('Error: Process return code from program {} code: {}'.format(prg, str(rtn_code)))
        sys.exit(1)

# vim: set ft=python :
