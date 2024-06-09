from setuptools import setup, find_packages

setup(
    name='cocotbext-qspi',
    version='0.1.0',
    description='Cocotb extension for QSPI verification',
    author='Jithesh Vijay',
    author_email='jitheshvijay67@gmail.com',
    url='https://github.com/JitheshVijay/cocotbext-qspi',
    packages=find_packages(),
    install_requires=[
        'cocotb>=1.5.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Testing',
    ],
    python_requires='>=3.6',
)
