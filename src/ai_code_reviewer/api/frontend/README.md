# Code Reviewer Frontend

React-based web interface for the AI Code Reviewer application.

## Features

- **Tab 1 - Diff Upload**: Upload .diff or .patch files for AI code review
- **Tab 2 - Manual Review**: Trigger reviews for Pull Requests or Commits from Bitbucket
- **Tab 3 - Reviews**: View successful code reviews with pagination (25 per page)
- **Tab 4 - Failures**: View failed review attempts with detailed error information
- **Tab 5 - Config**: System health and configuration status (right-aligned tab)

## Technology Stack

- **React 18+** with TypeScript 5.9+
- **Vite** for fast development and optimized builds
- **Material-UI (MUI) v5** for UI components with Intel blue theme
- **React Router v6** for navigation
- **Axios** for API calls
- **react-markdown** for rendering review feedback
- **ESLint 8.x** with @typescript-eslint v8.x for code quality

## Development

### Prerequisites

- Node.js 18+ and npm

### Setup

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Update VITE_API_BASE_URL if backend is not at localhost:8000
```

### Run Development Server

```bash
npm run dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000)

API requests to `/api/*` are automatically proxied to the backend (configured in `vite.config.ts`).

### Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── components/          # React components
│   ├── Layout/         # App layout (Header, Tabs)
│   ├── DiffUpload/     # Diff file upload
│   ├── ManualReview/   # Manual review trigger
│   ├── ReviewsTable/   # Successful reviews
│   ├── FailuresTable/  # Failed reviews
│   └── SystemInfo/     # System status
├── services/
│   └── api.ts          # API client
├── theme/
│   └── theme.ts        # Material-UI theme
├── types/
│   └── types.ts        # TypeScript types
├── App.tsx             # Main app
└── main.tsx            # Entry point
```

## Theme

The application uses Intel Blue (#0071C5) as the primary color, creating a professional and clean interface.

## API Integration

All API calls go through the `api.ts` service, which handles:
- Base URL configuration from environment
- Request/response types
- Error handling
- Timeout configuration (2 minutes for LLM operations)

## Code Quality

### Linting

```bash
# Run ESLint
npm run lint

# Auto-fix issues (from project root)
make frontend-lint
```

Configuration in `.eslintrc.cjs`:
- ESLint 8.x with @typescript-eslint v8.x
- React hooks rules
- React refresh plugin for Vite HMR
- TypeScript 5.9+ support

### Type Checking

TypeScript compilation runs during build:

```bash
# Build with type checking
npm run build
```

Type definitions:
- `src/types/types.ts` - API response types
- `src/vite-env.d.ts` - Vite environment variable types

## Environment Variables

- `VITE_API_BASE_URL`: Backend API URL (default: `/api`)

## Recent Updates (January 2025)

- ✅ Added ESLint configuration with TypeScript support (`.eslintrc.cjs`)
- ✅ Upgraded @typescript-eslint to v8.x for TypeScript 5.9 compatibility
- ✅ Created `vite-env.d.ts` for proper Vite environment type definitions
- ✅ Fixed all linting errors (prefer-const, unused variables)
- ✅ Integrated frontend linting into CI pipeline (`make frontend-lint`)
- ✅ Docker build successfully creates optimized production bundle
- ✅ All dependencies updated for compatibility

## Troubleshooting

### Linting Errors

1. Run linting: `npm run lint`
2. Auto-fix many issues: `npm run lint -- --fix`
3. Check ESLint config: `.eslintrc.cjs`
4. Verify @typescript-eslint version: Should be v8.x for TypeScript 5.9+

### Type Errors

1. Ensure `vite-env.d.ts` exists in `src/` directory
2. Verify TypeScript version 5.9+ in `package.json`
3. Check type definitions in `src/types/types.ts`
4. Run `npm install` to ensure all @types packages are installed

### Port Already in Use

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- --port 3001
```

### API Connection Issues

1. Ensure backend is running on http://localhost:8000
2. Check Vite proxy configuration in `vite.config.ts`
3. Verify API base URL: `import.meta.env.VITE_API_BASE_URL`
4. Check browser console for CORS errors
