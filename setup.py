from setuptools import find_packages, setup

setup(name='frorigsrch',
      version='0.1',
      description='A GUI for quering Oxford-English-Dictionary for the french origin of words',
      url='https://github.com/marsipu/frorigsrch',
      author='Martin Schulz',
      author_email='dev@earthman-music.de',
      python_requires='>=3.8',
      install_requires=['PyQt5',
                        # 'mne_pipeline_hd',
                        'beautifulsoup4'],
      license='GPL-3.0',
      packages=find_packages(),
      package_data={},
      classifiers=["Programming Language :: Python :: 3",
                   "License :: OSI Approved :: BSD License",
                   "Operating System :: OS Independent",
                   "Intended Audience :: Science/Research"],
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'frorigsrch = frorigsrch.__main__:main'
          ]
      }

      )
