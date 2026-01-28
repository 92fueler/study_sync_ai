# StudySync AI Frontend

Modern React + TypeScript frontend for StudySync AI - Cognitive Learning Manager.

> **Note**: For project-wide setup and architecture, see the [main README](../README.md).

## Quick Start

### Prerequisites

- Node.js 24.x (pinned version)
- npm 10+ or yarn/pnpm

**Using nvm (recommended):**
```bash
cd frontend
nvm use  # Automatically uses version from .nvmrc
```

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Features

- **Learning DNA Onboarding**: Multi-step wizard to capture user learning preferences
- **Knowledge Bank**: Bulk file upload with drag & drop support and grid view of artifacts
- **AI Learning Plan Proposal**: Modal interface for reviewing and approving AI-generated learning plans
- **Personalized Study Session Viewer**: Split-screen interface with media player, transcript sync, and Mermaid diagram support

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **React Router** for navigation
- **React Dropzone** for file uploads
- **Mermaid.js** for diagram rendering
- **Axios** for API communication

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API client and endpoints
│   ├── components/    # Reusable components
│   ├── pages/         # Page components
│   ├── utils/         # Utility functions
│   ├── App.tsx        # Main app component with routing
│   └── main.tsx       # Entry point
├── public/            # Static assets
└── package.json       # Dependencies
```

## Key Components

### Pages

- **Onboarding**: Multi-step onboarding wizard (Learning Style, Scheduling, Integrations)
- **KnowledgeBank**: Dashboard with bulk upload and artifact grid view
- **Dashboard**: Main dashboard with stats and quick actions
- **StudySession**: Split-screen study session viewer with media player

### Components

- **Layout**: Main layout with sidebar navigation
- **Mermaid**: Component for rendering Mermaid diagrams

## API Integration

The frontend communicates with the FastAPI backend at `/api/v1`. Key endpoints:

- `POST /upload` - Upload files for processing
- `GET /artifacts` - List user artifacts
- `GET /artifacts/{id}` - Get specific artifact
- `POST /profile` - Create user profile
- `GET /profile/{user_id}` - Get user profile
- `GET /notifications` - Get user notifications

## Features Implementation

### File Upload

Uses `react-dropzone` for drag & drop file uploads. Supports:
- PDF, TXT, MD files
- Audio files (MP3, WAV)
- Video files (MP4, MOV)

### Mermaid Diagrams

Renders Mermaid.js diagrams in markdown content. Supports:
- Flowcharts
- Sequence diagrams
- State diagrams
- And more Mermaid diagram types

### Media Player

Built-in media player for audio/video content with:
- Play/pause controls
- Skip forward/backward (10s)
- Progress tracking
- Synchronized transcript

## Troubleshooting

### CORS Issues

If you encounter CORS errors, ensure:
1. Backend CORS is configured to allow `http://localhost:3000`
2. Vite proxy is configured correctly in `vite.config.ts`

### Mermaid Diagrams Not Rendering

- Ensure `mermaid` package is installed
- Check browser console for errors
- Verify Mermaid syntax is correct

### File Upload Fails

- Check backend is running
- Verify file size limits (10MB default)
- Check network tab for API errors

### Port Already in Use

```bash
# Find process using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>
```

## Development Notes

- The app uses localStorage for user session management (demo purposes)
- API calls are proxied through Vite dev server to avoid CORS issues
- Tailwind CSS is used for all styling to match the design system

## Related Documentation

- [Main README](../README.md) - Project overview and setup
- [USER_GUIDE.md](../USER_GUIDE.md) - Complete API documentation
