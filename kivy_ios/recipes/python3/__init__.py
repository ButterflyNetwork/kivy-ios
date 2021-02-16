from kivy_ios.toolchain import Recipe, shprint
from kivy_ios.context_managers import cd
from os.path import join
import sh
import shutil
import os
import logging

logger = logging.getLogger(__name__)


class Python3Recipe(Recipe):
    version = "3.9.1"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    depends = ["hostpython3", "libffi", "openssl"]
    library = "libpython3.9.a"
    pbx_libraries = ["libz", "libbz2", "libsqlite3"]

    def init_with_ctx(self, ctx):
        super().init_with_ctx(ctx)
        self.set_python(self, "3.9")
        ctx.python_ver_dir = "python3.9"
        ctx.python_prefix = join(ctx.dist_dir, "root", "python3")
        ctx.site_packages_dir = join(
            ctx.python_prefix, "lib", ctx.python_ver_dir, "site-packages")

    def prebuild_arch(self, arch):
        # common to all archs
        if self.has_marker("patched"):
            return
        self.apply_patch("Python.patch")
        self.copy_file("Setup.embedded", "Modules/Setup.local")
        self.append_file("Setup.iOS", "Modules/Setup.local")
        self.set_marker("patched")

    def get_build_env(self, arch):
        build_env = arch.get_env()
        build_env["PATH"] = "{}:{}".format(
            join(self.ctx.dist_dir, "hostpython3", "bin"),
            os.environ["PATH"])
        build_env["CFLAGS"] += " --sysroot={}".format(arch.sysroot)
        return build_env

    def build_arch(self, arch):
        build_env = self.get_build_env(arch)
        configure = sh.Command(join(self.build_dir, "configure"))
        py_arch = arch.arch
        if py_arch == "armv7":
            py_arch = "arm"
        elif py_arch == "arm64":
            py_arch = "aarch64"
        prefix = join(self.ctx.dist_dir, "root", "python3")
        shprint(configure,
                "CC={}".format(build_env["CC"]),
                "LD={}".format(build_env["LD"]),
                "CFLAGS={}".format(build_env["CFLAGS"]),
                "LDFLAGS={}".format(build_env["LDFLAGS"]),
                "ac_cv_file__dev_ptmx=no",
                "ac_cv_file__dev_ptc=no",
                "--host={}-apple-ios".format(py_arch),
                "--build=x86_64-apple-darwin",
                "--prefix={}".format(prefix),
                "--without-ensurepip",
                "--without-doc-strings",
                "--enable-ipv6",
                "PYTHON_FOR_BUILD=_PYTHON_PROJECT_BASE=$(abs_builddir) \
                    _PYTHON_HOST_PLATFORM=$(_PYTHON_HOST_PLATFORM) \
                    PYTHONPATH=$(shell test -f pybuilddir.txt && echo $(abs_builddir)/`cat pybuilddir.txt`:)$(srcdir)/Lib\
                    _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata_$(ABIFLAGS)_$(MACHDEP)_$(MULTIARCH)\
                    {}".format(sh.Command(self.ctx.hostpython)),
                _env=build_env)
        shprint(sh.make, self.ctx.concurrent_make)

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_env = self.get_build_env(arch)
        build_dir = self.get_build_dir(arch.arch)
        shprint(sh.make, self.ctx.concurrent_make,
                "-C", build_dir,
                "install",
                "prefix={}".format(join(self.ctx.dist_dir, "root", "python3")),
                _env=build_env)
        self.reduce_python()

    def reduce_python(self):
        logger.info("Reduce python")
        logger.info("Remove files unlikely to be used")
        with cd(join(self.ctx.dist_dir, "root", "python3")):
            sh.rm("-rf", "bin", "share")
        # platform binaries and configuration
        with cd(join(
                self.ctx.dist_dir, "root", "python3", "lib",
                "python3.9", "config-3.9-darwin")):
            sh.rm(
                "libpython3.9.a",
                "python.o",
                "config.c.in",
                "makesetup",
                "install-sh",
            )

        # cleanup pkgconfig and compiled lib
        with cd(join(self.ctx.dist_dir, "root", "python3", "lib")):
            sh.rm("-rf", "pkgconfig", "libpython3.9.a")

        # cleanup python libraries
        with cd(join(
                self.ctx.dist_dir, "root", "python3", "lib", "python3.9")):
            sh.rm("-rf", "wsgiref", "curses", "idlelib", "lib2to3",
                  "ensurepip", "turtledemo", "lib-dynload", "venv",
                  "pydoc_data")
            sh.find(".", "-path", "*/test*/*", "-delete")
            sh.find(".", "-name", "*.exe", "-type", "f", "-delete")
            sh.find(".", "-name", "test*", "-type", "d", "-delete")
            sh.find(".", "-iname", "*.pyc", "-delete")
            sh.find(".", "-path", "*/__pycache__/*", "-delete")
            sh.find(".", "-name", "__pycache__", "-type", "d", "-delete")

            # now precompile to Python bytecode
            hostpython = sh.Command(self.ctx.hostpython)
            shprint(hostpython, "-m", "compileall", "-f", "-b")
            # sh.find(".", "-iname", "*.py", "-delete")

            # some pycache are recreated after compileall
            sh.find(".", "-path", "*/__pycache__/*", "-delete")
            sh.find(".", "-name", "__pycache__", "-type", "d", "-delete")

            # create the lib zip
            logger.info("Create a python3.9.zip")
            sh.mv("config-3.9-darwin", "..")
            sh.mv("site-packages", "..")
            sh.zip("-r", "../python39.zip", sh.glob("*"))
            sh.rm("-rf", sh.glob("*"))
            sh.mv("../config-3.9-darwin", ".")
            sh.mv("../site-packages", ".")


recipe = Python3Recipe()
