#!/usr/bin/env bash

# Check if HM_DATA_DIR is set
if [ -z "$HM_DATA_DIR" ]; then
    echo "HM_DATA_DIR is not set. Assuming default QA path."
    QA_DIR="$(pwd)/tmp/data_qa_temp"
else
    QA_DIR="$HM_DATA_DIR"
fi

# Remove the directory and its contents
if [ -d "$QA_DIR" ]; then
    rm -rf "$QA_DIR"
    echo "Cleaned up QA directory: $QA_DIR"
else
    echo "No QA directory found at $QA_DIR"
fi

# Unset the environment variable
unset HM_DATA_DIR
echo "QA environment variables unset."
