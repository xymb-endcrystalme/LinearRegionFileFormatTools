#!/bin/bash

# Run all Python tests in the test directory
python3 -m unittest discover -v -s test -p 'test_*.py'
