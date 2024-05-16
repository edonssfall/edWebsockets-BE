from middlewares.middleware_helpers import create_user_async, get_user_async, receive_user, check_response, \
    get_user
from channels.testing import WebsocketCommunicator, ChannelsLiveServerTestCase
from .utils import create_or_get_room, save_message, get_status
from middlewares.websocket_auth import TokenAuthMiddleware
from .consumers import ConnectionConsumer, ChatConsumer
from unittest.mock import patch, Mock, AsyncMock
from django.contrib.auth import get_user_model
from datetime import datetime

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

    @patch('middlewares.middleware_helpers.requests.get')
    def test_receive_user(self, mock_requests_get) -> None:
        """
        Test the receive_user function
        """
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

    async def test_create_user_async(self) -> None:
        """
        Test the create_user_async function
        """
        # Create a user and check if it matches the expected values
        user = await create_user_async(self.username, self.email)
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.email, self.email)
        self.assertTrue(user.is_active)

    async def test_get_user_async(self) -> None:
        """
        Test the get_user_async function
        """
        # Create a user, then fetch it and check if it matches the expected values
        await create_user_async(self.username, self.email)
        user = await get_user_async(self.email)
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.email, self.email)
        self.assertTrue(user.is_active)

    async def test_valid_response(self) -> None:
        """
        Test the check_response function with a valid response (status code 200)
        """
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.return_value = {'access': 'access_token', 'refresh': 'refresh_token'}

        result = await check_response(response_mock)
        self.assertEqual(result, {'access': 'access_token', 'refresh': 'refresh_token'})

    async def test_invalid_response(self) -> None:
        """
        Test the check_response function with an invalid response (status code 401)
        """
        response_mock = Mock()
        response_mock.status_code = 401

        # Check if an exception is raised
        with self.assertRaises(Exception):
            await check_response(response_mock)

    async def test_get_user_create(self) -> None:
        """
        Test the get_or_create_user function when creating a new user
        """
        # Set up the scope with session data
        await create_user_async(self.username, self.email)
        scope = await get_user(self.session_data, self.scope)

        # Check if the user was created and matches the expected values
        self.assertEqual(scope['user'].email, self.email)
        self.assertEqual(scope['user'].username, self.username)
        self.assertEqual(scope['cookies']['access'], self.session_data['access'])
        self.assertEqual(scope['cookies']['refresh'], self.session_data['refresh'])

    async def test_get_user_create_invalid(self) -> None:
        """
        Test get_user function when the user does not exist
        """
        with self.assertRaises(Exception):
            await get_user(self.session_data, self.scope)

    async def test_get_or_create_user_exists(self) -> None:
        # Test the get_or_create_user function when the user already exists
        # Create a user
        user = await create_user_async(self.username, self.email)

        # Set up the scope with session data
        scope = await get_user(self.session_data, self.scope)

        # Check if the existing user matches the expected values
        self.assertEqual(scope['user'], user)
        self.assertEqual(scope['cookies']['access'], self.session_data['access'])
        self.assertEqual(scope['cookies']['refresh'], self.session_data['refresh'])

    @patch('middlewares.middleware_helpers.requests.get')
    async def test_websocket_auth_middleware_positive(self, mock_requests_get) -> None:
        # Test the TokenAuthMiddleware with a positive response (status code 200)
        # Set up the mock to return a positive response
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = self.session_data
        await create_user_async(self.username, self.email)

        # Set up the scope with access and refresh tokens
        self.scope['cookies']['access'] = 'access_token'
        self.scope['cookies']['refresh'] = 'refresh_token'

        # Create an instance of the middleware
        middleware = TokenAuthMiddleware(AsyncMock())

        # Call the middleware
        await middleware(self.scope, None, None)

        # Check if the user data and tokens were updated in the scope
        self.assertEqual(self.scope['user'].email, self.email)
        self.assertEqual(self.scope['cookies']['access'], self.session_data['access'])
        self.assertEqual(self.scope['cookies']['refresh'], self.session_data['refresh'])
        self.assertEqual(self.scope['user'].username, self.username)

    @patch('middlewares.middleware_helpers.requests.get')
    @patch('middlewares.middleware_helpers.requests.post')
    async def test_websocket_auth_middleware_without_access_positive(self, mock_requests_get,
                                                                     mock_requests_post) -> None:
        """
        Test TokenAuthMiddleware with positive response when access token is missing but refresh token is present
        """
        # Mock positive responses for both GET and POST requests
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = self.session_data
        mock_requests_post.return_value.status_code = 200
        mock_requests_post.return_value.json.return_value = self.session_data

        await create_user_async(self.username, self.email)

        # Set up the scope with refresh token but without access token
        self.scope['cookies']['refresh'] = 'refresh_token'

        # Create an instance of the middleware
        middleware = TokenAuthMiddleware(AsyncMock())

        # Call the middleware
        await middleware(self.scope, None, None)

        # Check if the user data and tokens were updated in the scope
        self.assertEqual(self.scope['user'].email, self.email)
        self.assertEqual(self.scope['cookies']['access'], self.session_data['access'])
        self.assertEqual(self.scope['cookies']['refresh'], self.session_data['refresh'])
        self.assertEqual(self.scope['user'].username, self.username)

    @patch('middlewares.middleware_helpers.requests.get')
    async def test_websocket_auth_middleware_negative(self, mock_requests_get) -> None:
        """
        Test TokenAuthMiddleware with negative response when access token is missing
        """
        # Mock a negative response for the GET request
        mock_requests_get.return_value.status_code = 401

        # Set up the scope without an access token
        self.scope['cookies']['access'] = ''

        # Create an instance of the middleware
        middleware = TokenAuthMiddleware(AsyncMock())

        # Call the middleware and check if an exception is raised
        with self.assertRaises(Exception):
            await middleware(self.scope, None, None)

    @patch('middlewares.middleware_helpers.requests.get')
    @patch('middlewares.middleware_helpers.requests.post')
    async def test_websocket_auth_middleware_without_access_negative(self, mock_requests_get,
                                                                     mock_requests_post) -> None:
        """
        Test TokenAuthMiddleware with negative response when both access and refresh tokens are missing
        """
        # Mock negative responses for both GET and POST requests
        mock_requests_get.return_value.status_code = 401
        mock_requests_post.return_value.status_code = 200

        # Create an instance of the middleware
        middleware = TokenAuthMiddleware(AsyncMock())

        # Call the middleware and check if an exception is raised
        with self.assertRaises(Exception):
            await middleware(self.scope, None, None)


