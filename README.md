# Feedback Report Generator

A Django-based service that processes student event data to generate HTML and PDF reports asynchronously, stores them in a database, and provides endpoints to retrieve reports or check task status.

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
   docker-compose up -d
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
docker-compose up

# Access Django shell
docker-compose exec web python manage.py shell
```

## Tests

The application includes comprehensive unit tests to ensure the functionality of all components:

* **API Endpoint Tests**: Tests for all REST endpoints (HTML/PDF generation, status checks, report retrieval)
* **Task Processing Tests**: Tests for the asynchronous Celery task processing
* **Report Generation Tests**: Tests for HTML and PDF report generation logic

To run the tests:

```bash
# Run all tests
docker-compose run --rm web python manage.py test

# Run specific test module
docker-compose run --rm web python manage.py test apps.assignment.tests

# Run with verbose output
docker-compose run --rm web python manage.py test -v 2
```

## Django Admin Interface

To access the Django admin interface for monitoring tasks and reports:

1. Create a superuser:

```bash
docker-compose exec web python manage.py createsuperuser
```

2. Follow the prompts to set up username, email, and password

3. Access the admin interface at: [http://localhost:8000/admin/](http://localhost:8000/admin/)

4. Login with the superuser credentials created in step 1

5. From the admin interface, you can:

   * Monitor report generation tasks and their status
   * View and manage generated reports
   * Check error messages for failed tasks

## License

[Specify your license here]
