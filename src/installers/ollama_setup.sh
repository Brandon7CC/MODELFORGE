#!/bin/zsh

# Check which OS we're on
if [[ "$OSTYPE" == "linux-gnu" ]]; then
  OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  OS="darwin"
else
  echo "Unsupported OS: $OSTYPE"
  exit 1
fi

# If we're on macOS, install with Homebrew `brew install --cask google-cloud-sdk`
if [[ "$OS" == "darwin" ]]; then
  if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Please install Homebrew first."
    exit 1
  fi

  # Check if gcloud is installed
  if ! command -v ollama &> /dev/null; then
    brew install --cask ollama
  fi
fi

# If we're on Linux, install with `snap`.
if [[ "$OS" == "linux" ]]; then
  curl https://ollama.ai/install.sh | sh
fi