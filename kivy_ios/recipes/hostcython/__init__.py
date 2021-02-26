from kivy_ios.toolchain import Recipe, shprint, cache_execution
from kivy_ios.context_managers import cd, python_path
from os.path import join
import sh


class HostCython(Recipe):
    depends = ["hostpython3"]
    archs = ["x86_64"]
    version = '0.29.22'
    url = 'https://github.com/cython/cython/archive/{version}.zip'

    @cache_execution
    def install(self):
        arch = self.filtered_archs[0]
        build_dir = self.get_build_dir(arch.arch)
        hostpython = sh.Command(self.ctx.hostpython)
        hostpythonprefix = join(self.ctx.dist_dir, "hostpython3")

        with cd(build_dir):
            shprint(hostpython, "setup.py", "install",
                    f"--prefix={hostpythonprefix}")


recipe = HostCython()
