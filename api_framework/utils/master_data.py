# master_data.py

"""
Dynamic HRMS master-data lookups.

All IDs are fetched from the API at runtime instead of being hard-coded,
so tests never break just because dev data was reseeded and old UUIDs
in .env went stale.

CONFIRMED against real API responses (2026-09-01) for every endpoint
below — field names, status flag, and the managers-list nested shape
have all been verified, not assumed.

Standard master-data endpoints:
{
    "status": "success",
    "data": [
        {"uuid": "...", "...": "...", "status": 1}
    ]
}

Managers use a different, grouped shape:
{
    "status": "success",
    "data": [
        {"level": "...", "managers": [{"uuid": "...", "name": "...", ...}]}
    ]
}
Manager records have no "status" field, so they are never filtered.

Usage:

    from master_data import MasterData

    master = MasterData(authenticated_offer_client)

    function = master.get_function("Pre Sales")
    sub_function = master.get_sub_function(function["uuid"], "Client Solutions")
    job_title = master.get_job_title("Software Engineer I")
    legal_entity = master.get_legal_entity("INJ Partners")
    work_location = master.get_work_location("Noida Head Office")
    hierarchy = master.get_hierarchy_level("Manager")

    # NOTE: in this environment there are currently 2 active salary
    # structures sharing the same legal_entity_uuid/work_location_uuid
    # (SAL_NOIDA and TEST), so legal_entity/work_location filtering
    # alone is NOT enough to disambiguate. Always pass ss_code/ss_name
    # explicitly:
    salary = master.get_salary_structure("SAL_NOIDA")

    manager = master.get_reporting_manager()  # only works if exactly 1 exists

The returned objects are the complete API records, so callers can use
["uuid"], ["jt_name"], ["le_name"], etc. as required.
"""

from __future__ import annotations

from typing import Any


class MasterDataError(RuntimeError):
    """Raised when HRMS master data cannot be fetched or resolved."""


