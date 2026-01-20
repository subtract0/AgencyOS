#!/bin/bash

# Micro - Quick Setup Script

echo "🌙 Setting up Micro..."
echo ""

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install it first:"
    echo "   brew install node"
    echo "   or visit https://nodejs.org"
    exit 1
fi

# Check for npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js first."
    exit 1
fi

echo "✓ Node.js $(node -v)"
echo "✓ npm $(npm -v)"
echo ""

# Install dependencies
echo "Installing dependencies..."
npm install

# Check for .env
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Add your OpenAI API key to .env"
    echo "   Get one at: https://platform.openai.com/api-keys"
    echo ""
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Add your OpenAI API key to .env"
echo "  2. Run: npm run dev"
echo "  3. Open: http://localhost:3000"
echo ""
echo "To deploy:"
echo "  vercel"
echo ""
