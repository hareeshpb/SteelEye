import unittest
from unittest.mock import mock_open
import mock
import app
import requests
import boto3
from moto import mock_s3
import os


@mock_s3
class TestApp(unittest.TestCase):
    def setUp(self):
        self.url = "http://test.url"
        self.filename = "test.xml"
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="fulfil-hareesh")

    def tearDown(self):
        if (os.path.isfile(self.filename)):
            os.remove(self.filename)

    @mock.patch('requests.get')
    def test_download_xml(self, download):
        download.return_value.content = b'<Test>Test</Test>'
        self.assertEqual(app.download_xml(self.url, self.filename), True)

    def test_xml_parse_link(self):
        pass

    def test_handle_zip(self):
        pass

    def test_latest_file(self):
        pass

    def test_xml_to_dict(self):
        pass

    def test_csv_writer(self):
        pass

    def test_uploadtos3(self):
        self.assertEqual(app.uploadtos3(), True)


if __name__ == '__main__':
    unittest.main()
