"""
SQL Injection field registry.

This module defines which request fields are injectable and how
SQL injection payloads should be inserted into each field.

Keeping field mutation logic centralized allows the SQLi engine
to test fields without knowing the internal structure of the
API payload.
"""


# ============================================================================
# FIELD SETTERS — BANK
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


def _set_bank_ifsc(
    payload: dict,
    value: str,
):
    """Set bank IFSC code."""
    payload["bank"]["ifsc_code"] = value


# ============================================================================
# FIELD SETTERS — IDENTITY
# ============================================================================

def _set_identity_pan(
    payload: dict,
    value: str,
):
    """Set PAN field."""
    payload["identity"]["pan"] = value


def _set_identity_aadhaar(
    payload: dict,
    value: str,
):
    """Set Aadhaar field."""
    payload["identity"]["aadhar"] = value


# ============================================================================
# FIELD SETTERS — COMMUNICATION
# ============================================================================

def _set_communication_linkedin_url(
    payload: dict,
    value: str,
):
    """Set LinkedIn URL."""
    payload["communication"]["linkedin_url"] = value


# ============================================================================
# FIELD SETTERS — ADDRESSES (CURRENT)
# ============================================================================

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


def _set_address_current_state(
    payload: dict,
    value: str,
):
    """Set current address state."""
    payload["addresses"]["current"]["state"] = value


def _set_address_current_pincode(
    payload: dict,
    value: str,
):
    """Set current address pin code."""
    payload["addresses"]["current"]["pin_code"] = value


# ============================================================================
# FIELD SETTERS — ADDRESSES (PERMANENT)
# ============================================================================

def _set_address_permanent_line1(
    payload: dict,
    value: str,
):
    """Set permanent address line 1."""
    payload["addresses"]["permanent"]["line1"] = value


def _set_address_permanent_city(
    payload: dict,
    value: str,
):
    """Set permanent address city."""
    payload["addresses"]["permanent"]["city"] = value


def _set_address_permanent_state(
    payload: dict,
    value: str,
):
    """Set permanent address state."""
    payload["addresses"]["permanent"]["state"] = value


# ============================================================================
# FIELD SETTERS — FAMILY MEMBERS
# ============================================================================

def _set_family_member_name(
    payload: dict,
    value: str,
):
    """Set first family member name."""
    payload["family_members"][0]["name"] = value


# ============================================================================
# FIELD SETTERS — EDUCATION
# ============================================================================

def _set_education_college(
    payload: dict,
    value: str,
):
    """Set education institution (college) name."""
    payload["education"][0]["college"] = value


def _set_education_course(
    payload: dict,
    value: str,
):
    """Set education course/degree name."""
    payload["education"][0]["course"] = value


def _set_education_specialization(
    payload: dict,
    value: str,
):
    """Set education specialization."""
    payload["education"][0]["specialization"] = value


# ============================================================================
# INJECTABLE FIELD REGISTRY
# ============================================================================

INJECTABLE_FIELDS = {

    # ---- Bank ----
    "bank.account_holder_name":
        _set_bank_account_holder_name,

    "bank.bank_name":
        _set_bank_name,

    "bank.branch":
        _set_bank_branch,

    "bank.ifsc_code":
        _set_bank_ifsc,

    # ---- Identity ----
    "identity.pan":
        _set_identity_pan,

    "identity.aadhar":
        _set_identity_aadhaar,

    # ---- Communication ----
    "communication.linkedin_url":
        _set_communication_linkedin_url,

    # ---- Current Address ----
    "addresses.current.line1":
        _set_address_current_line1,

    "addresses.current.line2":
        _set_address_current_line2,

    "addresses.current.landmark":
        _set_address_current_landmark,

    "addresses.current.city":
        _set_address_current_city,

    "addresses.current.state":
        _set_address_current_state,

    "addresses.current.pin_code":
        _set_address_current_pincode,

    # ---- Permanent Address ----
    "addresses.permanent.line1":
        _set_address_permanent_line1,

    "addresses.permanent.city":
        _set_address_permanent_city,

    "addresses.permanent.state":
        _set_address_permanent_state,

    # ---- Family ----
    "family_members[0].name":
        _set_family_member_name,

    # ---- Education ----
    "education[0].college":
        _set_education_college,

    "education[0].course":
        _set_education_course,

    "education[0].specialization":
        _set_education_specialization,

}