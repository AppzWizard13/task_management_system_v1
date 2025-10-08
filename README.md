# Django Task Management System

A Django-based task management system with Docker, PostgreSQL, and automated superuser creation.

## Requirements

- Docker 20.10+
- Docker Compose 2.0+

## Quick Start Guide

### 1. Clone the Repository

git clone <repository-url>
cd <project-directory>

text

### 2. Create Environment File

Copy the `.env.example` file to create your `.env` file:

cp .env.example .env

text

Your `.env` file contains:

POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DATABASE=postgres_db
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=postgres_password
SECRET_KEY=django-insecure-bcrq#7ocs$4pba%7*v_vn!#c%4+p(1((3_*3$lejw-wx$47et6

Django Superuser Configuration
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@yopmail.com
DJANGO_SUPERUSER_PASSWORD=admin

text

⚠️ **Important**: For production, change `SECRET_KEY` and all passwords to secure values.

### 3. Build and Run the Project

docker-compose up -d --build