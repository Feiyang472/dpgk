from setuptools import setup

setup(name='dpgk',
      version='0.0',
      description='Workflows for classical/path integral MD simulations of physical properties',
      url='http://github.com/Feiyang472/dpgk',
      author='Ripeng Luo, Yifan Li, Feiyang Chen',
      packages=['dpgk'],
      zip_safe=False,
      install_requires = [
          'apache-airflow',
          'dpdispatcher',
          'matplotlib',
          'numpy'
      ])