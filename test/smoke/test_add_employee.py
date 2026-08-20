from pages.add_employee_page import AddEmployeePage
from pages.login_page import LoginPage
from test_data.employee_data import ADD_EMPLOYEE_DATA
from utils.test_context import TEST_CONTEXT

EMPLOYEE_COUNT = 3

def test_add_employee(page):

    login = LoginPage(page)
    employee = AddEmployeePage(page)

    # LOGIN ONLY ONCE
    login.open()
    login.login.login()

    created_employees = []

    for i in range(EMPLOYEE_COUNT):

        print("\n" + "=" * 80)
        print(f"Creating Employee {i + 1} of {EMPLOYEE_COUNT}")
        print("=" * 80)

        # Open Add Employee page
        employee.open()

        # Employment Details
        employee.fill_employee_details(
            ADD_EMPLOYEE_DATA
        )

        # Compensation
        employee.fill_compensation()

        # Additional Details
        employee.fill_additional_details()

        # Documents
        employee.fill_documents()

        # Create Employee
        payload = employee.create_employee()

        # Assertions
        assert payload["status"] == "success"
        assert TEST_CONTEXT["user_uuid"]
        assert TEST_CONTEXT["emp_code"]

        created_employees.append({
            "Employee Code": TEST_CONTEXT["emp_code"],
            "UUID": TEST_CONTEXT["user_uuid"],
            "Name": f"{TEST_CONTEXT['first_name']} {TEST_CONTEXT['last_name']}",
            "Email": TEST_CONTEXT["email"]
        })

        print(f"Employee Created : {TEST_CONTEXT['emp_code']}")
        print(f"UUID : {TEST_CONTEXT['user_uuid']}")

    print("\n\n")
    print("=" * 80)
    print(f"TOTAL EMPLOYEES CREATED : {len(created_employees)}")
    print("=" * 80)

    for emp in created_employees:
        print(
            f"{emp['Employee Code']} | "
            f"{emp['Name']} | "
            f"{emp['Email']}"
        )