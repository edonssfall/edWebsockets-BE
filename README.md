# Django Channels Chat Application

This project is a Django Channels application that implements WebSocket-based chat functionality. It includes middleware
for automatic authentication using refresh tokens stored in cookies and a search function implemented with WebSocket.

## Features
- Django version: 5.0
- Django Channels version: 3.0.5
- WebSocket-based chat functionality
- Middleware for automatic authentication using refresh tokens stored in cookies
- Search function with WebSocket

## Installation
1. Clone the repository
    ```bash
    git clone https://github.com/edonssfall/edWebsockets-BE.git
    ```
2. Enter the project directory
    ```bash
    cd edWebsockets-BE
    ```
3. Copy the `.env.example` file and rename it to `.env`
    ```bash
    cp .env.example .env
    ```
4. Create a virtual environment
    ```bash
    python3 -m venv venv
    ```
5. Activate the virtual environment
    ```bash
    source venv/bin/activate
    ```
6. Install the dependencies
    ```bash
    pip install -r requirements.txt
    ```
7. Run the migrations
    ```bash
    python manage.py migrate
    ```

## Usage
1. Run the development server
    ```bash
    python manage.py runserver
    ```
2. Open the application in your browser
    ```
    http://localhost:8000
    ```
