from setuptools import setup, find_packages


setup(
    name="rankor-api",
    description="An API for comparing things to rank them",
    version="0.0.1",
    author="Irmak Sirer",
    author_email="irmak.sirer@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi == 0.79.0",
        "Flask == 2.1.2",
        "Flask-PyMongo==2.3.0",
        "Flask-Login == 0.6.1"
        "pymongo[srv] == 4.1.1",
        "pydantic == 1.9.1",
        "trueskill == 0.4.5"
    ]
)
