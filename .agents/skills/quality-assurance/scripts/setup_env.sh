#!/usr/bin/env bash

# Define the temporary QA data directory
export HM_DATA_DIR="$(pwd)/tmp/data_qa_temp"

# Create the directory if it doesn't exist
mkdir -p "$HM_DATA_DIR"

echo "QA environment configured."
echo "HM_DATA_DIR is set to: $HM_DATA_DIR"
