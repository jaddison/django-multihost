import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

from distutils.core import setup
setup(
    name = 'django-multihost',
    description = 'Simple multihost handling for Django',
    long_description=read('README.rst'),
    author='James Addison',
    author_email='code@scottisheyes.com',
    packages = ['multihost',],
    version = '0.3',
    url='http://github.com/jaddison/django-multihost',
    keywords=[],
    license='BSD',
    classifiers=[
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: BSD License',
      'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
      'Framework :: Django',
    ],
)