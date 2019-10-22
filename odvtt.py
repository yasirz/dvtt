import os
import sys
import subprocess
import logging
import zipfile
import argparse
import json
import jsonschema
from pathlib import Path
import smtplib
import getpass
import paramiko
import warnings
import re
import platform
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate


def validate_configuration_file(schema, file_data):
    try:
        logger.info("Validating Configuration File")
        v = jsonschema.Draft7Validator(json.loads(schema))
        error_flag = False
        for error in sorted(v.iter_errors(json.loads(file_data)), key=str):
            print(error.message)
            error_flag = True
        if error_flag:
            return False
        return True
    except jsonschema.ValidationError:
        print("Validation Failed")
    except jsonschema.SchemaError:
        print("Validation Failed")
    except ValueError:
        print('Decoding JSON has failed')


def file_path_setting_win(path_config, schema_set=False):

    try:
        if schema_set:
            path_config = Path(path_config)
            path_config = path_config.resolve()
            url = str(f'{path_config}{os.sep}')
            path_config = re.escape(url)
            path_config = path_config
            return path_config

        path_config = Path(path_config)
        path_config = path_config.resolve()
        file_base_path = path_config.parent
        file_base_path = str(f'{file_base_path}{os.sep}')
        input_file_path = re.escape(file_base_path)
        path_config = input_file_path + path_config.name
        return path_config
    except Exception as ex:
        print("File handling error", ex.message)


def pre_validate_file(input_file, validator, schema_file, schema_dir='schemas/'):
    """Method which pre-validates the file using an external CSV validator against a CSV schema."""
    try:

        if platform.system() == 'Windows':
            schema_dir = file_path_setting_win(schema_dir, True)
            input_file = file_path_setting_win(input_file)
            validator = file_path_setting_win(validator)

        logger.info("File validation process started, please don't exit the application")
        result = subprocess.check_output([validator, input_file, schema_dir + schema_file])
        if result.find(b'PASS') == -1:
            logging.info('Pre-validation failed: {0}'.format(result))
        else:
            logger.info("Creating Zip")
            create_zip_file(input_file)
            return True
    except subprocess.CalledProcessError as err:
        logger.info('Pre-validation failed: {0}'.format(err.stdout))
        logger.info('Exiting script')
    except FileNotFoundError:
        print("We could not find the file")
        logger.info('Exiting script')
    except PermissionError:
        print("Permission Denied for accessing files")
        logger.info('Exiting script')
    except:
        print("An error undefined has occurred in validating file")
        logger.info('Exiting script')


def create_zip_file(input_file):
    try:
        path = Path(input_file)
        zip_file_name = path.stem + "_" + datetime.now().strftime("%Y-%m-%d-%H%m" + ".zip")
        zip_file = zipfile.ZipFile(zip_file_name, 'w')
        zip_file.write(path, path.name)
        zip_file.close()
        logger.info("Initializing file transfer")
        if transfer_file(zip_file_name):
            os.remove(zip_file_name)
            return True
        else:
            os.remove(zip_file_name)
            return False
    except zipfile.BadZipFile:
        print("Bad zip format")
        return False
    except zipfile.LargeZipFile:
        print("Zip64 required")
        return False


def transfer_file(input_file):
    try:
        path = Path(input_file)
        key = Path('sftp/certificate.pem')
        sftp_client = paramiko.SSHClient()
        sftp_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sftp_client.connect('192.168.100.214', username='root', key_filename=str(key))
        sftp_server = sftp_client.open_sftp()
        sftp_server.put(input_file, '/home/yasir/ftp/files/' + str(path), confirm=True)
        sftp_server.close()
        return True
    except IOError:
        os.remove(Path(path))
        print("Location not found")
        return False
    except paramiko.ssh_exception.SSHException:
        os.remove(Path(path))
        print("Not a valid key file")
        return False
    except paramiko.ssh_exception.NoValidConnectionsError:
        os.remove(Path(path))
        print("Unable to connect")
        return False


def send_email(server_host, server_port, email_address, email_password, email_to, email_cc, logger_file):
    try:
        msg = MIMEMultipart()
        msg['From'] = email_address
        msg['To'] = COMMASPACE.join(email_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = "ODVTT Notification"
        msg.attach(MIMEText("ODVTT status notification, please see the attachement for file transfer status\n\n\n\n\n"))
        logger_file = Path(logger_file)
        
        with open(logger_file, "rb") as file:
            part = MIMEApplication(
                file.read(),
                Name=logger_file.stem
            )

            part['Content-Disposition'] = 'attachment; filename="%s"' % logger_file.name
            msg.attach(part)

        mail = smtplib.SMTP_SSL(server_host, server_port)
        if mail.login(email_address, email_password):
            email_to = email_to + email_cc
            mail.sendmail(email_address, email_to, msg.as_string())
            logger.info("Email sent successfully")
            mail.close()
            return True
        else:
            return False
    except smtplib.SMTPException:
        print("Unable to send mail")
    except Exception as ex:
        print("Email sending failed", ex.message)
        return False


def verify_email_password(server_host, server_port, email_address, email_password):
    try:
        server_account = smtplib.SMTP_SSL(server_host, server_port)
        if server_account.login(email_address, email_password):
            return True
        else:
            return False
    except:
        return False


if __name__ == "__main__":

    warnings.filterwarnings(action='ignore', module='.*paramiko.*')

    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger('odvtt_tool')
    log_file = 'odvtt-log-' + datetime.now().strftime('%b-%d-%Y-%H%M' + '.log')  
    fh = logging.FileHandler(Path(log_file))
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", help="Specify all the information in JSON file. "
                                            "e.g Input File and SMTP Configuration for Email Notifications")
    args = parser.parse_args()
    # password = getpass.getpass("Enter email password (Password field will not be displayed): ")
    password = "Pakistan1"

    try:
        json_data = open(args.config_file).read()
    except IOError as e:
        print("I/O error ({0}) {1}".format(args.config_file, e.strerror))
        sys.exit()

    try:
        json_schema_file = open("schemas/JsonSchemaValidator.json").read()
    except ValueError:
        print('Decoding JSON has failed')
        sys.exit()

    # JSON Configuration & Schema File Comparison
    if validate_configuration_file(json_schema_file, json_data):
        with open(args.config_file) as f:
            data = json.load(f)
            logger.info("Configuration file validated successfully")
        # Validating Input File Data
        if verify_email_password(data['smtp_information']['smtp_server'], data['smtp_information']['smtp_port'],
                                 data['smtp_information']['email_address'], password):
            logger.info("Email verified")

            if pre_validate_file(data['input_file'], data['validator_path'], 'OperatorImportSchema.csvs'):
                logger.info("File transfer complete")
                print("Sending email..")

                send_email(data['smtp_information']['smtp_server'], data['smtp_information']['smtp_port'],
                           data['smtp_information']['email_address'], password,
                           data['email_to'], data['email_cc'], log_file)
                fh.close()
                os.remove(Path(log_file))
            else:
                    send_email(data['smtp_information']['smtp_server'], data['smtp_information']['smtp_port'],
                           data['smtp_information']['email_address'], password,
                           data['email_to'], data['email_cc'], log_file)
                    print("File Transfer Failed")
                    fh.close()
                    os.remove(Path(log_file))
                    sys.exit()
        else:
            print("Host/Email verification failed")
            fh.close()
            os.remove(Path(log_file))
            sys.exit()
