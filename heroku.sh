#!/bin/bash
gunicorn web:app --daemon
python processor.py
