#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def should_watch_tailwind():
    """Start one Tailwind watcher in the runserver parent process."""
    watch_enabled = os.environ.get('TAILWIND_WATCH', 'true').lower()
    return (
        len(sys.argv) > 1
        and sys.argv[1] == 'runserver'
        and os.environ.get('RUN_MAIN') != 'true'
        and watch_enabled not in {'0', 'false', 'no', 'off'}
    )


def start_tailwind_watcher():
    npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    npm = npm or shutil.which('npm')

    if not npm:
        print('Aviso: npm no esta disponible; Tailwind no se recompilara automaticamente.')
        return None

    options = {'cwd': BASE_DIR}
    if os.name == 'nt':
        options['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options['start_new_session'] = True

    print('Iniciando el observador de Tailwind...')
    return subprocess.Popen([npm, 'run', 'tailwind:watch'], **options)


def stop_tailwind_watcher(process):
    if process is None or process.poll() is not None:
        return

    if os.name == 'nt':
        subprocess.run(
            ['taskkill', '/PID', str(process.pid), '/T', '/F'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        os.killpg(process.pid, signal.SIGTERM)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    tailwind_process = start_tailwind_watcher() if should_watch_tailwind() else None
    try:
        execute_from_command_line(sys.argv)
    finally:
        stop_tailwind_watcher(tailwind_process)


if __name__ == '__main__':
    main()
