#!/bin/bash
# Setup script for Poetry + Poethepoet

echo "========================================"
echo "Setting up MCP SimplicityHL Server"
echo "========================================"
echo ""

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found!"
    echo ""
    echo "Install Poetry first:"
    echo "  curl -sSL https://install.python-poetry.org | python3 -"
    echo "  or: pip install poetry"
    exit 1
fi

echo "✅ Poetry found: $(poetry --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
poetry install --all-extras

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate Poetry shell:"
echo "     poetry shell"
echo ""
echo "  2. View available tasks:"
echo "     poe"
echo ""
echo "  3. Run tests:"
echo "     poe test"
echo ""
echo "  4. Start agent:"
echo "     poe agent"
echo ""
