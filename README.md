# Cross Platform Toolchain Scripts

This repository contains scripts to download and install a cross-platform toolchain

## build-gcc.py

This script downloads, compiles, and installs an x86_64-elf GCC toolchain.

Run with:

```bash
python3 build-gcc.py
```

It assumes that it will be run on a unix-like operating system.
Currently, it has only been tested on Ubuntu 20.04.4 with Linux version 5.13.0-40.

### Dependencies  

* Python3 (tested with version 3.8.10)
* python-gnupg (install with `pip install python-gnupg`)
* wget (for downloading source code)

## mac-m1-gcc.sh

This script installs an x86_64-elf GCC toolchain using homebrew.

It assumes that it will be run on a unix-like operating system with homebrew installed.
Generally it is only used on MacOS systems that cannot compile directly from source.

### Purpose

The default GCC toolchain still cannot be compiled on the new aarch64-based Macs, so this script should only need to be used in this situation.
The homebrew version of GCC and Binutils does compile and work fine on aarch64-based Macs, though I am not sure why.
Either way, this is the reason I have named the script `mac-m1-gcc.sh`.

### Dependencies

* Homebrew (tested with version 3.4.7)
* `nproc` (to get number of cores)