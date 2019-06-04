# TMDAretro
Tagged Message Delivery Agent (TMDA) for Python 2.7

TMDA is an open source software application designed to significantly reduce the amount of spam (Internet junk-mail) you receive.

TMDAretro was created for those who rely on TMDA and need it to continue working with Python 2.7. It was forked from Kevin Goodsell's [tmda-fork](https://github.com/KevinGoodsell/tmda-fork).

## Pre-install:

Backup and remove any previous versions or make sure they are not ahead in your PATH or Python module load path.

## PyPI install:

```sh
pip2 install --upgrade --user TMDAretro  # remove --upgrade or --user as appropriate
```

## Alternatively, git install & tests:

```sh
git clone https://github.com/ccaputo/TMDAretro.git
cd TMDAretro/tmda
make clean
make          # to ./env
make test
make install  # to ~/.local
```

## Post-install:

Adjust configuration to use ~/.local/bin, or as appropriate, as the path to TMDA programs.

Confirm operational version matches what was is installed:

```sh
pip2 list --format=columns | grep TMDAretro  # if you used pip2 above to perform install
tmda-keygen --version
```

## Resources:

[Mailing Lists](https://sf.net/p/tmda/mailman/)

[Old Homepage](http://tmda.net)

[Old Sourceforge Project](http://sf.net/projects/tmda)

[TMDA: Python 3+ Effort by Cédric Dufour](https://github.com/cedric-dufour/tmda)

[TMDAng: Python 3+ Effort by Paul Jimenez](https://github.com/pjz/TMDAng)
