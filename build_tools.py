import gnupg, os, shutil, subprocess
from pathlib import Path


gpg = gnupg.GPG(gnupghome=Path(os.environ['HOME']).joinpath('.gnupg'))



#------------------------------
# General Build Config
#------------------------------
PREFIX = Path(os.environ['HOME']).joinpath('opt/cross')
TARGET = 'x86_64-elf'
CPUS = os.cpu_count()
MAKEFLAGS = f'-j{CPUS}'


# Tool to download, build, and install (gcc, binutils)
class Tool:
    # Each attribute needed to make a valid tool
    ATTRS = ['flags', 'key_id', 'name', 'version', 'tar', 'url', 'make', 'install']

    # Returns true if this tool has all needed atributes
    def is_valid(self):
        for attr in self.ATTRS:
            if not hasattr(self, attr):
                return False
        return True

    # Default make command
    def make(self):
       return subprocess.run(['make', MAKEFLAGS], stdout=subprocess.DEVNULL).returncode == 0

    # Default install command
    def install(self):
        return subprocess.run(['make', 'install'], stdout=subprocess.DEVNULL).returncode == 0

    # Adds PREFIX to the source directory
    def src_prefix(self):
        return with_prefix(self.name)

    # Returns tar signature filename
    def tar_signature(self):
        return self.tar + '.sig'

    # Adds PREFIX to the tar file
    def tar_prefix(self):
        return with_prefix(self.tar)


#------------------------------
# Package-specific Functions
#------------------------------
def gcc_make():
    if subprocess.run(['make', MAKEFLAGS, 'all-gcc'], stdout=subprocess.DEVNULL).returncode:
        return False
    if subprocess.run(['make', MAKEFLAGS, 'all-target-libgcc'], stdout=subprocess.DEVNULL).returncode:
        return False
    return True


def gcc_install():
    if subprocess.run(['make', 'install-gcc'], stdout=subprocess.DEVNULL).returncode:
        return False
    if subprocess.run(['make', 'install-target-libgcc'], stdout=subprocess.DEVNULL).returncode:
        return False
    return True


#------------------------------
# Tool definitions
#------------------------------
BINUTILS = Tool()
GCC = Tool()


# Binutils tool info
BINUTILS.version = '2.38'
BINUTILS.name = f'binutils-{BINUTILS.version}'
BINUTILS.tar = f'{BINUTILS.name}.tar.xz'
BINUTILS.url = f'https://ftp.gnu.org/gnu/binutils/{BINUTILS.tar}'
BINUTILS.flags = [f'--target={TARGET}', f'--prefix={PREFIX}', '--with-sysroot',
        '--disable-nls', '--disable-werror']
BINUTILS.key_id = '13FCEF89DD9E3C4F'


# GCC tool info
GCC.version = '11.2.0'
GCC.name = f'gcc-{GCC.version}'
GCC.tar = f'{GCC.name}.tar.xz'
GCC.url = f'https://ftp.gnu.org/gnu/gcc/{GCC.name}/{GCC.tar}'
GCC.make = gcc_make
GCC.install = gcc_install
GCC.flags = [f'--target={TARGET}', f'--prefix={PREFIX}', '--disable-nls',
        '--enable-languages=c,c++', '--without-headers']
GCC.key_id = '6EEB81F8981C74C7'


#---------------------
# Utility Functions
#---------------------

# Adds prefix to the start of a path
def with_prefix(path):
    return Path(PREFIX).joinpath(path)


# Creates a directory if it does not exist
def ensure_exists(path):
    path = Path(path)
    if not path.is_dir():
        os.makedirs(path)

#-------------------------------------------
# Downloading/building/installing functions
#-------------------------------------------

# Download a tar file and move it to the target directory
def download_tar(tool):
    file_target = tool.tar_prefix()
    # only download if tar file doesn't already exist
    if not os.path.isfile(file_target):
        print(f'Downloading {tool.name}...')
        subprocess.run(['wget', '-q', '--show-progress', tool.url])
        subprocess.run(['wget', '-q', '--show-progress', tool.url + '.sig'])
        with open(tool.tar_signature(), 'rb') as sig:
            if not gpg.verify_file(sig, tool.tar):
                print(f'Key invalid for {tool.name}.')
                os.remove(tool.tar)
                return False
            print(f'Key valid for {tool.name}.')
        shutil.move(tool.tar, file_target)
    return True


# Unpack a tar file in its target directory
def unpack_tar(tool):
    print(f'Unpacking {tool.tar}...')
    shutil.unpack_archive(tool.tar_prefix(), PREFIX)


# Build a tool
def build_tool(tool):
    # ensure tool is valid
    if not tool.is_valid():
        print('Tool is not valid. Check tool definitions.')
        return False
    # download and unpack tar
    verified = download_tar(tool)
    # delete signature
    if os.path.isfile(tool.tar_signature()):
        os.remove(tool.tar_signature())
    # return false if signature was not verified
    if not verified:
        return False
    unpack_tar(tool)
    # save current path for later
    original_dir = Path(os.getcwd())
    # change to build dir
    build_dir = Path(tool.src_prefix()).joinpath('build')
    ensure_exists(build_dir)
    os.chdir(build_dir)
    # configure
    print(f'Configuring {tool.name} with the following flags: {tool.flags}...')
    if subprocess.run(['../configure'] + tool.flags, stdout=subprocess.DEVNULL).returncode:
        print(f'Failed to configure {tool.name}. Exiting...')
        return False
    # compile
    print(f'Compiling {tool.name}...')
    if not tool.make():
        print(f'Failed to make {tool.name}. Exiting...')
        return False
    # install
    print(f'Installing {tool.name}...')
    if not tool.install():
        print(f'Failed to install {tool.name}. Exiting...')
        return False
    # return to original directory
    os.chdir(original_dir)
    # remove source and build files
    shutil.rmtree(tool.src_prefix())
    return True


# Imports all necessary gpg keys
def import_keys():
    print("Ensuring all necessary gpg keys are downloaded...")
    keys = gpg.list_keys()
    for tool in [BINUTILS, GCC]:
        foundkey = False
        for key in keys:
            if key['keyid'] == tool.key_id:
                print(f'Found key ({tool.key_id}) for {tool.name}')
                foundkey = True
                break
        if not foundkey:
            print(f'Downloading key ({tool.key_id}) for {tool.name}')
            gpg.recv_keys('keyserver.ubuntu.com', tool.key_id)

    
if __name__ == '__main__':
    print(f'Installing GCC toolchain for {TARGET}...')

    # Create toolchain dir ($HOME/opt/cross)
    ensure_exists(PREFIX)

    # Import keys each time just in case
    import_keys()

    # Build binutils and gcc
    if not build_tool(BINUTILS):
        exit(1)
    if not build_tool(GCC):
        exit(2)

    print('Build succeded!')

