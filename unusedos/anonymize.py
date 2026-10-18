"""Path anonymization for exports and shared artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Anonymizer:
    enabled: bool
    host_replacement: str = "redacted-host"
    path_replacement: str = "/redacted"
    segments: tuple[str, ...] = ()

    def anonymize_path(self, path: str | None) -> str | None:
        if path is None or not self.enabled:
            return path

        result = str(path)
        for segment in self.segments:
            if not segment:
                continue
            result = re.sub(re.escape(segment), self.path_replacement.strip("/"), result, flags=re.IGNORECASE)

        replacement = self.path_replacement.rstrip("/")
        while f"{replacement}/{replacement}" in result:
            result = result.replace(f"{replacement}/{replacement}", replacement)

        return result
