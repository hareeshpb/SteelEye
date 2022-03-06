import configparser
import requests
import xml.etree.ElementTree as ET
import xmltodict
from io import BytesIO
from zipfile import ZipFile
import os
from csv import DictWriter
import boto3
from botocore.exceptions import NoCredentialsError
from app_logger import ErrorLogger, EventLogger

# Variable data written in Configuration File
config = configparser.RawConfigParser()
config.read('config.ini')


def download_xml(url: str, filename: str) -> None:
    try:
        resp = requests.get(url)
    except requests.HTTPError as exception:
        ErrorLogger(exception)
    os.remove(filename)
    try:
        with open(filename, 'wb') as f:
            f.write(resp.content)
    except IOError as exception:
        ErrorLogger(exception)


def handle_zip(url: str) -> None:
    try:
        resp = requests.get(url)
    except requests.HTTPError as exception:
        ErrorLogger(exception)
    try:
        zipfile = ZipFile(BytesIO(resp.content))
        zipfile.extractall('./dl')
    except IOError as exception:
        ErrorLogger(exception)

# The xpath is read from config


def xml_parse_link(filename: str, xpath: str, link_type: str, link_position: int) -> str:
    try:
        tree = ET.parse(filename)
    except ET.ParseError as exception:
        ErrorLogger(exception)
    root = tree.getroot()
    for child in root.find(xpath):
        if(child.attrib['name'] == 'download_link'):
            download_link = child.text
        elif(child.attrib['name'] == 'file_type' and child.text == link_type):
            return download_link

# This funtion ensures the latest downloaded file is taken up for
# processing, even though the file is destroyed after processing


def latest_file(path: str) -> str:
    try:
        files = os.listdir(path)
    except IOError as exception:
        ErrorLogger(exception)
    paths = [os.path.join(path, basename) for basename in files]
    max_paths = max(paths, key=os.path.getctime)
    for file in files:
        if file in max_paths:
            return file

# The required keys for dict are read from configuration files.
# Path2 -> The nested keys in order before looping through enteries
# Path3 -> The fixed path after that. ie. [0].Path3, [1].Path3
# Path4 -> The variable paths post Path3


def xml_to_dict(filename: str, xpath: str) -> bool:
    with open(filename, 'r', encoding='utf-8') as file:
        my_xml = file.read()
    xml_dict = xmltodict.parse(my_xml)
    keys = config['Inputs']['Path2']
    keys = keys.split(',',)
    for key in keys:
        xml_dict = xml_dict[key]
    for x in range(len(xml_dict)):
        fixed_paths = config['Inputs']['Path3']
        fixed_paths = fixed_paths.split(',',)
        vars = config['Inputs']['Path4']
        vars = vars.split(',',)
        dict = {}

        def fetch_element(n):
            nonlocal dict
            if(len(_var) == 2):
                dict[var] = xml_dict[x][fixed_paths[n]][_var[0]][_var[1]]
            elif(len(_var) == 1):
                dict[var] = xml_dict[0][fixed_paths[n]][_var[0]]
        for var in vars:
            _var = var.split('.',)
            for n in range(len(fixed_paths)):
                try:
                    fetch_element(n)
                except:
                    pass
        if(dict is None):
            print(x, xml_dict[x])
        csv_writer(row=dict)


def csv_writer(row: dict) -> None:
    file_exists = os.path.isfile('CSVFILE.csv')
    headersCSV = config['Inputs']['Path4']
    headersCSV = headersCSV.split(',',)
    with open('CSVFILE.csv', 'a', newline='') as f_object:
        dictwriter_object = DictWriter(f_object, fieldnames=headersCSV)
        if not file_exists:
            dictwriter_object.writeheader()
        dictwriter_object.writerow(row)


def uploadtos3() -> None:
    S3_ACCESS_KEY = config['AWS']['AccessKey']
    S3_SECRET_KEY = config['AWS']['SecretKey']
    BUCKET_NAME = config['AWS']['BucketName']
    s3 = boto3.client('s3', aws_access_key_id=S3_ACCESS_KEY,
                      aws_secret_access_key=S3_SECRET_KEY)
    try:
        s3.upload_file('CSVFILE.csv', BUCKET_NAME, 'CSVFILE.csv')
        EventLogger("Upload Successful")
    except FileNotFoundError:
        ErrorLogger("The file was not found")
    except NoCredentialsError:
        ErrorLogger("Credentials not available")


def orchestrator() -> None:
    url = config['Inputs']['url']
    download_xml(url=url, filename='input.xml')
    xpath = config['Inputs']['xpath1']
    link_position = int(config['Inputs']['link_position'])
    link_type = config['Inputs']['link_type']
    dl_link = xml_parse_link(filename='input.xml', xpath=xpath,
                             link_position=link_position, link_type=link_type)
    handle_zip(dl_link)
    filename = latest_file(path='./dl')
    if(os.path.isfile('CSVFILE.csv')):
        os.remove('CSVFILE.csv')
    xpath = config['Inputs']['xpath2']
    xml_to_dict(filename='./dl/'+filename, xpath=xpath)
    uploadtos3()


if __name__ == '__main__':
    orchestrator()
