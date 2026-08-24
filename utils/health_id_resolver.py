"""
Resolves dynamic path variables (e.g. {employee_uuid}) at runtime by calling
a known "source" list endpoint and pulling a real ID out of its response —
instead of hardcoding a UUID that may not exist tomorrow.

Cached per session: each variable is resolved once per run (the first time
it's needed), not once per endpoint that uses it — so if 5 endpoints all
need {employee_uuid}, we only call the source list endpoint once.
"""

import json


class IdResolutionError(Exception):
    """Raised when a source list endpoint can't be queried, or none of the
    candidate field names are found in the first record it returns."""
    pass


class HealthIdResolver:
    def __init__(self, health_client, resolver_config: dict):
        self.health_client = health_client
        self.resolver_config = resolver_config
        self._cache = {}  # var_name -> resolved value
        self._errors = {}  # var_name -> error message (for reporting)

    def resolve(self, var_name: str) -> str:
        if var_name in self._cache:
            return self._cache[var_name]
        if var_name in self._errors:
            # Already failed once this session — don't hammer the source
            # endpoint again, just re-raise the same failure.
            raise IdResolutionError(self._errors[var_name])

        if var_name not in self.resolver_config:
            msg = f"No RESOLVER_CONFIG entry for '{var_name}'"
            self._errors[var_name] = msg
            raise IdResolutionError(msg)

        cfg = self.resolver_config[var_name]
        source_path = cfg["source_path"]
        candidate_fields = cfg["fields"]

        try:
            resp, elapsed_ms, url, headers = self.health_client.request(
                method="GET", path=source_path, auth_profile="employee",
            )
        except Exception as e:
            msg = f"Failed to call source endpoint {source_path} for '{var_name}': {e}"
            self._errors[var_name] = msg
            raise IdResolutionError(msg)

        if resp.status_code != 200:
            msg = (
                f"Source endpoint {source_path} for '{var_name}' returned "
                f"{resp.status_code}, expected 200. Can't resolve ID."
            )
            self._errors[var_name] = msg
            raise IdResolutionError(msg)

        try:
            body = resp.json()
        except (ValueError, json.JSONDecodeError):
            msg = f"Source endpoint {source_path} for '{var_name}' didn't return valid JSON."
            self._errors[var_name] = msg
            raise IdResolutionError(msg)

        # Try common list-wrapping shapes: raw list, {"data": [...]},
        # {"items": [...]}, {"results": [...]}
        records = None
        if isinstance(body, list):
            records = body
        elif isinstance(body, dict):
            for key in ("data", "items", "results"):
                if isinstance(body.get(key), list):
                    records = body[key]
                    break
                # some APIs nest one level deeper, e.g. {"data": {"items": [...]}}
                if isinstance(body.get(key), dict):
                    for inner_key in ("items", "results", "data"):
                        if isinstance(body[key].get(inner_key), list):
                            records = body[key][inner_key]
                            break
                if records:
                    break

        if not records:
            msg = (
                f"Source endpoint {source_path} for '{var_name}' returned no "
                f"records (empty list) — can't extract an ID to test against."
            )
            self._errors[var_name] = msg
            raise IdResolutionError(msg)

        first_record = records[0]
        for field in candidate_fields:
            if isinstance(first_record, dict) and field in first_record:
                value = first_record[field]
                self._cache[var_name] = str(value)
                return self._cache[var_name]

        msg = (
            f"None of the candidate fields {candidate_fields} found in first "
            f"record from {source_path} for '{var_name}'. Actual record keys: "
            f"{list(first_record.keys()) if isinstance(first_record, dict) else type(first_record)}. "
            f"Update RESOLVER_CONFIG['{var_name}']['fields'] to match the real field name."
        )
        self._errors[var_name] = msg
        raise IdResolutionError(msg)

    def resolve_all(self, var_names: list) -> dict:
        """Resolves multiple vars, returns {var_name: value}. Raises on first failure."""
        return {v: self.resolve(v) for v in var_names}
