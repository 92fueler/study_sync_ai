#!/bin/bash
# Start frontend service
# Usage: ./scripts/startup/start-frontend.sh

set -e

cd "$(dirname "$0")/../.."

echo "=== Starting Frontend ==="

# Helper function to load nvm
load_nvm() {
    export NVM_DIR="$HOME/.nvm"
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        \. "$NVM_DIR/nvm.sh"
        return 0
    fi
    return 1
}

# Helper function to ensure nvm is loaded and use correct version
ensure_nvm_version() {
    if load_nvm; then
        if [ -f ".nvmrc" ]; then
            nvm use
        fi
    fi
}

# Load nvm if available
load_nvm || {
    # Try loading from shell config files
    if [ -s "$HOME/.zshrc" ] && grep -q "NVM_DIR" "$HOME/.zshrc"; then
        load_nvm
    elif [ -s "$HOME/.bashrc" ] && grep -q "NVM_DIR" "$HOME/.bashrc"; then
        load_nvm
    fi
}

# Check Node version and ensure correct version is used
NODE_VERSION=$(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1 || echo "")
REQUIRED_VERSION="24"

if [ -z "$NODE_VERSION" ] || [ "$NODE_VERSION" != "$REQUIRED_VERSION" ]; then
    echo "WARNING: Node.js version mismatch!"
    echo "Required: v$REQUIRED_VERSION.x"
    if [ -n "$NODE_VERSION" ]; then
        echo "Current: v$NODE_VERSION"
    else
        echo "Current: Node.js not found"
    fi
    
    if load_nvm && (type nvm &>/dev/null 2>&1 || [ -s "$HOME/.nvm/nvm.sh" ]); then
        echo "Attempting to switch to Node.js v$REQUIRED_VERSION using nvm..."
        
        cd frontend
        if [ -f .nvmrc ]; then
            NVMRC_VERSION=$(cat .nvmrc | tr -d '[:space:]')
            echo "Found .nvmrc with version: $NVMRC_VERSION"
            
            # Try to use the version, if it fails, install it
            set +e
            nvm use &>/dev/null 2>&1
            NVM_USE_EXIT_CODE=$?
            set -e
            
            if [ $NVM_USE_EXIT_CODE -ne 0 ]; then
                echo "Version $NVMRC_VERSION not installed, installing..."
                set +e
                nvm install
                INSTALL_EXIT=$?
                set -e
                
                if [ $INSTALL_EXIT -ne 0 ]; then
                    echo "ERROR: Failed to install Node.js version from .nvmrc"
                    echo "Please run manually: cd frontend && nvm install && nvm use"
                    exit 1
                fi
                
                echo "Switching to installed version..."
                nvm use
                echo "Successfully installed and switched to Node.js version from .nvmrc"
            else
                echo "Switched to Node.js version from .nvmrc"
            fi
        else
            echo "No .nvmrc found, installing v$REQUIRED_VERSION..."
            set +e
            nvm use $REQUIRED_VERSION &>/dev/null 2>&1
            NVM_USE_EXIT_CODE=$?
            set -e
            
            if [ $NVM_USE_EXIT_CODE -ne 0 ]; then
                nvm install $REQUIRED_VERSION
                nvm use $REQUIRED_VERSION
            fi
        fi
        cd ..
    else
        echo "ERROR: nvm is not available or not properly installed"
        echo "Please install nvm: https://github.com/nvm-sh/nvm"
        echo "Or install Node.js v$REQUIRED_VERSION manually"
        exit 1
    fi
fi

echo "Using Node.js $(node --version)"

# Navigate to frontend directory
cd frontend

# Ensure correct Node version is used
ensure_nvm_version .

# Check if dependencies need to be installed/updated
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
elif [ ! -d "node_modules/react-markdown" ] || [ ! -d "node_modules/remark-gfm" ]; then
    echo "New dependencies detected. Installing/updating frontend dependencies..."
    npm install
elif [ "package.json" -nt "node_modules" ] || [ "package-lock.json" -nt "node_modules" ]; then
    echo "package.json or package-lock.json updated. Updating dependencies..."
    npm install
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating frontend .env file..."
    cp .env.example .env
    echo "Frontend .env created. Edit if needed."
fi

echo ""
echo "Starting frontend on http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Ensure correct Node version before starting dev server
ensure_nvm_version .

npm run dev
