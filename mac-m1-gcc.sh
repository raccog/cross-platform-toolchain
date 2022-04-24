#!/bin/bash

#
#	This script installs GCC and Binutils to cross-compile to x86_64
#	using homebrew on MacOS.
#
#	It also installs all dependencies needed on MacOS and builds from source.
#	Files are installed to $HOME/opt/cross
#

PREFIX=$HOME/opt/cross
TARGET=x86_64-elf
CPUS=`nproc`

# Install GMP
echo "./configure --prefix=$PREFIX
make -j$CPUS
make install
exit" > gmp.txt
brew list gmp
if [[ $? == 0 ]]; then
    brew reinstall --build-from-source gmp -i < gmp.txt
else
    brew install --build-from-source gmp -i < gmp.txt
fi
rm gmp.txt

# Install MPFR
echo "./configure --prefix=$PREFIX --with-gmp=$PREFIX
make -j$CPUS
make install
exit" > mpfr.txt
brew list mpfr
if [[ $? == 0 ]]; then
    brew reinstall --build-from-source mpfr -i < mpfr.txt
else
    brew install --build-from-source mpfr -i < mpfr.txt
fi
rm mpfr.txt

# Install MPC
echo "./configure --prefix=$PREFIX --with-gmp=$PREFIX --with-mpfr=$PREFIX
make -j$CPUS
make install
exit" > mpc.txt
brew list gmp
if [[ $? == 0 ]]; then
    brew reinstall --build-from-source libmpc -i < mpc.txt
else
    brew install --build-from-source libmpc -i < mpc.txt
fi
rm mpc.txt

# Install binutils using homebrew interactive mode
echo "./configure --enable-targets=all --target="$TARGET" --disable-nls \
    --prefix=$PREFIX --with-sysroot --disable-werror
make -j$CPUS
make install
exit" > binutils.txt
brew list $TARGET-binutils
if [[ $? == 0 ]]; then
    brew reinstall --build-from-source $TARGET-binutils -i < binutils.txt
else
    brew install --build-from-source $TARGET-binutils -i < binutils.txt
fi
rm binutils.txt

# Export path to find assembler and linker
export PATH="$PREFIX/bin:$PATH"

# Install GCC
echo "mkdir build
cd build
../configure --target="$TARGET" --prefix=$PREFIX --disable-nls \
    --without-isl --without-headers --enable-languages=c,c++ \
    --with-as="$(which $TARGET-as)" --with-ld="$(which $TARGET-ld)" \
    --disable-hosted-libstdcxx --with-gmp=$PREFIX --with-mpfr=$PREFIX \
    --with-mpc=$PREFIX
make -j$CPUS all-gcc
make -j$CPUS all-target-libgcc
make install-gcc
make install-target-libgcc
exit" > gcc.txt
brew list $TARGET-gcc
if [[ $? == 0 ]]; then
    brew reinstall --build-from-source $TARGET-gcc -i < gcc.txt
else
    brew install --build-from-source $TARGET-gcc -i < gcc.txt
fi
rm gcc.txt
