# (2023-08) ios_sim_arm64: python-3.9.1, numpy-1.20.1

Some notes on building our current production python and numpy
libraries for `ios_sim_arm64` on the branch `arm64-sim-3.9.1`.

This branch is in turn base on:

- the ios_sim_arm64 aware branch `arm64/feat/native-simulator` (see branch info below for details).
- Krishna's origin `python-3.9.1` branch

## Python

### python3 target

Since we want ios_sim_arm64 binaries matched to those in production,
we have copied Krisha's patches from the branch,
`python-3.9.1`, which was used to build our libraries back in April of 2022.  
Here's the diff prior to the copy of patches:
```
(arm64-sim-3.9.1) ~/src/kivy-ios$ git diff --numstat HEAD..python-3.9.1 kivy_ios/recipes/python3/
0       92      kivy_ios/recipes/python3/ModulesSetup
0       2       kivy_ios/recipes/python3/ModulesSetup.mobile
7458    0       kivy_ios/recipes/python3/Python.patch
56      0       kivy_ios/recipes/python3/RestoreDynload.patch
120     0       kivy_ios/recipes/python3/Setup.embedded
34      0       kivy_ios/recipes/python3/Setup.iOS
35      76      kivy_ios/recipes/python3/__init__.py
0       104     kivy_ios/recipes/python3/configure.patch
0       19      kivy_ios/recipes/python3/ctypes_duplicate.patch
0       25      kivy_ios/recipes/python3/dynload_shlib.patch
0       12      kivy_ios/recipes/python3/posixmodule.patch
```
The new and old patches and Setup files are a disjoint set.
So we just swap their use in the recipe's __init__.py file. 

What is surprising is the size of the Python.patch.  Checking
the git log comments shows the Krishna pulled this patch from another
project, `beeware`, back in February of 2021:

```
commit 3c04bd20ef7ce25a90d08f8e4251c357eee2ab4a
Author: Krishna Ersson <kersson@butterflynetinc.com>
Date:   Mon Feb 15 23:36:38 2021 -0500

    Upgrade python3 to 3.9.1
    
    Uses patches from https://github.com/beeware/Python-Apple-support/tree/3.9/patch/Python
```

Again, this patch makes _a lot_ of changes to the code; (TODO) probably worth
reviewing at some point... The kivy-ios code does not do anything nearly as extensive.

BTW - the large number macro switches in the config section of `__init__.py`
are needed - they just indicate which api's are supported or not by the Mobile SDK.

### hostpython3 target

In addition to these changes, we had to patch the `hostpython3` target as the python 3.9.1 host 
build initially barfed running `configure` because of (M1 - arm?) platform issues. Happily, we
could just grap the patch used by pyenv for this purpose. Hooray!

      .pyenv/plugins/python-build/share/python-build/patches/3.9.1/Python-3.9.1/0001-bpo-45405-Prevent-internal-configure-error-when-runn.patch 

## Numpy

Krishna's python-3.9.1 branch has numpy related commits that post-date
the timestamps of our production python-3.9.1/numpy-1.20.1 binaries on
S3 (built on Mar 11, 2021). 

This is a bit of a pickle as some symbols, e.g. `_sgemm_`, in the binaries
generated from
the HEAD of this tree are now slightly different from those in production
for ios_arm64.

There is one prior commit, 2 weeks before release, that looks like a
probable source of our current production binaries:


     commit 8f41cb5260c1a7f129e5cd1cff561e9a2f1cdc0f
     Author: Krishna Ersson <kersson@butterflynetinc.com>
     Date:   Thu Feb 25 22:25:42 2021 -0500

             Upgrade numpy to 1.20.1

So instead of our stuff, I've opted to use a slightly more recent
main line branch commit of 1.20.2 (together with the arm64 simulator branch changes):
    
       commit e38cd58b16aed04aae6701e4f2fb4b1dbf854f44
       Merge: 6b245b1 84595ab
       Author: Andre Miras <AndreMiras@users.noreply.github.com>
       Date:   Sun Apr 4 20:25:20 2021 +0200
    
           Merge pull request #604 from misl6/feat/upgrade-numpy
    
           Update numpy to version 1.20.2

1.20.2 is not 1.20.1, but should be compatible (no header changes).
It also addresses the same Accelerate framework issue mentioned
in Krishna's commits.

---

# Background
We use kivy-ios to build python and numpy for the
phone. 

A lot of th work here involves code patches to make the binaries phone compatible. These patches are, of course,
tightly couple to library versions.

Historically, Krishna added a bunch of changes (branch: python-3.9.1) 
on top of the main repo version (1.2.1) he forked - some to correct issues that
may have been address in the upstream
repo, some perhaps specific to our needs. Frankly, I've not walked
through these in detail yet.

With the move from Rosetta to a naive arm64 Simulator, we can't
build traditional fat binaries because the arm64 simulator and arm64 device code share the same architecture.
Unfortunately, our fork
of kivy-ios, and the master branch of the upstream repo, both assume
an x86-64 simulator, and build traditional fatties.

So we've branched an open [PR](https://github.com/kivy/kivy-ios/pull/7780) which addresses
the arm64 issue. At the time of this writing, this is a WIP, so a tad dangerous - we
should revisit prior to going live. But for now, we're just adding the ios_sim_arm64 slice, so 
device code will remain unchanged.

# Building
```
git clone git@github.com:ButterflyNetwork/kivy-ios.git
git checkout arm64-sim-3.9.1
(pyenv install 3.9.1 # if needed)
pyenv virtualenv 3.9.1 kivy-ios
pyenv local kivy-ios
pip install -e .
toolchain build python3 numpy
```
This should construct the libraries and xcframeworks (if you use 'em)
we need. The above `toolchain` target builds for the default simulator
on the platform and for the phone (M1 w/o rosetta: arm64/arm64, otherwise: x86_64/arm64).
`toolchain` has a bunch of useful actions - check out `status`, `clean`, and `distclean`


# Branch structure / history

You may want to reference these:
```
~/src/kivy-ios$ git remote -vv
arm64	git@github.com:misl6/kivy-ios.git (fetch)
arm64	git@github.com:misl6/kivy-ios.git (push)
origin	git@github.com:ButterflyNetwork/kivy-ios.git (fetch)
origin	git@github.com:ButterflyNetwork/kivy-ios.git (push)
upstream	git@github.com:kivy/kivy-ios.git (fetch)
upstream	git@github.com:kivy/kivy-ios.git (push)

git checkout arm64/feat/native-simulator # this is the branch in the arm64 PR.
git switch -c bfly-arm64
git push -u origin bfly-arm64

~/src/kivy-ios$ gb -vv
* bfly-arm64   e57f300 [origin/bfly-arm64] Support ARM64 Simulator + Introduce build platform concept
...
```








