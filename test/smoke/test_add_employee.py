from pages.login_page import LoginPage
from pages.add_employee_page import AddEmployeePage
from test_data.employee_data import ADD_EMPLOYEE_DATA
from utils.test_context import TEST_CONTEXT


def test_add_employee(page):

    login = LoginPage(page)
    employee = AddEmployeePage(page)

    # LOGIN
    login.open()
    login.login_as_super_admin()

    # OPEN ADD EMPLOYEE PAGE
    employee.open()

    employee.fill_employee_details(
        ADD_EMPLOYEE_DATA
    )

    employee.fill_compensation()

    payload = employee.create_employee()

    assert payload["status"] == "success"

    assert TEST_CONTEXT["user_uuid"]
    assert TEST_CONTEXT["emp_code"]

    print(
        f"Employee Created : "
        f"{TEST_CONTEXT['emp_code']}"
    )

    print(
        f"UUID : "
        f"{TEST_CONTEXT['user_uuid']}"
    )