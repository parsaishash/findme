from __future__ import annotations

import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import requests
from celery import shared_task
from django.conf import settings

from .models import DownloadJob
from . import utils


def _proxies_dict(job: DownloadJob) -> dict | None:
    if job.proxy:
        return job.proxy.as_requests_dict()
    return None


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def run_download_job(self, job_id: int) -> None:
    job = DownloadJob.objects.select_related("proxy", "created_by").get(id=job_id)
    job.status = DownloadJob.STATUS_RUNNING
    job.message = ""
    job.save(update_fields=["status", "message", "updated_at"])

    try:
        base = Path(settings.FILE_SERVER_ROOT).resolve()
        dest = (base / job.target_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.relative_to(base)

        proxies = _proxies_dict(job)

        if job.job_type == DownloadJob.TYPE_URL:
            _task_url(job, dest, proxies)
        elif job.job_type == DownloadJob.TYPE_GIT:
            _task_git(job, dest, proxies)
        elif job.job_type == DownloadJob.TYPE_DOCKER:
            _task_docker(job, dest, proxies)

        job.status = DownloadJob.STATUS_SUCCESS
        job.save(update_fields=["status", "updated_at"])
    except Exception as exc:
        job.status = DownloadJob.STATUS_FAILED
        job.message = str(exc)
        job.save(update_fields=["status", "message", "updated_at"])
        raise


def _task_url(job: DownloadJob, dest: Path, proxies: dict | None) -> None:
    parsed = urlparse(job.source)
    filename = os.path.basename(parsed.path) or "download.bin"
    final = dest / filename if dest.is_dir() or not str(dest).endswith(filename) else dest
    final.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(job.source, stream=True, proxies=proxies, timeout=60) as r:
        r.raise_for_status()
        with open(final, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
    job.result_path = utils.normalize_path(str(final.relative_to(Path(settings.FILE_SERVER_ROOT))))
    job.save(update_fields=["result_path", "updated_at"])


def _task_git(job: DownloadJob, dest: Path, proxies: dict | None) -> None:
    # Choose target directory name
    if dest.exists() and dest.is_dir() and any(dest.iterdir()):
        repo_name = os.path.splitext(os.path.basename(urlparse(job.source).path.rstrip("/")))[0] or "repo"
        target = dest / repo_name
    else:
        target = dest
    target.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    if proxies and proxies.get("http"):
        env["https_proxy"] = proxies.get("https") or proxies["http"]
        env["http_proxy"] = proxies["http"]
    subprocess.check_call(["git", "clone", "--depth", "1", job.source, str(target)], env=env)
    job.result_path = utils.normalize_path(str(target.relative_to(Path(settings.FILE_SERVER_ROOT))))
    job.save(update_fields=["result_path", "updated_at"])


def _task_docker(job: DownloadJob, dest: Path, proxies: dict | None) -> None:
    image = job.source
    safe_name = image.replace("/", "_").replace(":", "-")
    tar_path = dest / f"{safe_name}.tar"
    tar_path.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    if proxies and proxies.get("http"):
        env["HTTPS_PROXY"] = proxies.get("https") or proxies["http"]
        env["HTTP_PROXY"] = proxies["http"]
    subprocess.check_call(["docker", "pull", image], env=env)
    subprocess.check_call(["docker", "save", "-o", str(tar_path), image], env=env)
    job.result_path = utils.normalize_path(str(tar_path.relative_to(Path(settings.FILE_SERVER_ROOT))))
    job.save(update_fields=["result_path", "updated_at"])


