#!/bin/bash

# macOS-specific script to run the Qt application safely
# This script sets up environment variables to prevent SIGBUS errors

echo "Setting up macOS environment for Qt application..."

# Set Qt-specific environment variables for macOS
export QT_MAC_WANTS_LAYER=1
export QT_LOGGING_RULES="*.debug=false"
export QT_AUTO_SCREEN_SCALE_FACTOR=0
export QT_SCALE_FACTOR=1
export DYLD_LIBRARY_PATH=""

# Disable OpenGL acceleration which can cause issues on some macOS systems
export QT_OPENGL=software

# Set Python to use system frameworks properly
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Environment variables set:"
echo "QT_MAC_WANTS_LAYER=$QT_MAC_WANTS_LAYER"
echo "QT_LOGGING_RULES=$QT_LOGGING_RULES"
echo "QT_OPENGL=$QT_OPENGL"

echo "Starting Qt application..."
python main.py "$@"
