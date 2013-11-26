from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import numpy
import os

ext = Extension("ckdtree", ["ckdtree.pyx"],
            include_dirs = [numpy.get_include()])
                
setup(ext_modules=[ext],
              cmdclass = {'build_ext': build_ext})

#if os.path.isfile("ckdtree.c"):
#    os.remove("ckdtree.c")
