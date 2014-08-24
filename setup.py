from setuptools import setup, find_packages

setup(
    name="rabbittop",
    version="0.1.0",
    description="RabbitMQ commandline monitoring tool",
    url="https://github.com/jve/rabbit_top",
    author="Jozef van Eenbergen",
    author_email="jvaneenbergen@gmail.com",
    license="MIT",
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers :: System Administrators :: Operations',
        'Topic :: Software Development :: Monitoring',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords="monitoring rabbitmq support",
    packages=find_packages(exclude=['bin', 'docs', 'tests']),
    entry_points={
        'console_scripts': [
            'rabbittop=rabbittop.main:main',
        ],
    },
)
