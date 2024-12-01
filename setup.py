from setuptools import setup

setup(
    name="ghaze",  # Your CLI name
    version="0.1",
    py_modules=["ghaze"],  # Replace with your script name (without .py)
    install_requires=[],  # Add required libraries here
    entry_points={
        "console_scripts": [
            "ghaze=ghaze:main",  # Maps "ghaze" command to main()
        ],
    },
)
