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

config = configparser.RawConfigParser()
config.read('config.ini')


def download_xml(url: str, filename: str) -> bool:
    resp = requests.get(url)
    os.remove(filename)
    with open(filename, 'wb') as f:
        f.write(resp.content)
    return True


def handle_zip(url: str) -> bool:
    resp = requests.get(url)
    zipfile = ZipFile(BytesIO(resp.content))
    zipfile.extractall('./dl')
    return True


def xml_parse_link(filename: str, xpath: str, link_type: str, link_position: int) -> str:
    tree = ET.parse(filename)
    root = tree.getroot()
    for child in root.find(xpath):
        if(child.attrib['name'] == 'download_link'):
            download_link = child.text
        elif(child.attrib['name'] == 'file_type' and child.text == link_type):
            return download_link


def latest_file(path: str) -> str:
    files = os.listdir(path)
    paths = [os.path.join(path, basename) for basename in files]
    max_paths = max(paths, key=os.path.getctime)
    for file in files:
        if file in max_paths:
            return file


def xml_to_csv(filename: str, xpath: str) -> bool:
    with open(filename, 'r', encoding='utf-8') as file:
        my_xml = file.read()
    xml_dict = xmltodict.parse(my_xml)
    keys = config['Inputs']['Path2']
    keys = keys.split(',',)
    for key in keys:
        xml_dict = xml_dict[key]
    for x in range(len(xml_dict)):
        fixed_path = config['Inputs']['Path3']
        vars = config['Inputs']['Path4']
        vars = vars.split(',',)
        dict = {}
        for var in vars:
            _var = var.split('.',)
            if(len(_var) == 2):
                dict[var] = xml_dict[0][fixed_path][_var[0]][_var[1]]
            elif(len(_var) == 1):
                dict[var] = xml_dict[0][fixed_path][_var[0]]
        csv_writer(dict)


def csv_writer(row: dict):
    file_exists = os.path.isfile('CSVFILE.csv')
    headersCSV = config['Inputs']['Path4']
    headersCSV = headersCSV.split(',',)
    with open('CSVFILE.csv', 'a', newline='') as f_object:
        dictwriter_object = DictWriter(f_object, fieldnames=headersCSV)
        if not file_exists:
            dictwriter_object.writeheader()
        dictwriter_object.writerow(row)


def uploadtos3() -> bool:
    S3_ACCESS_KEY = config['AWS']['AccessKey']
    S3_SECRET_KEY = config['AWS']['SecretKey']
    BUCKET_NAME = config['AWS']['BucketName']
    s3 = boto3.client('s3', aws_access_key_id=S3_ACCESS_KEY,
                      aws_secret_access_key=S3_SECRET_KEY)
    try:
        s3.upload_file('CSVFILE.csv', BUCKET_NAME, 'CSVFILE.csv')
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False


def orchestrator():
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
    xml_to_csv(filename='./dl/'+filename, xpath=xpath)
    uploadtos3()


orchestrator()
