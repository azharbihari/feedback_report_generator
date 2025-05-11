# Feedback Report Generator

A Django-based service that processes student event data to generate HTML and PDF reports asynchronously, stores them in a database, and provides endpoints to retrieve reports or check task status.

## Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Tech Stack](#tech-stack)
* [Project Structure](#project-structure)
* [API Endpoints](#api-endpoints)
* [Setup Instructions](#setup-instructions)
* [Usage Example](#usage-example)
* [Sample Payload](#sample-payload)
* [Architecture](#architecture)
* [Database Schema](#database-schema)
* [Monitoring](#monitoring)
* [Development](#development)
* [Tests](#tests)
* [Troubleshooting](#troubleshooting)
* [Contributing](#contributing)
* [Contact Information](#contact-information)
* [License](#license)

## Overview

This application processes student event data, sorts events by unit, assigns question aliases (Q1, Q2, etc.), and generates reports showing the order of units answered by students. The system uses Celery for asynchronous processing, Redis as the message broker, and PostgreSQL for storing reports.

## Features

* Asynchronous report generation using Celery
* Support for both HTML and PDF report formats
* Efficient storage of large report content using compression
* RESTful API endpoints for report generation and retrieval
* Task monitoring via Flower
* Containerized deployment using Docker Compose

## Tech Stack

* **Backend Framework**: Django with Django REST Framework (DRF)
* **Database**: PostgreSQL 16
* **Asynchronous Processing**: Celery
* **Message Broker**: Redis
* **Task Monitoring**: Flower
* **PDF Generation**: ReportLab
* **Package Management**: Poetry
* **Containerization**: Docker Compose

## Project Structure

```
.
├── Dockerfile
├── README.md
├── apps
│   ├── __init__.py
│   └── assignment
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── migrations
│       │   ├── 0001_initial.py
│       │   └── __init__.py
│       ├── models.py
│       ├── schemas.py
│       ├── serializers.py
│       ├── tasks.py
│       ├── tests.py
│       ├── urls.py
│       ├── utils.py
│       └── views.py
├── core
│   ├── __init__.py
│   ├── asgi.py
│   ├── celery.py
│   ├── settings.py
│   ├── templates
│   │   └── index.html
│   ├── urls.py
│   ├── views.py
│   └── wsgi.py
├── docker-compose.yml
├── dump.json           # Sample payload for testing
├── manage.py
├── poetry.lock
└── pyproject.toml
```

The project follows a modular structure:
- `apps/assignment/`: Contains the main application logic for report generation
- `core/`: Contains project-wide settings and configuration
- `dump.json`: Sample payload for testing the API

## API Endpoints

### Generate HTML Report

* **URL**: `/assignment/html`
* **Method**: POST
* **Input**: JSON payload containing student event data
* **Output**: Returns a task_id and status URL
* **Description**: Enqueues a task to process the payload asynchronously using Celery

### Check HTML Report Status

* **URL**: `/assignment/html/<task_id>`
* **Method**: GET
* **Output**: Returns the status of the task and report URLs if completed
* **Description**: Checks the task status and provides links to generated reports

### Generate PDF Report

* **URL**: `/assignment/pdf`
* **Method**: POST
* **Input**: Same JSON payload as for HTML reports
* **Output**: Returns a task_id and status URL
* **Description**: Enqueues a Celery task to generate a PDF report

### Check PDF Report Status

* **URL**: `/assignment/pdf/<task_id>`
* **Method**: GET
* **Output**: Returns the status of the task and report URLs if completed
* **Description**: Checks the task status and provides links to generated PDF reports

### View Report

* **URL**: `/assignment/reports/<task_id>/<report_id>`
* **Method**: GET
* **Output**: Returns the actual HTML or PDF report content
* **Description**: Retrieves and displays the generated report

## Sample Payload

The repository includes a `dump.json` file with sample student event data that can be used for testing the API. This file contains a comprehensive dataset with multiple students and their associated events across different units.

Example structure of the payload:

```json
[
  {
    "namespace": "ns_example",
    "student_id": "00a9a76518624b02b0ed57263606fc26",
    "events": [
      {
        "type": "saved_code",
        "created_time": "2024-07-21 03:04:55.939000+00:00",
        "unit": "17"
      },
      {
        "type": "submission",
        "created_time": "2024-07-21 03:06:53.025000+00:00",
        "unit": "17"
      }
      // Additional events...
    ]
  }
  // Additional students...
]
```

You can use this sample payload to test the report generation endpoints:

```bash
# Test HTML report generation
curl -X POST http://localhost:8000/assignment/html \
  -H "Content-Type: application/json" \
  -d @dump.json

# Test PDF report generation
curl -X POST http://localhost:8000/assignment/pdf \
  -H "Content-Type: application/json" \
  -d @dump.json
```

## Setup Instructions

### Prerequisites

* Docker and Docker Compose installed on your system

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/azharbihari/feedback_report_generator.git
   cd feedback_report_generator
   ```

2. Create a `.env` file in the project root with the following variables:

   ```
   # Database settings
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=db
   DB_PORT=5432

   # Celery settings
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0

   # Flower settings
   FLOWER_USER=admin
   FLOWER_PASSWORD=admin
   ```

3. Build and start the containers:

   ```bash
   docker compose up --build -d
   ```

4. The application should now be running at:

   * Django API: [http://localhost:8000/](http://localhost:8000/)
   * Flower dashboard: [http://localhost:5555/](http://localhost:5555/)

## Usage Example

### Generating a Report

1. Send a POST request to `/assignment/html` with the event data:

   ```json
   [
     {
       "namespace": "ns_example",
       "student_id": "00a9a76518624b02b0ed57263606fc26",
       "events": [
         {
           "type": "saved_code",
           "created_time": "2024-07-21 03:04:55.939000+00:00",
           "unit": 17
         },
         {
           "type": "submitted_code",
           "created_time": "2024-07-21 03:05:10.123000+00:00",
           "unit": 19
         }
       ]
     }
   ]
   ```

2. You'll receive a response with a task ID:

   ```json
   {
     "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
     "status": "PENDING",
     "status_url": "http://localhost:8000/assignment/html/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
   }
   ```

3. Check the status by visiting the provided URL or making a GET request to it.

4. Once completed, you'll receive links to the generated reports.

## Architecture

The application uses a modular architecture with:

* Django models for database schema
* Celery tasks for asynchronous processing
* Pydantic schemas for data validation
* Compression utilities for efficient storage
* Docker Compose for containerization

## Database Schema

* **ReportTask**: Tracks the status of report generation tasks
* **GeneratedReport**: Stores the compressed report content with appropriate indexes

## Monitoring

Access the Flower dashboard at [http://localhost:5555/](http://localhost:5555/) to monitor Celery tasks.

## Development

To run the project in development mode:

```bash
# Start all services
docker compose up

# Access Django shell
docker compose exec web python manage.py shell
```

## Tests

The application includes comprehensive unit tests to ensure the functionality of all components:

* **API Endpoint Tests**: Tests for all REST endpoints (HTML/PDF generation, status checks, report retrieval)
* **Task Processing Tests**: Tests for the asynchronous Celery task processing
* **Report Generation Tests**: Tests for HTML and PDF report generation logic

To run the tests:

```bash
# Run all tests
docker compose run --rm web python manage.py test

# Run with verbose output
docker compose run --rm web python manage.py test -v 2
```

## Troubleshooting

Common issues and their solutions:

* **Connection refused to Redis**: Ensure the Redis container is running with `docker compose ps`
* **Database migrations**: If you encounter database issues, try running migrations with `docker compose exec web python manage.py migrate`
* **Permission issues**: If you encounter permission issues with Docker volumes, check the ownership of the project directory

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Contact Information

* **Developer**: Azhar Bihari
* **Email**: azharbihari@outlook.com
* **GitHub**: [github.com/azharbihari](https://github.com/azharbihari)
* **LinkedIn**: [linkedin.com/in/azharbihari](https://linkedin.com/in/azharbihari)

<!-- ## License

This project is licensed under the MIT License - see the LICENSE file for details. -->
