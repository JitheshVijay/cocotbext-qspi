from setuptools import setup, find_packages

setup(
    name='cocotbext-qspi',
    version='0.1.0',
    description='cocotb extension for QSPI flash verification, with a flash slave model',
    author='Jithesh Vijay',
    author_email='jitheshvijay67@gmail.com',
    url='https://github.com/JitheshVijay/cocotbext-qspi',
    packages=find_packages(),
    install_requires=[
        'cocotb>=2.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Framework :: cocotb',
        'Topic :: Software Development :: Testing',
    ],
    python_requires='>=3.8',
)