class TestsConnectionWebsocket(ChannelsLiveServerTestCase):
    async def initialize_user(self) -> None:
        """
        Helper method to initialize a user for testing.
        """
        # Create a test user and set the URL for the websocket connection
        self.user = await create_user_async('testuser', 'test@test.com')
        await create_user_async('testuser2', 'test2@test.com')
        await create_or_get_room(self.user)
        self.url = f'/ws/{self.user.username}'

    async def test_connection(self) -> None:
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
        status = await get_status(self.user)
        self.assertTrue(status.online)

        # Disconnect from the websocket
        await communicator.send_json_to({'search_query': 'testuser2'})

        # Check if the status is offline after disconnecting
        response = await communicator.receive_json_from()
        self.assertIn('users', response)

        # Check if status is offline after disconnect
        await communicator.disconnect()

        # Check if the status is offline after disconnecting
        status = await get_status(self.user)
        self.assertFalse(status.online)


class TestsChatConsumer(ChannelsLiveServerTestCase):
    def setUp(self):
        self.room = 'test-room'

        self.username = 'testuser'
        self.email = 'test@example.com'

        self.username2 = 'testuser2'
        self.email2 = 'test2@example.com'

        self.content = 'Test message'
        self.timestamp = datetime.now()

    def check_timestamp(self, response_data: dict) -> None:
        """
        Helper method to check if the timestamp matches the expected value.
        """
        timestamp_from_response = datetime.strptime(response_data['timestamp'], '%Y-%m-%d %H:%M:%S')

        # Compare the relevant components
        self.assertEqual(
            (timestamp_from_response.year, timestamp_from_response.month, timestamp_from_response.day,
             timestamp_from_response.hour, timestamp_from_response.minute, timestamp_from_response.second),
            (self.timestamp.year, self.timestamp.month, self.timestamp.day,
             self.timestamp.hour, self.timestamp.minute, self.timestamp.second)
        )

    async def initialize_user(self) -> None:
        """
        Helper method to initialize a user for testing.
        """
        # Create a test user and set the URL for the websocket connection
        self.user = await create_user_async(self.username, self.email)
        self.url = f'/ws/{self.user.username}'

        # Create a second test user
        self.user2 = await create_user_async(self.username2, self.email2)

    async def simulate_connection(self) -> WebsocketCommunicator:
        """
        Simulate a WebSocket connection for testing.
        """
        # Create a websocket communicator for the ConnectionConsumer
        communicator = WebsocketCommunicator(ConnectionConsumer.as_asgi(), self.url)

        # Set access and refresh tokens in the scope
        access_token = 'access_token_value'
        refresh_token = 'refresh_token_value'
        communicator.scope['cookies'] = {'access': access_token, 'refresh': refresh_token}
        communicator.scope['user'] = self.user

        # Connect to the websocket consumer
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        return communicator

    async def test_create_room(self) -> None:
        """
        Test creating a chat room.
        """
        # Initialize a test user
        await self.initialize_user()

        # Simulate WebSocket connection
        communicator = await self.simulate_connection()

        # Receive initial data from the WebSocket connection
        await communicator.receive_json_from()
        await communicator.receive_json_from()

        # Send a message to create a room with another user
        await communicator.send_json_to({'chat': 'testuser2'})

        # Receive response containing room UUID
        response = await communicator.receive_json_from()
        self.assertIn('room_uuid', response)

        # Extract room UUID from the response
        room_uuid = response['room_uuid']

        # Save a message in the chat room
        await save_message(room_uuid, {'content': self.content, 'sender': self.username, 'timestamp': self.timestamp})

        # Connect to the chat room WebSocket endpoint
        communicator_chat = WebsocketCommunicator(ChatConsumer.as_asgi(), f'/ws/chat/{room_uuid}')
        await communicator_chat.connect()

        # Receive message from the chat room
        response = await communicator_chat.receive_json_from()
        self.assertIn('messages', response)

        # Check if the received message matches the send message
        response_data = response['messages'][0]
        self.assertEqual(response_data['content'], self.content)
        self.assertEqual(response_data['sender'], self.username)
        self.check_timestamp(response_data)

    async def test_send_message(self) -> None:
        """
        Test sending a message in a chat room.
        """
        # Initialize the user for testing
        await self.initialize_user()

        # Create chat rooms for both users
        await create_or_get_room(self.user)
        await create_or_get_room(self.user2)

        # Simulate a WebSocket connection
        communicator = await self.simulate_connection()

        # Receive initial data from the WebSocket connection
        await communicator.receive_json_from()
        response = await communicator.receive_json_from()
        self.assertIn('chats', response)

        # Extract room UUID from the response data
        response_data = response['chats'][0]
        room_uuid = response_data['uuid']

        # Save a message in the chat room
        await save_message(room_uuid, {'content': self.content, 'sender': self.username, 'timestamp': self.timestamp})

        # Connect to the chat room WebSocket endpoint
        communicator_chat = WebsocketCommunicator(ChatConsumer.as_asgi(), f'/ws/chat/{room_uuid}')
        connected, _ = await communicator_chat.connect()
        self.assertTrue(connected)

        # Receive message from the chat room
        response = await communicator_chat.receive_json_from()
        self.assertIn('messages', response)

        # Check if the received message matches the send message
        response_data = response['messages'][0]
        self.assertEqual(response_data['content'], self.content)
        self.assertEqual(response_data['sender'], self.username)
        self.check_timestamp(response_data)
