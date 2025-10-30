#!/bin/bash
cd /home/kavia/workspace/code-generation/plugin-platform-215909-215972/BackendAPIService
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

