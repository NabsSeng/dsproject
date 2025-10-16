# AI Code Generation API

A Flask-based API for generating code using Google Gemini AI and deploying to GitHub Pages.

## Features

- Natural language to code generation using Google Gemini
- GitHub repository creation and file management
- GitHub Pages deployment
- Task-based generation with evaluation callbacks
- Static web application generation (HTML/CSS/JavaScript)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the application:
```bash
python app.py
```

## API Endpoints

- `POST /api/generate-and-deploy-task` - Generate code from task brief and deploy
- `GET /api/health` - Health check
- `GET /api/status` - Service status

## Environment Variables

- `GEMINI_API_KEY` - Google Gemini API key
- `GITHUB_TOKEN` - GitHub personal access token
- `SECRET_KEY` - Secret key for authentication

## License

MIT License
