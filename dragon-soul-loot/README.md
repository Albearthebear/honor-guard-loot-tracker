# Dragon Soul Loot Manager

A real-time loot management system for World of Warcraft's Dragon Soul raid, supporting up to 50 concurrent users with live priority updates and loot assignments.

## Features

- Real-time loot priority display
- Live loot assignment system
- WebSocket-based updates
- Support for both 10 and 25-man raid compositions
- Token and role-based priority calculations
- Historical loot tracking

## Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 16+ (for local frontend development)
- Python 3.9+ (for local backend development)

### Development Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd dragon-soul-loot
   ```

2. Start the development environment:
   ```bash
   docker-compose up
   ```

3. Access the applications:
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - API Base URL: http://localhost:8000

### Local Development

To run the services individually:

#### Backend
```bash
cd app
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## Project Structure

```
dragon-soul-loot/
├── app/                    # FastAPI backend
│   ├── api/               # API routes
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   └── websockets/        # WebSocket handlers
├── frontend/              # React frontend
├── data/                  # Data files
└── tests/                 # Test suite
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## License

MIT License
