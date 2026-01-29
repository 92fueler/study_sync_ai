# StudySync AI Frontend (React 19 + Vite 7)

## Overview 🚀
This is the new frontend implementation for StudySync AI, built from the ground up to support the "Cognitive Learning Manager" vision. It features a polished, responsive UI/UX with 4 main pages:
1. **Dashboard**: Central hub for raw notes and active plans.
2. **Learning DNA**: Personalization engine with decoupled formats/preferences.
3. **Learning Plan**: AI-proposed plans with approval workflow and topic icons.
4. **Knowledge Bank**: Batch ingestion hub with drag-and-drop and live processing.

## Quick Start
```bash
cd frontend
npm install
npm run dev
```
App runs at: **http://localhost:3001**

## Tech Stack
- **React 19**
- **Vite 7**
- **TypeScript**
- **Tailwind CSS 3.3**
- **Lucide React** (Icons)
- **Google Fonts** (Playfair Display + Inter)

## Project Structure
```
frontend/
├── src/
│   ├── api/           # API integration (Legacy/Shared)
│   ├── components/    # Reusable UI components
│   ├── pages/         # Main page views
│   ├── utils/         # shared utilities
│   ├── assets/        # Static assets
│   ├── App.tsx        # Routing configuration
│   └── main.tsx       # App entry point
```

---

# Legacy Documentation (Original README)

Below is the original documentation from the previous React 18 implementation. Some information (like API endpoints or StudySession page) may still be relevant for reference.

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

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
