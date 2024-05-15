from middlewares.middleware_helpers import create_user_async, get_user_async, receive_user, check_response, \
    get_or_create_user
from channels.testing import WebsocketCommunicator, ChannelsLiveServerTestCase
from middlewares.websocket_auth import TokenAuthMiddleware
from unittest.mock import patch, Mock, AsyncMock
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .consumers import ConnectionConsumer
from .utils import create_or_get_room
from .models import Status

User = get_user_model()


class TestsMiddlewareHelpers(ChannelsLiveServerTestCase):
    def setUp(self):
        # Set up common variables for test cases
        self.username = 'testuser'
        self.email = 'test@test.com'
        self.session_data = {
            'user': {
                'email': self.email,
            },
            'access': 'access_token',
            'refresh': 'refresh_token',
        }
        self.scope = {
            'url_route': {
                'kwargs': {
                    'username': self.username,
                }
            },
            'cookies': {
                'access': '',
                'refresh': '',
            }
        }

    @staticmethod
    async def mock_middleware(scope, receive, send):
        # Mock middleware function for testing purposes
        return AsyncMock()

    @patch('middlewares.middleware_helpers.requests.get')
    def test_receive_user(self, mock_requests_get):
        # Test the receive_user function
        mocked_response = {
            'username': 'testuser',
            'email': 'test@test.com',
        }

        # Set up the mock to return a mocked response
        mock_requests_get.return_value.json.return_value = mocked_response

        # Call the function
        host = 'http://example.com'
        token = {'access': 'access_token'}
        response = receive_user(host, token)

        # Check if the requests.get method was called with the correct arguments
        mock_requests_get.assert_called_once_with(
            f'{host}/own-profile',
            headers={'Authorization': f'Bearer {token["access"]}'},
        )

        # Check if the response matches the mocked response
        self.assertEqual(response.json.return_value, mocked_response)

    async def test_create_user_async(self):
        # Test the create_user_async function
        # Create a user and check if it matches the expected values
        user = await create_user_async(self.username, self.email)
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.email, self.email)
        self.assertTrue(user.is_active)

    async def test_get_user_async(self):
        # Test the get_user_async function
        # Create a user, then fetch it and check if it matches the expected values
        await create_user_async(self.username, self.email)
        user = await get_user_async(self.email)
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.email, self.email)
        self.assertTrue(user.is_active)

    async def test_valid_response(self):
        # Test the check_response function with a valid response (status code 200)
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.return_value = {'access': 'access_token', 'refresh': 'refresh_token'}

        result = await check_response(response_mock)
        self.assertEqual(result, {'access': 'access_token', 'refresh': 'refresh_token'})

    async def test_invalid_response(self):
        # Test the check_response function with an invalid response (status code 401)
        response_mock = Mock()
        response_mock.status_code = 401

        # Check if an exception is raised
        with self.assertRaises(Exception):
            await check_response(response_mock)

    async def test_get_or_create_user_create(self):
        # Test the get_or_create_user function when creating a new user
        # Set up the scope with session data
        scope = await get_or_create_user(self.session_data, self.scope)

        # Check if the user was created and matches the expected values
        self.assertEqual(scope['user'].email, self.email)
        self.assertEqual(scope['user'].username, self.username)
        self.assertEqual(scope['cookies']['access'], self.session_data['access'])
        self.assertEqual(scope['cookies']['refresh'], self.session_data['refresh'])

    async def test_get_or_create_user_exists(self):
        # Test the get_or_create_user function when the user already exists
        # Create a user
        user = await create_user_async(self.username, self.email)

        # Set up the scope with session data
        scope = await get_or_create_user(self.session_data, self.scope)

        # Check if the existing user matches the expected values
        self.assertEqual(scope['user'], user)
        self.assertEqual(scope['cookies']['access'], self.session_data['access'])
        self.assertEqual(scope['cookies']['refresh'], self.session_data['refresh'])

    @patch('middlewares.middleware_helpers.requests.get')
    async def test_websocket_auth_middleware_positive(self, mock_requests_get):
        # Test the TokenAuthMiddleware with a positive response (status code 200)
        # Set up the mock to return a positive response
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = self.session_data

        # Set up the scope with access and refresh tokens
        self.scope['cookies']['access'] = 'access_token'
        self.scope['cookies']['refresh'] = 'refresh_token'

        # Create an instance of the middleware
        middleware = TokenAuthMiddleware(await self.mock_middleware(self.scope, None, None))

        # Call the middleware
        await middleware(self.scope, None, None)

        # Check if the user data and tokens were updated in the scope
        self.assertEqual(self.scope['user'].email, self.email)
        self.assertEqual(self.scope['cookies']['access'], self.session_data['access'])
        self.assertEqual(self.scope['cookies']['refresh'], self.session_data['refresh'])
        self.assertEqual(self.scope['user'].username, self.username)

    @patch('middlewares.middleware_helpers.requests.get')
    @patch('middlewares.middleware_helpers.requests.post')
    async def test_websocket_auth_middleware_without_access_positive(self, mock_requests_get, mock_requests_post):
        """
        Test TokenAuthMiddleware with positive response when access token is missing but refresh token is present
        """
        # Mock positive responses for both GET and POST requests
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = self.session_data
        mock_requests_post.return_value.status_code = 200
        mock_requests_post.return_value.json.return_value = self.session_data

        # Set up the scope with refresh token but without access token
        self.scope['cookies']['refresh'] = 'refresh_token'

        # Create an instance of the middleware
        middleware = TokenAuthMiddleware(await self.mock_middleware(self.scope, None, None))

        # Call the middleware
        await middleware(self.scope, None, None)

        # Check if the user data and tokens were updated in the scope
        self.assertEqual(self.scope['user'].email, self.email)
        self.assertEqual(self.scope['cookies']['access'], self.session_data['access'])
        self.assertEqual(self.scope['cookies']['refresh'], self.session_data['refresh'])
        self.assertEqual(self.scope['user'].username, self.username)

    @patch('middlewares.middleware_helpers.requests.get')
    async def test_websocket_auth_middleware_negative(self, mock_requests_get):
        """
        Test TokenAuthMiddleware with negative response when access token is missing
        """
        # Mock a negative response for the GET request
        mock_requests_get.return_value.status_code = 401

        # Set up the scope without an access token
        self.scope['cookies']['access'] = ''

        # Create an instance of the middleware
        middleware = TokenAuthMiddleware(await self.mock_middleware(self.scope, None, None))

        # Call the middleware and check if an exception is raised
        with self.assertRaises(Exception):
            await middleware(self.scope, None, None)

    @patch('middlewares.middleware_helpers.requests.get')
    @patch('middlewares.middleware_helpers.requests.post')
    async def test_websocket_auth_middleware_without_access_negative(self, mock_requests_get, mock_requests_post):
        """
        Test TokenAuthMiddleware with negative response when both access and refresh tokens are missing
        """
        # Mock negative responses for both GET and POST requests
        mock_requests_get.return_value.status_code = 401
        mock_requests_post.return_value.status_code = 401

        # Create an instance of the middleware
        middleware = TokenAuthMiddleware(await self.mock_middleware(self.scope, None, None))

        # Call the middleware and check if an exception is raised
        with self.assertRaises(Exception):
            await middleware(self.scope, None, None)


