"""Start one local backend, reusing an already healthy instance."""
import json
import socket
import urllib.error
import urllib.request


def is_running():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3) as response:
            result=json.load(response)
        return result.get('service')=='backend' and result.get('status')=='healthy'
    except (OSError, ValueError, urllib.error.URLError):
        return False


def main():
    if is_running():
        print('AI Smart Traffic is already running. No second server was started.')
        print('Open http://127.0.0.1:8000/video-preview')
        print('Road setup: http://127.0.0.1:8000/road-setup')
        return
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1',8000))
        except OSError:
            print('Port 8000 is occupied, but the traffic health check did not respond.')
            print('Wait for the existing server to finish starting, then try again.')
            return
    from backend.app.database.connection import engine
    if engine.dialect.name == 'sqlite':
        import runpy
        runpy.run_module('backend.scripts.setup_local',run_name='__main__')
    else:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        print('PostgreSQL database connection ready.')
    import runpy
    runpy.run_module("backend.scripts.setup_ai_backend",run_name="__main__")
    import uvicorn
    uvicorn.run('backend.app.main:app',host='127.0.0.1',port=8000)


if __name__=='__main__':
    main()
