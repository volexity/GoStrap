# GoStrap

GoStrap is a tool to easily bootstrp GO samples using a set of GO libraries and GO versions.

## Build & Install

To build GoStrap use Hatch's usual build command :
```bash
hatch build
```

The built archive will be placed in the "dist" directory as a .whl file.
To install GoStrap, simply install the .whl file using pip.

```bash
pip install dist/gostrap-*.whl
```

## Command Line Usage

Once installed, a new utility `gostrap` will be available.

```
usage: gostrap [-h] [-l [LIBS ...]] [-g [VERSIONS ...]] [-a ARCH] [-p PLATFORM] [-f] [-s]

options:
  -h, --help                              show this help message and exit
  -l [LIBS ...], --libs [LIBS ...]        List of GO libs to include in the generated samples.
  -g [VERSIONS ...], --go [VERSIONS ...]  List of GO version to build the samples with.
  -a ARCH, --arch ARCH                    Target CPU architecture.
  -p PLATFORM, --platform PLATFORM        Target Operaring System.
  -f, --force                             Force build existing samples.
  -s, --show                              Show available go versions
```

Here is a typical workflow using GoStrap :

```bash
gostrap --libs "set,of,libs" --go "go1.23.4,go1.14" --arch "AMD64" --platform "Windows"
```
