from setuptools import setup, find_packages

setup(
    name='teleauth',
    version='1.1.1',
    description='A library for user authentication in Telegram bots',
    packages=find_packages(),
    install_requires=['prettytable'],
    author='nilopro',
    author_email='menezesdev@pm.me',
    url='https://github.com/nilopro/teleauth',
    download_url='https://github.com/nilopro/teleauth/archive/v1.1.0.tar.gz',
    keywords=['telegram', 'authentication', 'bot'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)