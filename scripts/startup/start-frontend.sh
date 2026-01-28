#!/bin/bash
# Start frontend service
# Usage: ./scripts/startup/start-frontend.sh

set -e

cd "$(dirname "$0")/../.."

echo "=== Starting Frontend ==="

# Check Node version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
REQUIRED_VERSION="24"

if [ "$NODE_VERSION" != "$REQUIRED_VERSION" ]; then
    echo "WARNING: Node.js version mismatch!"
    echo "Required: v$REQUIRED_VERSION.x"
    echo "Current: $(node --version)"
    
    # Try to use nvm if available
    if command -v nvm &> /dev/null || [ -s "$HOME/.nvm/nvm.sh" ]; then
        echo "Attempting to switch to Node.js v$REQUIRED_VERSION using nvm..."
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        cd frontend
        if [ -f .nvmrc ]; then
            nvm use
        else
            nvm install $REQUIRED_VERSION
            nvm use $REQUIRED_VERSION
        fi
        cd ..
    else
        echo "Please install Node.js v$REQUIRED_VERSION or use nvm"
        echo "Install nvm: https://github.com/nvm-sh/nvm"
        exit 1
    fi
fi

echo "Using Node.js $(node --version)"

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Check if .env exists in frontend
if [ ! -f "frontend/.env" ]; then
    echo "Creating frontend .env file..."
    cp frontend/.env.example frontend/.env
    echo "Frontend .env created. Edit if needed."
fi

echo ""
echo "Starting frontend on http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd frontend
npm run dev
