
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mailspoof",
    version="1.2.0",
    author="Syed Sameer Ul Hassan",
    description="Professional Email Spoofing and Phishing Simulation Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/syed-sameer-ul-hassan/MailSpoof",
    project_urls={
        "Bug Tracker": "https://github.com/syed-sameer-ul-hassan/MailSpoof/issues",
        "Documentation": "https://github.com/syed-sameer-ul-hassan/MailSpoof/blob/main/README.md",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Communications :: Email",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="email spoofing phishing simulation penetration testing red team smtp security audit social engineering cybersecurity",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "dnspython>=2.0",
    ],
    package_data={
        "lib": [
            "templates/builtins/*.txt",
        ],
    },
    entry_points={
        "console_scripts": [
            "mailspoof=lib.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
