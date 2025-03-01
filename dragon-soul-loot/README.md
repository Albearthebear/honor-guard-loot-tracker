# Honor Guard Loot Tracker

A real-time loot management system for World of Warcraft Dragon Soul raids, designed to track and prioritize loot distribution based on attendance and previous loot history.

## Features

- **Real-time Loot Priority Display**: Interactive dashboard showing current loot priorities
- **Loot Assignment System**: Interface to input items as they drop in the raid
- **Dynamic Priority Updates**: Instant recalculation of priorities when loot is assigned
- **Data Management**: Integration with CSV export functionality
- **Role-Based Penalty Adjustments**: Special consideration for tanks (7.5% reduction) and healers (5% reduction)

## Technology Stack

- **Backend**: FastAPI with WebSocket support
- **Frontend**: HTML, CSS, JavaScript with Bootstrap
- **Containerization**: Docker
- **Deployment**: Google Cloud Run
- **CI/CD**: GitHub Actions

## Development

### Local Development

1. Clone the repository:
   ```
   git clone https://github.com/Albearthebear/honor-guard-loot-tracker.git
   cd honor-guard-loot-tracker
   ```

2. Run with Docker Compose:
   ```
   docker-compose up
   ```

3. Access the application at http://localhost:8000

### Branches

- `main`: Production-ready code deployed to Cloud Run
- `development`: Development branch with the latest features

## Deployment

The application is automatically deployed to Google Cloud Run when changes are pushed to the main branch.

### Manual Deployment

1. Build the Docker image:
   ```
   docker build -t honor-guard-loot-tracker .
   ```

2. Run the container:
   ```
   docker run -p 8000:8000 honor-guard-loot-tracker
   ```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

