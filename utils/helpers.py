from openpyxl import Workbook, load_workbook
from datetime import datetime
import os

from utils.run_manager import (
    get_run_folder
)

RUN_FOLDER = get_run_folder()

EXCEL_FOLDER = os.path.join(
    RUN_FOLDER,
    "excel"
)

os.makedirs(
    EXCEL_FOLDER,
    exist_ok=True
)

os.makedirs(
    EXCEL_FOLDER,
    exist_ok=True
)

REPORT_FILE = os.path.join(
    EXCEL_FOLDER,
    "test_execution_report.xlsx"
)

FIELD_LOG_FILE = os.path.join(
    EXCEL_FOLDER,
    "onboarding_data_log.xlsx"
)
API_LOG_FILE = os.path.join(
    EXCEL_FOLDER,
    "api_execution_log.xlsx"
)

# ==========================================================
# TEST EXECUTION REPORT
# ==========================================================

def create_excel_report():

    if not os.path.exists(REPORT_FILE):

        wb = Workbook()

        ws = wb.active

        ws.title = "Execution Report"

        ws.append([
            "Candidate Name",
            "Candidate Email",
            "Execution Time",
            "Test Name",
            "Status",
            "Action",
            "API Status",
            "API Message",
            "API Response",
            "Error",
            "Screenshot"
        ])

        wb.save(REPORT_FILE)

        print(
            f"[EXCEL CREATED] {REPORT_FILE}"
        )


def write_result(
    test_name,
    status,
    error="",
    screenshot="",
    action="",
    candidate_name="",
    candidate_email="",
    api_status="",
    api_message="",
    api_response=""
):

    create_excel_report()

    wb = load_workbook(REPORT_FILE)

    ws = wb["Execution Report"]

    ws.append([
        candidate_name,
        candidate_email,
        str(datetime.now()),
        test_name,
        status,
        action,
        api_status,
        api_message,
        api_response,
        error,
        screenshot
    ])
    wb.save(REPORT_FILE)
    print(
        f"[REPORT UPDATED] {REPORT_FILE}"
    )


# ==========================================================
# ONBOARDING DATA LOG
# ONE TEST EXECUTION = ONE ROW
# ==========================================================

def create_field_log():

    if not os.path.exists(FIELD_LOG_FILE):

        wb = Workbook()

        ws = wb.active

        ws.title = "Onboarding Data Log"

        ws.append([
            "Execution Time",
            "Test Name",

            # Employee Details
            "First Name",
            "Middle Name",
            "Last Name",
            "Email",

            # Job Details
            "Job Offered",
            "Department",
            "Job Title",
            "Manager",

            # Employment Details
            "Employment Type",
            "Company Entity",
            "Salary Structure",

            # Additional Information
            "Section"
        ])

        wb.save(FIELD_LOG_FILE)

        print(
            f"[EXCEL CREATED] {FIELD_LOG_FILE}"
        )


def write_field_log(
    test_name,
    field_data,
    section="Onboarding"
):

    create_field_log()

    wb = load_workbook(FIELD_LOG_FILE)
    ws = wb["Onboarding Data Log"]

    # ==========================================
    # Existing headers
    # ==========================================
    headers = [
        cell.value
        for cell in ws[1]
    ]

    # ==========================================
    # Required base columns
    # ==========================================
    base_data = {
    "execution_time": str(datetime.now()),
    "test_name": test_name,
    **field_data,
    "section": section
    }

    # ==========================================
    # Add new columns automatically
    # ==========================================
    for key in base_data.keys():

        header = key.replace("_", " ").title()

        if header not in headers:

            ws.cell(
                row=1,
                column=len(headers) + 1,
                value=header
            )

            headers.append(header)

    # ==========================================
    # Build row according to headers
    # ==========================================
    row = []

    for header in headers:

        lookup_key = (
            header
            .lower()
            .replace(" ", "_")
        )

        row.append(
            base_data.get(
                lookup_key,
                ""
            )
        )

    print("\n===== FIELD DATA RECEIVED =====")

    for k, v in field_data.items():
        print(k, "=", v)

    print("Field Count =", len(field_data))

    ws.append(row)

    print(
        f"\nWriting row to Excel. "
        f"Row Length={len(row)} "
        f"Headers={len(headers)}"
    )

    wb.save(FIELD_LOG_FILE)
    print(
        f"[FIELD LOG UPDATED] {FIELD_LOG_FILE}"
    )

# ==========================================================
# API EXECUTION LOG
# ==========================================================

def create_api_log():

    if not os.path.exists(
            API_LOG_FILE
    ):

        wb = Workbook()

        ws = wb.active

        ws.title = (
            "API Execution Log"
        )
        

        ws.append([
            "Execution Time",
            "Run ID",
            "Environment",
            "Username",
            "Test Name",
            "Method",
            "Endpoint",
            "Status Code",
            "Expected Status",
            "Actual Status",
            "Duration(ms)",
            "SLA(ms)",
            "SLA Status",
            "Result",
            "Request Payload",
            "Response Body",
            "Error"
        ])

        wb.save(
            API_LOG_FILE
        )

        print(
            f"[EXCEL CREATED] "
            f"{API_LOG_FILE}"
        )


def write_api_log(
        test_name,
        method,
        endpoint,
        status_code,
        run_id="",
        environment="",
        username="",
        expected_status="",
        actual_status="",
        duration="",
        sla="",
        sla_status="",
        result="",
        request_payload="",
        response_body="",
        error=""
):

    create_api_log()

    wb = load_workbook(
        API_LOG_FILE
    )

    ws = wb[
        "API Execution Log"
    ]

    ws.append([
        str(datetime.now()),
        run_id,
        environment,
        username,
        test_name,
        method,
        endpoint,
        status_code,
        expected_status,
        actual_status,
        duration,
        sla,
        sla_status,
        result,
        request_payload,
        response_body,
        error
    ])

    wb.save(
        API_LOG_FILE
    )

    print(
        f"[API LOG UPDATED] "
        f"{API_LOG_FILE}"
    )