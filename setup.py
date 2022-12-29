from setuptools import setup, find_packages

setup(
    name='TeleAuth',
    version='1.0.0',
    description='A library for user authentication in Telegram bots',
    packages=find_packages(),
    install_requires=['prettytable'],
    author='nilopro',
    author_email='menezesdev@pm.me',
    url='https://github.com/nilopro/TeleAuth',
    download_url='https://github.com/nilopro/TeleAuth/archive/v1.0.0.tar.gz',
    keywords=['telegram', 'authentication', 'bot'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)