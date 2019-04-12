import sys

from asgiref.sync import async_to_sync
from asgiref.testing import ApplicationCommunicator

from django.core.asgi import get_asgi_application
from django.core.signals import request_started
from django.db import close_old_connections
from django.test import SimpleTestCase, override_settings

from .urls import test_filename


@override_settings(ROOT_URLCONF='asgi.urls')
class ASGITest(SimpleTestCase):

    def setUp(self):
        request_started.disconnect(close_old_connections)

    def _get_scope(self, **kwargs):
        return {
            'type': 'http',
            'asgi': {'version': '3.0', 'spec_version': '2.1'},
            'http_version': '1.1',
            'method': 'GET',
            'query_string': b'',
            'server': ('testserver', 80),
            **kwargs,
        }

    def tearDown(self):
        request_started.connect(close_old_connections)

    @async_to_sync
    async def test_get_asgi_application(self):
        """
        get_asgi_application() returns a functioning ASGI callable.
        """
        application = get_asgi_application()
        # Construct HTTP request.
        communicator = ApplicationCommunicator(application, self._get_scope(path='/'))
        await communicator.send_input({'type': 'http.request'})
        # Read the response.
        response_start = await communicator.receive_output()
        self.assertEqual(response_start['type'], 'http.response.start')
        self.assertEqual(response_start['status'], 200)
        self.assertEqual(
            set(response_start['headers']),
            {
                (b'Content-Length', b'12'),
                (b'Content-Type', b'text/html; charset=utf-8'),
            },
        )
        response_body = await communicator.receive_output()
        self.assertEqual(response_body['type'], 'http.response.body')
        self.assertEqual(response_body['body'], b'Hello World!')

    @async_to_sync
    async def test_file_response(self):
        """
        Makes sure that FileResponse works over ASGI.
        """
        application = get_asgi_application()
        # Construct HTTP request.
        communicator = ApplicationCommunicator(application, self._get_scope(path='/file/'))
        await communicator.send_input({'type': 'http.request'})
        # Get the file content.
        with open(test_filename, 'rb') as test_file:
            test_file_contents = test_file.read()
        # Read the response.
        response_start = await communicator.receive_output()
        self.assertEqual(response_start['type'], 'http.response.start')
        self.assertEqual(response_start['status'], 200)
        self.assertEqual(
            set(response_start['headers']),
            {
                (b'Content-Length', str(len(test_file_contents)).encode('ascii')),
                (b'Content-Type', b'text/plain' if sys.platform.startswith('win') else b'text/x-python'),
                (b'Content-Disposition', b'inline; filename="urls.py"'),
            },
        )
        response_body = await communicator.receive_output()
        self.assertEqual(response_body['type'], 'http.response.body')
        self.assertEqual(response_body['body'], test_file_contents)