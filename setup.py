from setuptools import setup, find_packages

pkg_version = '0.1.1'

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(name='APImetrics',
      version=pkg_version,
      description="APImetrics Client",
      long_description=open('README.md', 'r').read(),
      classifiers=[
          # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
          'Development Status :: 4 - Beta',

          # Pick your license as you wish (should match "license" above)
          'License :: OSI Approved :: Apache Software License',

          # Indicate who your project is intended for
          "Intended Audience :: Developers",
          "Intended Audience :: System Administrators",
          "Topic :: Software Development :: Testing",
          "Topic :: System :: Networking :: Monitoring",
          "Topic :: Utilities",

          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",

          "Environment :: Console",
          "Operating System :: POSIX",
      ], 
      keywords='api http monitoring test apimetrics',
      author='Nick Denny',
      author_email='nick@apimetrics.io',
      url='http://apimetrics.io/',
      license='License :: OSI Approved :: Apache Software License',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=install_requires,
      entry_points={
          'console_scripts': ['apimetrics=apimetrics.cli:main'],
          'setuptools.installation': [
              'eggsecutable=apimetrics.cli:main',
          ]
      },
      download_url="https://github.com/APImetrics/APImetrics-Python-Client/archive/v{pkg_version}.tar.gz".format(pkg_version=pkg_version)
     )