class MasterData:
    """Dynamic lookup helper for HRMS onboarding master data."""

    FUNCTIONS_ENDPOINT = "/api/admin/functions"
    SUB_FUNCTIONS_ENDPOINT = "/api/admin/sub-functions/by-function/{function_uuid}"
    JOB_TITLES_ENDPOINT = "/api/admin/job-titles"
    LEGAL_ENTITIES_ENDPOINT = "/api/admin/legal-entities"
    WORK_LOCATIONS_ENDPOINT = "/api/admin/work-locations"
    HIERARCHY_LEVELS_ENDPOINT = "/api/admin/hierarchy-levels"
    SALARY_STRUCTURES_ENDPOINT = "/api/admin/salary-structures"
    MANAGERS_ENDPOINT = "/api/hr/users/managers-list"

    def __init__(self, client):
        """
        client:
            Existing authenticated HTTP client used by the test suite.
            Must expose client.get(path) and return a requests.Response
            -like object (response.json(), response.status_code).
        """
        self.client = client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_data(self, endpoint: str) -> list[dict[str, Any]]:
        """GET an endpoint and return its data list."""
        response = self.client.get(endpoint)

        if hasattr(response, "raise_for_status"):
            try:
                response.raise_for_status()
            except Exception as exc:
                raise MasterDataError(
                    f"{endpoint} failed: "
                    f"{getattr(response, 'status_code', '?')} "
                    f"{getattr(response, 'text', '')}"
                ) from exc

        try:
            payload = response.json()
        except (ValueError, AttributeError) as exc:
            raise MasterDataError(
                f"Invalid JSON returned by {endpoint}"
            ) from exc

        if payload.get("status") != "success":
            raise MasterDataError(
                f"Master-data request failed: {endpoint}; "
                f"response={payload}"
            )

        data = payload.get("data")

        if not isinstance(data, list):
            raise MasterDataError(
                f"Expected data[] from {endpoint}, "
                f"got {type(data).__name__}: {data!r}"
            )

        return data

    @staticmethod
    def _active(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return records explicitly marked active."""
        return [record for record in records if record.get("status") == 1]

    @staticmethod
    def _find(
        records: list[dict[str, Any]],
        *,
        value: str,
        fields: tuple[str, ...],
        resource_name: str,
    ) -> dict[str, Any]:
        """
        Find a record by one of the supplied fields.
        Matching is case-insensitive and ignores surrounding whitespace.
        """
        wanted = value.strip().casefold()

        for record in records:
            for field in fields:
                actual = record.get(field)
                if actual is not None and str(actual).strip().casefold() == wanted:
                    return record

        available = [
            {field: record.get(field) for field in fields if record.get(field) is not None}
            for record in records
        ]

        raise MasterDataError(
            f"{resource_name} '{value}' was not found among active records. "
            f"Available values: {available}"
        )

    # ------------------------------------------------------------------
    # Functions
    # ------------------------------------------------------------------

    def get_functions(self) -> list[dict[str, Any]]:
        """Return all active top-level functions."""
        return self._active(self._get_data(self.FUNCTIONS_ENDPOINT))

    def get_function(self, name_or_code: str) -> dict[str, Any]:
        """Resolve an active function by fun_name or fun_code."""
        return self._find(
            self.get_functions(),
            value=name_or_code,
            fields=("fun_name", "fun_code"),
            resource_name="Function",
        )

    # ------------------------------------------------------------------
    # Sub-functions
    # ------------------------------------------------------------------

    def get_sub_functions(self, function_uuid: str) -> list[dict[str, Any]]:
        """Return active sub-functions for a function."""
        endpoint = self.SUB_FUNCTIONS_ENDPOINT.format(function_uuid=function_uuid)
        return self._active(self._get_data(endpoint))

    def get_sub_function(self, function_uuid: str, name_or_code: str) -> dict[str, Any]:
        """Resolve an active sub-function by name/code."""
        records = self.get_sub_functions(function_uuid)
        return self._find(
            records,
            value=name_or_code,
            fields=("sf_name", "sf_code", "name", "code"),
            resource_name="Sub-function",
        )

    # ------------------------------------------------------------------
    # Job titles
    # ------------------------------------------------------------------

    def get_job_titles(self) -> list[dict[str, Any]]:
        """Return all active job titles. Confirmed fields: uuid, jt_code, jt_name, status."""
        return self._active(self._get_data(self.JOB_TITLES_ENDPOINT))

    def get_job_title(self, name_or_code: str) -> dict[str, Any]:
        """Resolve an active job title."""
        return self._find(
            self.get_job_titles(),
            value=name_or_code,
            fields=("jt_name", "jt_code"),
            resource_name="Job title",
        )

    # ------------------------------------------------------------------
    # Legal entities
    # ------------------------------------------------------------------

    def get_legal_entities(self) -> list[dict[str, Any]]:
        """Return all active legal entities. Confirmed fields: uuid, le_code, le_name, status."""
        return self._active(self._get_data(self.LEGAL_ENTITIES_ENDPOINT))

    def get_legal_entity(self, name_or_code: str) -> dict[str, Any]:
        """Resolve an active legal entity."""
        return self._find(
            self.get_legal_entities(),
            value=name_or_code,
            fields=("le_name", "le_code"),
            resource_name="Legal entity",
        )

    # ------------------------------------------------------------------
    # Work locations
    # ------------------------------------------------------------------

    def get_work_locations(self, legal_entity_uuid: str | None = None) -> list[dict[str, Any]]:
        """Return active work locations, optionally filtered by legal_entity_uuid client-side."""
        records = self._active(self._get_data(self.WORK_LOCATIONS_ENDPOINT))

        if legal_entity_uuid:
            records = [r for r in records if r.get("legal_entity_uuid") == legal_entity_uuid]

        return records

    def get_work_location(
        self, name_or_code: str, legal_entity_uuid: str | None = None
    ) -> dict[str, Any]:
        """Resolve an active work location by name/code."""
        return self._find(
            self.get_work_locations(legal_entity_uuid=legal_entity_uuid),
            value=name_or_code,
            fields=("wl_name", "wl_code"),
            resource_name="Work location",
        )

    # ------------------------------------------------------------------
    # Hierarchy levels
    # ------------------------------------------------------------------

    def get_hierarchy_levels(self) -> list[dict[str, Any]]:
        """Return all active hierarchy levels. Confirmed fields: uuid, code, title, rank, can_be_manager, status."""
        return self._active(self._get_data(self.HIERARCHY_LEVELS_ENDPOINT))

    def get_hierarchy_level(self, title_or_code: str) -> dict[str, Any]:
        """Resolve an active hierarchy level."""
        return self._find(
            self.get_hierarchy_levels(),
            value=title_or_code,
            fields=("title", "code"),
            resource_name="Hierarchy level",
        )

    # ------------------------------------------------------------------
    # Salary structures
    # ------------------------------------------------------------------

    def get_salary_structures(
        self,
        legal_entity_uuid: str | None = None,
        work_location_uuid: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Return active salary structures, optionally filtered by
        legal_entity_uuid and/or work_location_uuid.

        WARNING: in the confirmed dev dataset, this filter combination
        alone is NOT unique — multiple active structures (e.g.
        SAL_NOIDA and TEST) share the same legal_entity_uuid and
        work_location_uuid. Always disambiguate with ss_code/ss_name
        via get_salary_structure() when more than one is expected.
        """
        records = self._active(self._get_data(self.SALARY_STRUCTURES_ENDPOINT))

        if legal_entity_uuid:
            records = [r for r in records if r.get("legal_entity_uuid") == legal_entity_uuid]

        if work_location_uuid:
            records = [r for r in records if r.get("work_location_uuid") == work_location_uuid]

        return records

    def get_salary_structure(
        self,
        name_or_code: str | None = None,
        *,
        legal_entity_uuid: str | None = None,
        work_location_uuid: str | None = None,
    ) -> dict[str, Any]:
        """
        Resolve an active salary structure.

        Strongly recommended: always pass name_or_code (e.g. "SAL_NOIDA")
        in this environment, since legal_entity/work_location filtering
        alone currently matches more than one active structure.
        """
        records = self.get_salary_structures(
            legal_entity_uuid=legal_entity_uuid,
            work_location_uuid=work_location_uuid,
        )

        if name_or_code:
            return self._find(
                records,
                value=name_or_code,
                fields=("ss_name", "ss_code"),
                resource_name="Salary structure",
            )

        if len(records) == 1:
            return records[0]

        if not records:
            raise MasterDataError(
                "No active salary structure matches the supplied "
                "legal entity/work location."
            )

        available = [
            {
                "uuid": r.get("uuid"),
                "ss_code": r.get("ss_code"),
                "ss_name": r.get("ss_name"),
                "legal_entity_uuid": r.get("legal_entity_uuid"),
                "work_location_uuid": r.get("work_location_uuid"),
            }
            for r in records
        ]

        raise MasterDataError(
            "Multiple active salary structures match the supplied "
            "legal entity/work location. Specify ss_name or ss_code. "
            f"Available: {available}"
        )

    # ------------------------------------------------------------------
    # Reporting managers
    # ------------------------------------------------------------------

    def get_reporting_managers(self) -> list[dict[str, Any]]:
        """
        Return all managers, flattened from the grouped
        data[].managers[] response. Managers have no status field,
        so no active filter is applied.
        """
        response = self.client.get(self.MANAGERS_ENDPOINT)

        if hasattr(response, "raise_for_status"):
            try:
                response.raise_for_status()
            except Exception as exc:
                raise MasterDataError(
                    f"{self.MANAGERS_ENDPOINT} failed: "
                    f"{getattr(response, 'status_code', '?')} "
                    f"{getattr(response, 'text', '')}"
                ) from exc

        try:
            payload = response.json()
        except (ValueError, AttributeError) as exc:
            raise MasterDataError(
                f"Invalid JSON returned by {self.MANAGERS_ENDPOINT}"
            ) from exc

        if payload.get("status") != "success":
            raise MasterDataError(f"Manager request failed: {payload}")

        groups = payload.get("data")

        if not isinstance(groups, list):
            raise MasterDataError("Expected manager data[] list.")

        managers: list[dict[str, Any]] = []

        for group in groups:
            group_managers = group.get("managers", [])
            if isinstance(group_managers, list):
                managers.extend(group_managers)

        return managers

    def get_reporting_manager(self, name_or_employee_code: str | None = None) -> dict[str, Any]:
        """
        Resolve a reporting manager by name, emp_code, or email.
        If no value is supplied, exactly one manager must be available
        (NOTE: confirmed dev dataset currently has 4+ managers across
        levels, so pass a name/emp_code explicitly rather than relying
        on this fallback).
        """
        managers = self.get_reporting_managers()

        if name_or_employee_code:
            return self._find(
                managers,
                value=name_or_employee_code,
                fields=("name", "emp_code", "email"),
                resource_name="Reporting manager",
            )

        if len(managers) == 1:
            return managers[0]

        if not managers:
            raise MasterDataError("No reporting managers were returned by the API.")

        available = [
            {
                "uuid": m.get("uuid"),
                "emp_code": m.get("emp_code"),
                "name": m.get("name"),
                "email": m.get("email"),
            }
            for m in managers
        ]

        raise MasterDataError(
            "Multiple reporting managers are available. "
            "Specify a manager by name, employee code, or email. "
            f"Available: {available}"
        )


def get_master_data(client) -> MasterData:
    """Create a MasterData helper around an existing authenticated client."""
    return MasterData(client)