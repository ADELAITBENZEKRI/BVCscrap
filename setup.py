from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

setup(
    name='BVCscrap',
    version='0.0.4',
    description='Python library to scrape financial data from Casablanca Stock Exchange',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='ANDAM Amine and editor BOUAYAD Rayane',
    author_email='bouayadr39@gmail.com',
    url='https://github.com/Rayane3/BVCscrap',
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
