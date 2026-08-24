import os
import base64

import resend
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# RESEND CONFIGURATION
# ============================================================

resend.api_key = os.getenv("RESEND_API_KEY")

to_email = os.getenv("HEALTH_MAIL_TO")
from_email = os.getenv(
    "HEALTH_MAIL_FROM",
    "onboarding@resend.dev",
)

if not resend.api_key:
    raise RuntimeError(
        "RESEND_API_KEY is not configured"
    )

if not to_email:
    raise RuntimeError(
        "HEALTH_MAIL_TO is not configured"
    )


# ============================================================
# EXCEL ATTACHMENT
# ============================================================

# Change this path if your Excel file is somewhere else.
#
# Example:
# reports/Run_001/api_health_report.xlsx
#
attachment_path = os.getenv(
    "HEALTH_REPORT_PATH",
    "api_health_report.xlsx",
)

attachments = []

if os.path.exists(attachment_path):

    print(
        f"Attaching health report: {attachment_path}"
    )

    with open(attachment_path, "rb") as f:

        encoded_file = base64.b64encode(
            f.read()
        ).decode("utf-8")

    attachments.append(
        {
            "filename": os.path.basename(
                attachment_path
            ),
            "content": encoded_file,
        }
    )

else:

    print(
        f"WARNING: Attachment not found: "
        f"{attachment_path}"
    )


# ============================================================
# EMAIL
# ============================================================

params = {
    "from": from_email,

    "to": [
        to_email
    ],

    "subject": (
        "HRMS API Health - "
        "Resend Integration Test"
    ),

    "html": """
    <html>
        <body>

            <h2>
                ✅ Resend Integration Successful
            </h2>

            <p>
                This is a test email from the
                HRMS API Health Monitoring Suite.
            </p>

            <table
                border="1"
                cellpadding="8"
                cellspacing="0"
            >

                <tr>
                    <td>
                        <strong>Environment</strong>
                    </td>

                    <td>
                        Development
                    </td>
                </tr>

                <tr>
                    <td>
                        <strong>Status</strong>
                    </td>

                    <td>
                        CONNECTED
                    </td>
                </tr>

                <tr>
                    <td>
                        <strong>
                            Notification Provider
                        </strong>
                    </td>

                    <td>
                        Resend
                    </td>
                </tr>

            </table>

            <br>

            <p>
                The Python health suite successfully
                connected to Resend and submitted
                an email.
            </p>

            <p>
                The API health Excel report is attached
                to this email.
            </p>

        </body>
    </html>
    """,

    "attachments": attachments,
}


# ============================================================
# SEND EMAIL
# ============================================================

email = resend.Emails.send(params)

print(
    "Email submitted successfully."
)

print(email)