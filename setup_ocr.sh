#!/bin/bash

# OCR Setup Script

echo "Setting up OCR for Blockchain Forensics Platform..."

# Check if Tesseract is installed
if ! command -v tesseract &> /dev/null; then
    echo "❌ Tesseract not found. Installing..."

    # Detect OS and install accordingly
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install tesseract tesseract-lang
        else
            echo "❌ Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
    else
        echo "❌ Unsupported OS. Please install Tesseract manually."
        exit 1
    fi
else
    echo "✅ Tesseract already installed: $(tesseract --version | head -1)"
fi

# Test OCR functionality
echo "Testing OCR with sample image..."
if [ -f "test_image.png" ]; then
    tesseract test_image.png stdout -l eng+deu
else
    echo "ℹ️  No test image found. OCR setup complete."
fi

echo "✅ OCR setup finished!"
echo ""
echo "To enable OCR in your application:"
echo "1. Set OCR_ENABLED=1 in your .env file"
echo "2. Restart your backend server"
echo "3. Upload an image via the chat widget"
echo ""
echo "For more information, see OCR_SETUP.md"
