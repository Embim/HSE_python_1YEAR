# Health Tracker Bot

Telegram bot for tracking water, calories, and workouts using PostgreSQL, SQLAlchemy, and external APIs.

## Stack

- Python 3.10+
- aiogram 3.x
- PostgreSQL 15
- SQLAlchemy (async ORM)
- Altair (charts)
- Docker

## Architecture

Clean layered architecture:
- **Handlers** - thin controllers, route requests
- **Services** - business logic layer
- **Repositories** - data access layer
- **DTOs** - data transfer objects
- **Formatters** - message formatting
- **Logger** - centralized logging

## APIs

- OpenWeatherMap - temperature data
- OpenRouter - nutrition data via AI (nvidia/nemotron-3-nano-30b-a3b:free)
- OpenRouter - text translation (nvidia/nemotron-nano-9b-v2:free)

## Quick Start

### Setup Environment

```bash
cp .env.example .env
```

Edit `.env`:
```
BOT_TOKEN=<telegram_token>
OPENWEATHER_API_KEY=<key>
OPENROUTER_API_KEY=<key>
DATABASE_URL=postgresql://hw2_admin:nimda@localhost:5432/HW2_track
```

### Run Everything (Bot + Database)

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database on port 5432
- Bot container (builds from Dockerfile)
- Creates tables automatically via SQLAlchemy

### Run Only Database (for local development)

```bash
docker-compose up -d postgres
python bot.py
```

**Database Connection:**
- Host: localhost:5432
- DB: HW2_track
- User: hw2_admin
- Pass: nimda

## Commands

- `/start` - start
- `/set_profile` - setup profile
- `/log_water <ml>` - log water
- `/log_food` - log food (FSM)
- `/log_workout` - log workout (FSM)
- `/check_progress` - daily progress
- `/graphs` - 7-day chart
- `/recommend` - personalized tips

## Database Schema

- `users` - user profiles
- `daily_logs` - daily aggregates
- `water_logs` - water entries
- `food_logs` - food entries
- `workout_logs` - workout entries

## Docker

### Start All Services
```bash
docker-compose up -d
```

### Start Only Database
```bash
docker-compose up -d postgres
```

### Stop
```bash
docker-compose down
```

### Rebuild Bot
```bash
docker-compose up -d --build bot
```

### View Logs
```bash
docker-compose logs -f bot
docker-compose logs -f postgres
```

### Backup
```bash
docker exec hw2_track_db pg_dump -U hw2_admin HW2_track > backup.sql
```

### Restore
```bash
docker exec -i hw2_track_db psql -U hw2_admin HW2_track < backup.sql
```

### psql Access
```bash
docker exec -it hw2_track_db psql -U hw2_admin -d HW2_track
```

## Project Structure

```
HW2/
  bot.py                      - entry point
  config.py                   - configuration and constants

  Core:
    database.py               - SQLAlchemy async engine
    models.py                 - ORM models (User, DailyLog, etc.)
    logger.py                 - centralized logging
    dto.py                    - data transfer objects

  Layers:
    handlers.py               - thin Telegram handlers
    states.py                 - FSM states
    middlewares.py            - logging middleware

    services/
      user_service.py         - user profile logic
      diary_service.py        - diary operations logic

    repositories/
      user_repository.py      - user data access
      diary_repository.py     - diary data access

    formatters.py             - message text formatting

  Domain:
    calculations.py           - health formulas
    recommendation_engine.py  - recommendation rules

  External:
    API.py                    - external API clients
    charts.py                 - Altair graph generation

  Infrastructure:
    requirements.txt          - Python dependencies
    docker-compose.yml        - PostgreSQL + Bot services
    Dockerfile                - bot container image
    .env.example              - environment template
```

## Architecture Details

### Request Flow

```
User Message
    ↓
Handler (thin)
    ↓
Service (business logic)
    ↓
Repository (data access)
    ↓
Database (PostgreSQL)
```

### Layer Responsibilities

**Handlers** (`handlers.py`)
- Extract user_id from event
- Call service methods
- Format response with Formatters
- Send message to user
- No business logic, calculations, or DB access

**Services** (`services/`)
- Coordinate business operations
- Call repositories for data
- Call external APIs
- Apply business rules
- Return structured data

**Repositories** (`repositories/`)
- Database CRUD operations
- Return DTOs (not dicts)
- Manage transactions
- No business logic

**Formatters** (`formatters.py`)
- Construct user-facing messages
- Single source of truth for text
- No logic, just formatting

**DTOs** (`dto.py`)
- Type-safe data containers
- dataclass-based
- Used for data transfer between layers

### Configuration

All constants, thresholds, and data extracted to `config.py`:
- API keys and URLs
- Calculation constants
- Recommendation thresholds
- Food/workout reference data
- Water tips

### Logging

Centralized logging via `logger.py`:
- All print() statements removed
- Structured logging with levels (INFO, WARNING, ERROR)
- Consistent format across all modules

### Error Handling

- API calls have timeouts (10s) and retries (2 attempts)
- Network errors logged and handled gracefully
- Database transactions properly managed
- No secrets printed to logs

## Testing

The layered architecture enables easy testing:

**Unit Tests** - Test business logic in services
```python
# Example: test recommendation logic
result = _get_food_recommendations(calorie_deficit=250)
assert result['message'] == "Вы близки к дневной норме!"
```

**Integration Tests** - Test repository + database
```python
# Example: test user creation
user = await UserRepository.create(...)
assert user.user_id == expected_id
```

**Mock External Dependencies**
```python
# Services can be tested with mocked repositories
# Repositories can be tested with real database
# Handlers can be tested with mocked services
```

## Deployment

Deploy to Render.com, Railway, or similar. Use managed PostgreSQL for production.
