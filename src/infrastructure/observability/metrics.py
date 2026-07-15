"""Bounded-cardinality Prometheus metrics without a runtime collector dependency."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

HTTP_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
JOB_BUCKETS = (0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 15.0, 60.0)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _labels(values: tuple[tuple[str, str], ...]) -> str:
    return "{" + ",".join(f'{key}="{_escape(value)}"' for key, value in values) + "}"


@dataclass(slots=True)
class Histogram:
    buckets: tuple[float, ...]
    counts: list[int] = field(init=False)
    count: int = 0
    total: float = 0.0

    def __post_init__(self) -> None:
        self.counts = [0 for _ in self.buckets]

    def observe(self, value: float) -> None:
        self.count += 1
        self.total += value
        for index, boundary in enumerate(self.buckets):
            if value <= boundary:
                self.counts[index] += 1


class MetricsRegistry:
    """Thread-safe registry with only route-template and status-class labels."""

    def __init__(self, *, environment: str, version: str) -> None:
        self.environment = environment
        self.version = version
        self._lock = RLock()
        self._http_count: dict[tuple[str, str, str], int] = {}
        self._http_duration: dict[tuple[str, str], Histogram] = {}
        self._job_count: dict[tuple[str, str], int] = {}
        self._job_duration: dict[tuple[str, str], Histogram] = {}
        self._jobs_in_progress: dict[str, int] = {}

    def observe_http(self, method: str, route: str, status_code: int, duration: float) -> None:
        status_class = f"{status_code // 100}xx"
        with self._lock:
            key = (method, route, status_class)
            self._http_count[key] = self._http_count.get(key, 0) + 1
            histogram = self._http_duration.setdefault((method, route), Histogram(HTTP_BUCKETS))
            histogram.observe(duration)

    def job_started(self, job_type: str) -> None:
        with self._lock:
            self._jobs_in_progress[job_type] = self._jobs_in_progress.get(job_type, 0) + 1

    def job_finished(self, job_type: str, status: str, duration: float) -> None:
        with self._lock:
            key = (job_type, status)
            self._job_count[key] = self._job_count.get(key, 0) + 1
            self._job_duration.setdefault(key, Histogram(JOB_BUCKETS)).observe(duration)
            self._jobs_in_progress[job_type] = max(0, self._jobs_in_progress.get(job_type, 1) - 1)

    def _render_histogram(
        self,
        name: str,
        values: dict[tuple[str, str], Histogram],
        label_names: tuple[str, str],
    ) -> list[str]:
        lines = [f"# TYPE {name} histogram"]
        for key in sorted(values):
            histogram = values[key]
            base = tuple(zip(label_names, key, strict=True))
            for boundary, count in zip(histogram.buckets, histogram.counts, strict=True):
                lines.append(f'{name}_bucket{_labels((*base, ("le", str(boundary))))} {count}')
            lines.append(f'{name}_bucket{_labels((*base, ("le", "+Inf")))} {histogram.count}')
            lines.append(f"{name}_sum{_labels(base)} {histogram.total:.9f}")
            lines.append(f"{name}_count{_labels(base)} {histogram.count}")
        return lines

    def render(self) -> str:
        with self._lock:
            lines = [
                "# HELP risco_application_info Immutable build and environment identity.",
                "# TYPE risco_application_info gauge",
                "risco_application_info"
                f'{{environment="{_escape(self.environment)}",'
                f'version="{_escape(self.version)}"}} 1',
                "# HELP risco_http_requests_total Completed HTTP requests.",
                "# TYPE risco_http_requests_total counter",
            ]
            for (method, route, status_class), count in sorted(self._http_count.items()):
                labels = _labels(
                    (("method", method), ("route", route), ("status_class", status_class))
                )
                lines.append(f"risco_http_requests_total{labels} {count}")
            lines.extend(
                self._render_histogram(
                    "risco_http_request_duration_seconds",
                    self._http_duration,
                    ("method", "route"),
                )
            )
            lines.extend(
                [
                    "# HELP risco_jobs_total Completed background jobs.",
                    "# TYPE risco_jobs_total counter",
                ]
            )
            for (job_type, status), count in sorted(self._job_count.items()):
                labels = _labels((("job_type", job_type), ("status", status)))
                lines.append(f"risco_jobs_total{labels} {count}")
            lines.extend(
                self._render_histogram(
                    "risco_job_duration_seconds",
                    self._job_duration,
                    ("job_type", "status"),
                )
            )
            lines.extend(
                [
                    "# HELP risco_jobs_in_progress Current background jobs.",
                    "# TYPE risco_jobs_in_progress gauge",
                ]
            )
            for job_type, count in sorted(self._jobs_in_progress.items()):
                labels = _labels((("job_type", job_type),))
                lines.append(f"risco_jobs_in_progress{labels} {count}")
            return "\n".join(lines) + "\n"
