#!/bin/bash

echo "Starting YouTube Agent services..."

# Function to start service in new terminal
start_service() {
    local name=$1
    local command=$2
    echo "Starting ${name} service..."
    osascript -e "tell app \"Terminal\" to do script \"cd $(pwd) && ${command}\""
}

# Function to wait for a service to be ready
wait_for_service() {
    local port="$1"
    local service="$2"
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for ${service} to be ready..."
    while ! nc -z localhost "${port}" 2>/dev/null; do
        if [ "${attempt}" -ge "${max_attempts}" ]; then
            echo "${service} failed to start"
            return 1
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "${service} is ready!"
}

# Install required packages if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing required packages..."
    pip install -r requirements.txt
fi

# Kill any existing processes on the required ports
echo "Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
lsof -ti:5002 | xargs kill -9 2>/dev/null || true

# Make sure scripts are executable
chmod +x script-to-srt.py text-to-speech.py generate-video.py
    
    # Try iTerm2 first, fall back to Terminal
    if command -v osascript &> /dev/null; then
        # Check if iTerm2 is available
        if osascript -e 'tell application "System Events" to exists process "iTerm"' &> /dev/null; then
            osascript <<EOF
                tell application "iTerm"
                    create window with default profile
                    tell current window
                        tell current session
                            write text "cd $(pwd)"
                            write text "echo '=== Starting $name service ==='"
                            write text "$command"
                        end tell
                    end tell
                end tell
EOF
        else
            # Fall back to Terminal.app
            osascript <<EOF
                tell application "Terminal"
                    do script "cd $(pwd) && echo '=== Starting $name service ===' && $command"
                end tell
EOF
        fi
    else
        # For non-macOS systems, run in background
        echo "Starting $name..."
        $command &
    fi
}

# Ensure Python virtual environment is activated if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install required packages if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing required packages..."
    pip install -r requirements.txt
fi

# Start the SRT Generation service
start_service "SRT Generation" "python script-to-srt.py"
wait_for_service 8000 "SRT Generation"

# Start the Text-to-Speech service
start_service "Text-to-Speech" "python text-to-speech.py"
wait_for_service 5001 "Text-to-Speech"

# Start the Video Generation service
start_service "Video Generation" "python generate-video.py"
wait_for_service 5002 "Video Generation"

echo "All services started successfully!"
echo "Services running:"
echo "- SRT Generation: http://localhost:8000"
echo "- Text-to-Speech: http://localhost:5001"
echo "- Video Generation: http://localhost:5002"