class ConnectionWebsocketTests(ChannelsLiveServerTestCase):

    def setUp(self):
        self.room = 'test-room'

    async def initialize_user(self):
        """
        Helper method to initialize a user for testing.
        """
        # Create a test user and set the URL for the websocket connection
        self.user = await create_user_async('testuser', 'test@test.com')
        self.room = await create_or_get_room(self.user)
        self.url = f'/ws/{self.user.username}'

    @database_sync_to_async
    def get_status(self):
        """
        Helper method to get the status of the user.
        """
        return Status.objects.get(user=self.user)

    async def test_connection(self):
        """
        Test establishing a websocket connection and sending tokens.
        """
        # Initialize a test user
        await self.initialize_user()

        # Create a websocket communicator for the ConnectionConsumer
        communicator = WebsocketCommunicator(ConnectionConsumer.as_asgi(), self.url)

        # Simulate sending tokens from the authentication service
        access_token = 'access_token_value'
        refresh_token = 'refresh_token_value'
        communicator.scope['cookies'] = {'access': access_token, 'refresh': refresh_token}
        communicator.scope['user'] = self.user

        # Connect to the websocket consumer
        connected, _ = await communicator.connect()

        # Send tokens as JSON to the consumer
        await communicator.send_json_to({'access': access_token, 'refresh': refresh_token})

        # Receive a JSON response from the consumer
        response = await communicator.receive_json_from()

        # Check if the response contains both access and refresh tokens
        self.assertIn('access', response)
        self.assertIn('refresh', response)

        # Receive chats
        response = await communicator.receive_json_from()
        self.assertIn('chats', response)

        # Check if the connection was successful and status created in the database with online status
        status = await self.get_status()
        self.assertTrue(status.online)



        # Check if status is offline after disconnect
        await communicator.disconnect()

        # Check if the status is offline after disconnecting
        status = await self.get_status()
        self.assertFalse(status.online)
