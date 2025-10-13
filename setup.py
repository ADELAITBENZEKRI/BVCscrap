from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

setup(
    name='BVCscrap',
    version='0.0.4',
    description='Python library to scrape financial data from Casablanca Stock Exchange',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='ANDAM Amine and editor Ait benzekri Adel',
    author_email='adelaitbenzekri@gmail.com',
    url='https://github.com/ADELAITBENZEKRI/BVCscrap',
    license='MIT',
    packages=find_packages(include=["BVCscrap", "BVCscrap.*"]),
    install_requires=[
        'requests',
        'beautifulsoup4',
        'pandas',
        'lxml'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)

