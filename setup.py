import io
from setuptools import setup, find_packages

long_description = '\n'.join((
    io.open('README.rst', encoding='utf-8').read(),
    io.open('CHANGES.txt', encoding='utf-8').read()
))

setup(
    name='proxima',
    version='0.1.dev0',
    description="Asynchronous reverse HTTP proxy",
    long_description=long_description,
    author="Martijn Faassen",
    author_email="faassen@startifact.com",
    url='http://proxima.readthedocs.org',
    license="BSD",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.5',
    ],
    keywords="configuration",
    install_requires=[
        'setuptools',
        'aiohttp',
    ],
    entry_points={
        'console_scripts': [
            'proxima = proxima.proxy:main',
        ]
    },
    extras_require=dict(
        test=[
            'pytest >= 2.5.2',
            'py >= 1.4.20',
            'pytest-cov',
            'pytest-remove-stale-bytecode',
        ],
    ),
)
