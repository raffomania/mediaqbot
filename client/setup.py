from setuptools import setup

setup(name='mediaqbot-client',
    version='0.0.1',
    description='Player for the Telegram MediaQBot',
    author='Hans Ole Hatzel',
    author_email='hhatzel@gmail.com',
    license='MIT',
    packages=['mediaqclient'],
    entry_points={
        'console_scripts': [
            'mediaq = mediaqclient.main:launch'
        ]
    }
)
