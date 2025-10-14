from setuptools import setup, find_packages

setup(
    name="darkmap",
    version="2.0",
    author="ICITIFY TECH",
    description="Dark-Map — All-in-One Nmap Automation Framework",
    packages=find_packages(),  # finds the inner darkmap folder
    install_requires=["jinja2", "requests", "python-nmap"],
    entry_points={
        "console_scripts": [
            "darkmap=darkmap.darkmap:launch",  # points to launch() inside darkmap/darkmap.py
        ],
    },
    python_requires=">=3.8",
)
