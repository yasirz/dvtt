# Data Validation & Transfer Tool (DVTT)
Data Validation & Transfer Tool (ODVTT) is partially related to DIRBS System. It is used to validate operator 
data dump which is imported into DIRBS Core.

### Directory structure

This repository contains code for **ODVTT**. Directory structure is:

* ``examples/`` -- Contains JSON configuratio file which is passed as command line argument
* ``schemas/`` -- Validation schema for JSON configuration & CSV file
* ``sftp/`` -- An example .pem for file transfer
* ``tests/`` -- Unit test scripts and Data

### Prerequisites
In order to run a development environment, download and install, [Python 3.6+](https://www.python.org/downloads/)

Downlload java based validation tool [CSV Validator](https://github.com/digital-preservation/csv-validator/tree/master/csv-validator-cmd)
& [Java](https://www.java.com/en/download/) 

We also assume that this repo is cloned from Github onto the local computer, it is assumed that 
all commands mentioned in this guide are run from root directory of the project and inside
```virtual environment```

On Windows, we assume that a Bash like shell is available (i.e Bash under Cygwin), with GNU make installed.

#### Starting a dev environment
The easiest and quickest way to get started is to use local-only environment (i.e everything runs locally). To setup 
the local environment, follow the section below:

#### Setting up local dev environment
For setting up a local dev environment we assume that the ```prerequisites``` are met already. To setup a local 
environment:
* Create virtual environment using **virtualenv** and activate it:
```bash
virtualenv venv
source venv/bin/activate
```
*   For Windows, you have to install virtualenv using pip:
```bash
pip install virtualenv
virtualenv venv
venv\bin\activate.bat
```

* Install the project requirements
```bash
$ pip install -r requirements.txt
```

**Note:** _Please see the [odvtt_example.json](examples/odvtt_example.json) configuration file for inputs which are required._

* Run the dvtt tool
```bash
python odvtt.py /your/configuration/file.json
```
