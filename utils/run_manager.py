import os
import sys
_RUN_FOLDER = None

def get_run_type():

    for arg in sys.argv:

        if (
            arg.endswith(".py")
            and "test_" in arg
        ):

            filename = os.path.basename(arg)

            filename = filename.replace(
                ".py",
                ""
            )

            filename = filename.replace(
                "test_",
                ""
            )

            return filename.title().replace(
                "_",
                ""
            )

    return "General"


def get_run_folder():

    global _RUN_FOLDER

    if _RUN_FOLDER:
        return _RUN_FOLDER

    reports_dir = "reports"

    os.makedirs(
        reports_dir,
        exist_ok=True
    )

    existing = []

    for name in os.listdir(reports_dir):

        full_path = os.path.join(
            reports_dir,
            name
        )

        if (
            name.startswith("Run_")
            and os.path.isdir(full_path)
        ):

            try:

                run_number = (
                    name.split("_")[1]
                )

                existing.append(
                    int(run_number)
                )

            except Exception:
                pass

    next_run = (
        max(existing) + 1
        if existing
        else 1
    )

    run_type = get_run_type()

    _RUN_FOLDER = os.path.join(
        reports_dir,
        f"Run_{next_run:03d}_{run_type}"
    )

    subfolders = [
        "excel",
        "screenshots",
        "html",
        "api_failures",
        "logs"
    ]

    for folder in subfolders:
        os.makedirs(
            os.path.join(
                _RUN_FOLDER,
                folder
            ),
            exist_ok=True
        )


    return _RUN_FOLDER