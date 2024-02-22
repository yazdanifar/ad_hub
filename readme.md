# Ad-Hub Project

## Setup


1. Create a virtual environment and activate it:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Setup a PostgreSQL database with the following credentials:

   ```
   username: postgres
   password: postgres
   database: ad_hub
   ```

## Running the Server

To start the application, run:

```bash
python main.py
```

The server will start running on `http://localhost:8000`.

## Testing

To run unit tests, use Pytest:

```bash
pytest
```

## API Documentation

You can access the Swagger documentation for the API at `http://localhost:8000/docs`. This provides an interactive interface to explore and test the API endpoints.

