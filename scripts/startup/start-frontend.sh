#!/bin/bash
# Start frontend service
# Usage: ./scripts/startup/start-frontend.sh

set -e

cd "$(dirname "$0")/../.."

echo "=== Starting Frontend ==="

# Load nvm if available - try multiple methods
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    \. "$NVM_DIR/nvm.sh"
elif [ -s "$NVM_DIR/bash_completion" ]; then
    \. "$NVM_DIR/bash_completion"
fi

# Also try loading from common shell config files if nvm command not available
if ! command -v nvm &> /dev/null; then
    # Try sourcing from .zshrc or .bashrc
    if [ -s "$HOME/.zshrc" ]; then
        # Extract nvm loading lines and source them
        if grep -q "NVM_DIR" "$HOME/.zshrc"; then
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        fi
    elif [ -s "$HOME/.bashrc" ]; then
        if grep -q "NVM_DIR" "$HOME/.bashrc"; then
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        fi
    fi
fi

# Check Node version
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
    
    # Try to use nvm if available
    # Ensure nvm is loaded
    export NVM_DIR="$HOME/.nvm"
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        \. "$NVM_DIR/nvm.sh"
    fi
    
    # Check if nvm is now available (it's a function, not a command)
    if type nvm &>/dev/null 2>&1 || [ -s "$HOME/.nvm/nvm.sh" ]; then
        echo "Attempting to switch to Node.js v$REQUIRED_VERSION using nvm..."
        
        cd frontend
        if [ -f .nvmrc ]; then
            NVMRC_VERSION=$(cat .nvmrc | tr -d '[:space:]')
            echo "Found .nvmrc with version: $NVMRC_VERSION"
            
            # Ensure nvm is loaded in this subshell context
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
            
            # Try to use the version, if it fails, install it
            set +e  # Temporarily disable exit on error for nvm use check
            nvm use &>/dev/null 2>&1
            NVM_USE_EXIT_CODE=$?
            set -e  # Re-enable exit on error
            
            if [ $NVM_USE_EXIT_CODE -ne 0 ]; then
                echo "Version $NVMRC_VERSION not installed, installing..."
                set +e  # Disable exit on error for install
                # Install the version - nvm install will read from .nvmrc when in frontend directory
                echo "Running: nvm install (reading from .nvmrc)..."
                nvm install
                INSTALL_EXIT=$?
                set -e  # Re-enable exit on error
                
                if [ $INSTALL_EXIT -ne 0 ]; then
                    echo "ERROR: Failed to install Node.js version from .nvmrc"
                    echo "Please run manually: cd frontend && nvm install && nvm use"
                    exit 1
                fi
                
                # Now use the version
                echo "Switching to installed version..."
                nvm use
                echo "Successfully installed and switched to Node.js version from .nvmrc"
            else
                echo "Switched to Node.js version from .nvmrc"
            fi
        else
            echo "No .nvmrc found, installing v$REQUIRED_VERSION..."
            # Ensure nvm is loaded
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
            
            set +e  # Temporarily disable exit on error for nvm use check
            nvm use $REQUIRED_VERSION &>/dev/null 2>&1
            NVM_USE_EXIT_CODE=$?
            set -e  # Re-enable exit on error
            
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
