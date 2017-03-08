from setuptools import setup, find_packages

setup(name='mediaqbot-client',
    version='0.0.1',
    description='Player for the Telegram MediaQBot',
    author='Hans Ole Hatzel',
    author_email='hhatzel@gmail.com',
    license='MIT',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mediaq = mediaqclient.main:launch'
        ]
    }
)
