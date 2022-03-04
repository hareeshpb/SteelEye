import configparser
from fileinput import filename
from tabnanny import filename_only
from urllib import response
import requests
import xml.etree.ElementTree as ET
from lxml import etree
import xmltodict
import pandas as pd
from io import BytesIO
from zipfile import ZipFile
import os

config = configparser.RawConfigParser()
config.read('config.ini')


def download_xml(url: str, filename: str) -> bool:
    resp = requests.get(url)
    os.remove(filename)
    with open(filename, 'wb') as f:
        f.write(resp.content)
    return True


def handle_zip(url: str) -> bool:
    print(url)
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
    # for x in range(len(xml_dict)):
    vars = config['Inputs']['Path3']
    vars = vars.split(',',)
    for var in vars:
        _var = var.split('.',)
        if(len(_var) == 2):
            print(var, ':', xml_dict[0]['TermntdRcrd'][_var[0]][_var[1]])
        elif(len(_var) == 1):
            print(var, ':', xml_dict[0]['TermntdRcrd'][_var[0]])


def orchestrator():
    xpath = config['Inputs']['xpath1']
    link_position = int(config['Inputs']['link_position'])
    link_type = config['Inputs']['link_type']
    dl_link = xml_parse_link(filename='input.xml', xpath=xpath,
                             link_position=link_position, link_type=link_type)
    handle_zip(dl_link)
    filename = latest_file(path='./dl')
    print(filename)
    xpath = config['Inputs']['xpath2']
    xml_to_csv(filename='./dl/'+filename, xpath=xpath)


orchestrator()
