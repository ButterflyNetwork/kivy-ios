# Background
We use kivy-ios to build python and numpy for the
phone. This is a pretty complex repo - it patches the
shit out of stuff to make the binaries phone compatible. It's
_very_ specific about versions of python and ancillary libraries
because of this.

Historically, Krishna added a bunch of changes (branch: python-3.9.1) 
on top of the main repo version (1.2.1) he forked - some to correct issues that
may have been address in the upstream
repo, some perhaps specific to our needs. Frankly, I've not walked
through these in detail yet.

With the move from Rosetta to a naive arm64 Simulator, we can't
build traditional fat binaries - you could when we had different
architectures for different platforms, but `lipo` barfs on two
arm64 (ios_arm64 and ios_sim_arm64) binaries. Unfortunately, our fork
of kivy-ios, and the master branch of the upstream repo, both assume
an x86-64 simulator, and build traditional fatties.

I've branched an open [PR](https://github.com/kivy/kivy-ios/pull/7780) which addresses
the arm64 issue. At the time of this writing, this is a WIP, so a tad dangerous - we
should revisit prior to going live.

# Building
```
git clone git@github.com:ButterflyNetwork/kivy-ios.git
git checkout bfly-arm64
(pyenv install 3.10.10 # if needed)
pyenv virtualenv 3.10.10 kivy-ios
pyenv local kivy-ios
pip install -e .
toolchain build python3 numpy
```
The choice of 3.10.10 may not be necessary - but this is the mobile version
built by the repo, so figured to follow suit.

This should construct the libraries and xcframeworks (if you use 'em)
we need. The above `toolchain` target builds for the default simulator
on the platform and for the phone (M1 w/o rosetta: arm64/arm64, otherwise: x86_64/arm64).
`toolchain` has a bunch of useful actions - check out `status`, `clean`, and `distclean`


# Branch history
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








