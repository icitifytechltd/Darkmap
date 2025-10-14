from setuptools import setup, find_packages

setup(
    name="darkmap",
    version="2.0",
    author="ICITIFY TECH",
    description="Dark-Map — Advanced Python wrapper around Nmap with plugin support.",
    packages=find_packages(),
    install_requires=["jinja2", "requests", "python-nmap"],
    entry_points={
        "console_scripts": [
            "darkmap=darkmap.darkmap:launch",
        ],
    },
    python_requires=">=3.8",
)
