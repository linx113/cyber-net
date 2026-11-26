# Contributing

1. Copy `.env.example` to `.env` for local development and replace the
   development passwords. Never commit `.env` or credentials.
2. Run the services with `docker compose up --build -d`.
3. Before opening a pull request, run:

   ```powershell
   cd frontend
   npm ci
   npm run lint
   npm run build
   cd ..
   $env:PYTHONPATH = "services/analytics-service"
   python -m unittest discover -s services/analytics-service/tests
   $env:PYTHONPATH = "services/device-simulator"
   python -m unittest discover -s services/device-simulator/tests
   docker compose --profile tools config --quiet
   ```

4. Describe operational or schema changes in `README.md`, including how
   existing database volumes are migrated.
