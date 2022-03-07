import unittest
import mock
import app
import requests
from moto import mock_s3
import os


class TestApp(unittest.TestCase):
    def setUp(self):
        self.url = "http://test.url"
        self.filename = "test.xml"

    def tearDown(self):
        if (os.path.isfile(self.filename)):
            os.remove(self.filename)

    @mock.patch('requests.get')
    def test_download_xml(self, download):
        download.return_value.content = b'<Test>Test</Test>'
        self.assertEqual(app.download_xml(self.url, self.filename), True)

    def test_handle_zip(self):
        pass

    def test_xml_parse_link(self):
        pass

    def test_latest_file(self):
        pass

    def test_xml_to_dict(self):
        pass

    def test_csv_writer(self):
        pass

    def test_uploadtos3(self):

        pass


if __name__ == '__main__':
    unittest.main()
