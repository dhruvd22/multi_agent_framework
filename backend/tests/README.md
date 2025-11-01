# Testing Infrastructure

## Backend Tests

### Setup

```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py
```

## Frontend Tests

### Setup

```bash
cd frontend
npm install
```

### Running Tests

```bash
# Run tests
npm test

# Run tests in watch mode
npm test -- --watch
```

## Test Structure

```
backend/tests/
├── test_agents.py          # Agent tests
├── test_memory.py          # Memory system tests
├── test_mcp.py             # MCP server tests
├── test_api.py             # API endpoint tests
└── fixtures/               # Test fixtures

frontend/src/__tests__/
├── components/              # Component tests
└── pages/                   # Page tests
```

