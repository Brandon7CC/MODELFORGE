#!/bin/zsh
# Set up `gcloud` cli on macOS and Linux

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
  if ! command -v gcloud &> /dev/null; then
    brew install --cask google-cloud-sdk
  fi
fi

# If we're on Linux, install with `snap`.
if [[ "$OS" == "linux" ]]; then
  # Check if gcloud is installed
  if ! command -v gcloud &> /dev/null; then
    sudo apt-get update
    sudo apt-get install apt-transport-https ca-certificates gnupg curl sudo -y
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
    sudo apt-get update && sudo apt-get install google-cloud-cli
  fi
fi

# Initialize gcloud
gcloud init
gcloud auth application-default login


