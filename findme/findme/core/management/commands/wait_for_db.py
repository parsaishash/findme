"""
Django management command to wait for database to be ready.
Useful for CI/CD pipelines and container orchestration.
"""
import time
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Wait for database to be ready"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--timeout",
            type=int,
            default=60,
            help="Maximum time to wait in seconds (default: 60)",
        )
        parser.add_argument(
            "--interval",
            type=float,
            default=1.0,
            help="Check interval in seconds (default: 1.0)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        timeout = options["timeout"]
        interval = options["interval"]

        self.stdout.write("Waiting for database...")
        start_time = time.time()

        while True:
            try:
                connection.ensure_connection()
                self.stdout.write(
                    self.style.SUCCESS("Database is ready!")
                )
                break
            except OperationalError:
                if time.time() - start_time > timeout:
                    self.stderr.write(
                        self.style.ERROR(
                            f"Database not ready after {timeout} seconds"
                        )
                    )
                    raise

                self.stdout.write(".", ending="")
                self.stdout.flush()
                time.sleep(interval)

        # Additional check - try a simple query
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(
                self.style.SUCCESS("Database connection verified")
            )
        except OperationalError as e:
            self.stderr.write(
                self.style.ERROR(f"Database query failed: {e}")
            )
            raise