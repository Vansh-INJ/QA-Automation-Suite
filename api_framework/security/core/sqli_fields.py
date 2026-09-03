"""
SQL Injection field registry.

This module defines which request fields are injectable and how
SQL injection payloads should be inserted into each field.

Keeping field mutation logic centralized allows the SQLi engine
to test fields without knowing the internal structure of the
API payload.
"""


# ============================================================================
# FIELD SETTERS
# ============================================================================

def _set_bank_account_holder_name(
    payload: dict,
    value: str,
):
    """Set bank account holder name."""

    payload["bank"]["account_holder_name"] = value


def _set_bank_name(
    payload: dict,
    value: str,
):
    """Set bank name."""

    payload["bank"]["bank_name"] = value


def _set_bank_branch(
    payload: dict,
    value: str,
):
    """Set bank branch."""

    payload["bank"]["branch"] = value


def _set_identity_pan(
    payload: dict,
    value: str,
):
    """Set PAN field."""

    payload["identity"]["pan"] = value


def _set_communication_linkedin_url(
    payload: dict,
    value: str,
):
    """Set LinkedIn URL."""

    payload["communication"]["linkedin_url"] = value


def _set_address_current_line1(
    payload: dict,
    value: str,
):
    """Set current address line 1."""

    payload["addresses"]["current"]["line1"] = value


def _set_address_current_line2(
    payload: dict,
    value: str,
):
    """Set current address line 2."""
    payload["addresses"]["current"]["line2"] = value


def _set_address_current_landmark(
    payload: dict,
    value: str,
):
    """Set current address landmark."""
    payload["addresses"]["current"]["landmark"] = value



def _set_address_current_city(
    payload: dict,
    value: str,
):
    """Set current address city."""

    payload["addresses"]["current"]["city"] = value


def _set_family_member_name(
    payload: dict,
    value: str,
):
    """Set first family member name."""

    payload["family_members"][0]["name"] = value


# ============================================================================
# INJECTABLE FIELD REGISTRY
# ============================================================================

INJECTABLE_FIELDS = {

    "bank.account_holder_name":
        _set_bank_account_holder_name,

    "bank.bank_name":
        _set_bank_name,

    "bank.branch":
        _set_bank_branch,

    "identity.pan":
        _set_identity_pan,

    "communication.linkedin_url":
        _set_communication_linkedin_url,

    "addresses.current.line1":
        _set_address_current_line1,

    "addresses.current.line2":
        _set_address_current_line2,

    "addresses.current.landmark":
        _set_address_current_landmark, 

    "addresses.current.city":
        _set_address_current_city,

    "family_members[0].name":
        _set_family_member_name,

}