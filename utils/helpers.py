from openpyxl import Workbook, load_workbook
from datetime import datetime
import os

REPORT_FILE = "reports/test_execution_report.xlsx"
FIELD_LOG_FILE = "reports/onboarding_data_log.xlsx"


def create_excel_report():

    if not os.path.exists(REPORT_FILE):
        wb = Workbook()
        ws = wb.active
        ws.title = "Execution Report"
        ws.append([
            "Execution Time",
            "Test Name",
            "Status",
            "Error",
            "Screenshot"
        ])
        wb.save(REPORT_FILE)


def write_result(
    test_name,
    status,
    error="",
    screenshot=""
):

    create_excel_report()
    wb = load_workbook(REPORT_FILE)
    ws = wb["Execution Report"]
    ws.append([
        str(datetime.now()),
        test_name,
        status,
        error,
        screenshot
    ])
    wb.save(REPORT_FILE)


def create_field_log():

    if not os.path.exists(FIELD_LOG_FILE):
        wb = Workbook()
        ws = wb.active
        ws.title = "Onboarding Data Log"
        ws.append([
            "Execution Time",
            "Test Name",
            "Field Name",
            "Field Value",
            "Section"
        ])
        wb.save(FIELD_LOG_FILE)


def write_field_log(test_name, field_data, section="Onboarding"):

    create_field_log()
    wb = load_workbook(FIELD_LOG_FILE)
    ws = wb["Onboarding Data Log"]

    for key, value in field_data.items():
        ws.append([
            str(datetime.now()),
            test_name,
            key,
            str(value),
            section
        ])

    wb.save(FIELD_LOG_FILE)
