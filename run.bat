@echo off
call env\Scripts\activate
uvicorn main:app --host 127.0.0.1 --port 8000