{
    "status": "success",
    "data": {
        "condition_engine": {
            "version": "1.0",
            "description": "Frontend condition processing spec. Parse conditions[] on fields and section_rules[] on sections to drive all dynamic behavior \u2014 no hardcoding required.",
            "operators": {
                "is_true": "Field value is truthy \u2014 checkbox is checked",
                "is_false": "Field value is falsy \u2014 checkbox is unchecked",
                "equals": "Strict equality against the given value",
                "not_equals": "Value does not equal the given value",
                "is_empty": "Value is null \/ undefined \/ empty string",
                "is_not_empty": "Value is present and non-empty"
            },
            "action_types": {
                "copy_section": "Copies every field value from source_section into target_section. When live_sync is true, re-copy on every subsequent change to source_section while the trigger condition remains active.",
                "disable": "Disables all fields in target_section (or target_field for a single field). Disabled fields are still submitted.",
                "enable": "Re-enables all fields in target_section or target_field.",
                "clear": "Clears the values of all fields in target_section or target_field."
            },
            "section_rule_types": {
                "exclusive_checkbox": "In a repeatable section, enforces that only one instance has the named field checked (radio-like behaviour). Obeys min_selected \/ max_selected. When behavior is radio_like, checking one instance automatically unchecks all others.",
                "unique_select": "In a repeatable section, each option for the named select field can be chosen only once across all instances. Options already chosen in any instance are removed from the dropdown of all other instances in real time.",
                "min_instances": "Minimum number of repeatable section instances the user must add.",
                "max_instances": "Maximum number of repeatable section instances the user is allowed to add."
            },
            "cross_validation_types": {
                "not_equal": "The field value must not equal the value of compare_to_field. Evaluated on blur and on submit. scope:local resolves compare_to_field relative to the current section instance; scope:global resolves it as an absolute section.field path."
            },
            "constraint_types": {
                "max_date": "Accepted values: 'today' (dynamic, evaluated at runtime) or an ISO date string. The field value must not be later than this date.",
                "min_date": "Accepted values: 'today' or an ISO date string. The field value must not be earlier than this date."
            }
        },
        "meta": {
            "description": "Defines how the frontend fetches dropdown options for every select field. Static sources are fetched once on form load and cached. Dynamic sources are re-fetched whenever their depends_on field changes. response_map tells the frontend which keys in the API response map to option label and value. data_key is the path to the array inside the response (e.g. 'data' for { status, data: [] }).",
            "sources": {
                "gender": {
                    "type": "static",
                    "endpoint": "\/api\/admin\/master-options\/gender_applicability",
                    "method": "GET",
                    "cache": true,
                    "response_map": {
                        "label": "name",
                        "value": "id",
                        "data_key": "data"
                    }
                },
                "relations": {
                    "type": "static",
                    "endpoint": "\/api\/admin\/master-options\/relations",
                    "method": "GET",
                    "cache": true,
                    "response_map": {
                        "label": "name",
                        "value": "id",
                        "data_key": "data"
                    }
                },
                "education_levels": {
                    "type": "static",
                    "endpoint": "\/api\/admin\/master-options\/education_levels",
                    "method": "GET",
                    "cache": true,
                    "response_map": {
                        "label": "name",
                        "value": "id",
                        "data_key": "data"
                    }
                },
                "countries": {
                    "type": "static",
                    "endpoint": "\/api\/admin\/master-options\/countries",
                    "method": "GET",
                    "cache": true,
                    "response_map": {
                        "label": "name",
                        "value": "id",
                        "data_key": "data"
                    }
                },
                "states": {
                    "type": "static",
                    "endpoint": "\/api\/admin\/master-options\/states",
                    "method": "GET",
                    "cache": true,
                    "response_map": {
                        "label": "name",
                        "value": "id",
                        "data_key": "data"
                    }
                },
                "blood_groups": {
                    "type": "static",
                    "endpoint": "\/api\/admin\/master-options\/blood_group",
                    "method": "GET",
                    "cache": true,
                    "response_map": {
                        "label": "name",
                        "value": "code",
                        "data_key": "data"
                    }
                }
            },
            "lookups": {
                "pincode": {
                    "description": "Called when a valid 6-digit PIN code is entered. Auto-fills city and state in the same address section. If the lookup fails or returns no data, fields remain editable so the user can fill them manually.",
                    "endpoint": "\/api\/admin\/master-options\/pincode-lookup",
                    "method": "GET",
                    "param": "pincode",
                    "data_key": "data",
                    "auto_fill": [
                        {
                            "field": "city",
                            "from_response": "city"
                        },
                        {
                            "field": "state",
                            "from_response": "state_id"
                        },
                        {
                            "field": "country",
                            "from_response": "country_id"
                        }
                    ],
                    "on_success": "disable_auto_filled",
                    "on_clear": "enable_and_clear_auto_filled",
                    "messages": {
                        "loading": "Looking up PIN code...",
                        "not_found": "PIN code not found. Please enter your city and state manually.",
                        "error": "Could not verify this PIN code right now. Please fill in city and state manually."
                    }
                }
            }
        },
        "form": {
            "sections": [
                {
                    "key": "personal",
                    "title": "Personal Information",
                    "fields": [
                        {
                            "name": "gender",
                            "label": "Gender",
                            "type": "select",
                            "options_key": "gender",
                            "required": true,
                            "messages": {
                                "required": "Please select your gender."
                            }
                        },
                        {
                            "name": "date_of_birth",
                            "label": "Date of Birth",
                            "type": "date",
                            "required": true,
                            "validation": "regex:\/^\\d{4}-\\d{2}-\\d{2}$\/",
                            "constraints": {
                                "max_date": "today"
                            },
                            "messages": {
                                "required": "Date of birth is required.",
                                "invalid": "Please enter a valid date of birth.",
                                "max_date": "Date of birth cannot be a future date."
                            }
                        },
                        {
                            "name": "blood_group",
                            "label": "Blood Group",
                            "type": "text",
                            "required": false,
                            "validation": "regex:\/^(A|B|AB|O)[+-]$\/",
                            "messages": {
                                "invalid": "Please enter a valid blood group \u2014 accepted values are A+, A\u2212, B+, B\u2212, O+, O\u2212, AB+, or AB\u2212."
                            }
                        },
                        {
                            "name": "profile_image",
                            "label": "Profile Image",
                            "type": "file",
                            "required": false,
                            "validation": "avatar",
                            "messages": {
                                "invalid": "Only JPG, JPEG, or PNG files are allowed for profile image."
                            }
                        }
                    ]
                },
                {
                    "key": "communication",
                    "title": "Communication Details",
                    "fields": [
                        {
                            "name": "primary_phone",
                            "label": "Primary Phone",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^\\d{10}$\/",
                            "messages": {
                                "required": "Primary phone number is required.",
                                "invalid": "Please enter a valid 10-digit phone number without spaces or special characters."
                            }
                        },
                        {
                            "name": "secondary_phone",
                            "label": "Secondary Phone",
                            "type": "text",
                            "required": false,
                            "validation": "regex:\/^\\d{10}$\/",
                            "cross_validations": [
                                {
                                    "id": "secondary_not_same_as_primary",
                                    "type": "not_equal",
                                    "compare_to_field": "primary_phone",
                                    "scope": "local",
                                    "message": "Secondary phone number cannot be the same as the primary phone number."
                                }
                            ],
                            "messages": {
                                "invalid": "Please enter a valid 10-digit phone number without spaces or special characters."
                            }
                        },
                        {
                            "name": "linkedin_url",
                            "label": "LinkedIn URL",
                            "type": "text",
                            "required": false,
                            "validation": "regex:\/^https:\\\/\\\/(www\\.)?linkedin\\.com\\\/(in|company|pub)\\\/[a-zA-Z0-9\\-_%]+\\\/?$\/",
                            "messages": {
                                "invalid": "Please enter a valid LinkedIn profile URL (e.g., https:\/\/linkedin.com\/in\/your-name)."
                            }
                        }
                    ]
                },
                {
                    "key": "bank",
                    "title": "Bank Details",
                    "fields": [
                        {
                            "name": "account_holder_name",
                            "label": "Account Holder Name",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z\\s]{1,100}$\/",
                            "messages": {
                                "required": "Account holder name is required.",
                                "invalid": "Name must contain only letters and spaces, up to 100 characters."
                            }
                        },
                        {
                            "name": "bank_name",
                            "label": "Bank Name",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z0-9\\s\\.\\,\\-\\&]{1,100}$\/",
                            "messages": {
                                "required": "Bank name is required.",
                                "invalid": "Please enter a valid bank name (max 100 characters)."
                            }
                        },
                        {
                            "name": "branch",
                            "label": "Branch",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z0-9\\s\\.\\,\\-\\&]{1,100}$\/",
                            "messages": {
                                "required": "Branch name is required.",
                                "invalid": "Please enter a valid branch name (max 100 characters)."
                            }
                        },
                        {
                            "name": "account_number",
                            "label": "Account Number",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^\\d{9,18}$\/",
                            "messages": {
                                "required": "Account number is required.",
                                "invalid": "Account number must contain only digits and be between 9 and 18 characters long."
                            }
                        },
                        {
                            "name": "ifsc_code",
                            "label": "IFSC Code",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[A-Z]{4}0[A-Z0-9]{6}$\/",
                            "messages": {
                                "required": "IFSC code is required.",
                                "invalid": "Please enter a valid IFSC code \u2014 4 uppercase letters, followed by 0, then 6 alphanumeric characters (e.g., SBIN0001234)."
                            }
                        }
                    ]
                },
                {
                    "key": "identity",
                    "title": "Identity Details",
                    "fields": [
                        {
                            "name": "aadhar",
                            "label": "Aadhar Number",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^\\d{12}$\/",
                            "messages": {
                                "required": "Aadhar number is required.",
                                "invalid": "Please enter a valid 12-digit Aadhar number."
                            }
                        },
                        {
                            "name": "pan",
                            "label": "PAN Number",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[A-Z]{5}[0-9]{4}[A-Z]$\/",
                            "messages": {
                                "required": "PAN number is required.",
                                "invalid": "Please enter a valid PAN number \u2014 5 uppercase letters, 4 digits, then 1 uppercase letter (e.g., ABCDE1234F)."
                            }
                        },
                        {
                            "name": "uan",
                            "label": "UAN",
                            "type": "text",
                            "required": false,
                            "validation": "regex:\/^\\d{12}$\/",
                            "messages": {
                                "invalid": "Please enter a valid 12-digit Universal Account Number (UAN)."
                            }
                        }
                    ]
                },
                {
                    "key": "addresses.current",
                    "title": "Current Address",
                    "fields": [
                        {
                            "name": "line1",
                            "label": "Address Line 1",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z0-9\\s\\.\\,\\-\\\/\\#\\&']{1,255}$\/",
                            "messages": {
                                "required": "Address Line 1 is required.",
                                "invalid": "Please enter a valid address \u2014 only letters, numbers, and common punctuation are allowed (max 255 characters)."
                            }
                        },
                        {
                            "name": "line2",
                            "label": "Address Line 2",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z0-9\\s\\.\\,\\-\\\/\\#\\&']{1,255}$\/",
                            "messages": {
                                "required": "Address Line 2 is required.",
                                "invalid": "Please enter a valid address \u2014 only letters, numbers, and common punctuation are allowed (max 255 characters)."
                            }
                        },
                        {
                            "name": "country",
                            "label": "Country",
                            "type": "select",
                            "options_key": "countries",
                            "required": true,
                            "messages": {
                                "required": "Please select your country."
                            }
                        },
                        {
                            "name": "pin_code",
                            "label": "PIN Code",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^\\d{6}$\/",
                            "lookup_key": "pincode",
                            "messages": {
                                "required": "PIN code is required.",
                                "invalid": "Please enter a valid 6-digit PIN code."
                            }
                        },
                        {
                            "name": "state",
                            "label": "State",
                            "type": "select",
                            "options_key": "states",
                            "required": true,
                            "messages": {
                                "required": "Please select your state."
                            }
                        },
                        {
                            "name": "city",
                            "label": "City",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z\\s]{1,100}$\/",
                            "messages": {
                                "required": "City is required.",
                                "invalid": "City name must contain only letters (max 100 characters)."
                            }
                        }
                    ]
                },
                {
                    "key": "addresses.permanent",
                    "title": "Permanent Address",
                    "fields": [
                        {
                            "name": "line1",
                            "label": "Address Line 1",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z0-9\\s\\.\\,\\-\\\/\\#\\&']{1,255}$\/",
                            "messages": {
                                "required": "Address Line 1 is required.",
                                "invalid": "Please enter a valid address \u2014 only letters, numbers, and common punctuation are allowed (max 255 characters)."
                            }
                        },
                        {
                            "name": "line2",
                            "label": "Address Line 2",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z0-9\\s\\.\\,\\-\\\/\\#\\&']{1,255}$\/",
                            "messages": {
                                "required": "Address Line 2 is required.",
                                "invalid": "Please enter a valid address \u2014 only letters, numbers, and common punctuation are allowed (max 255 characters)."
                            }
                        },
                        {
                            "name": "country",
                            "label": "Country",
                            "type": "select",
                            "options_key": "countries",
                            "required": true,
                            "messages": {
                                "required": "Please select your country."
                            }
                        },
                        {
                            "name": "pin_code",
                            "label": "PIN Code",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^\\d{6}$\/",
                            "lookup_key": "pincode",
                            "messages": {
                                "required": "PIN code is required.",
                                "invalid": "Please enter a valid 6-digit PIN code."
                            }
                        },
                        {
                            "name": "state",
                            "label": "State",
                            "type": "select",
                            "options_key": "states",
                            "required": true,
                            "messages": {
                                "required": "Please select your state."
                            }
                        },
                        {
                            "name": "city",
                            "label": "City",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z\\s]{1,100}$\/",
                            "messages": {
                                "required": "City is required.",
                                "invalid": "City name must contain only letters (max 100 characters)."
                            }
                        },
                        {
                            "name": "same_as_current",
                            "label": "Same as Current Address",
                            "type": "checkbox",
                            "required": false,
                            "conditions": [
                                {
                                    "id": "sync_permanent_with_current",
                                    "trigger": {
                                        "event": "on_change",
                                        "operator": "is_true"
                                    },
                                    "actions": [
                                        {
                                            "type": "copy_section",
                                            "source_section": "addresses.current",
                                            "target_section": "addresses.permanent",
                                            "exclude_fields": [
                                                "same_as_current"
                                            ],
                                            "live_sync": true
                                        },
                                        {
                                            "type": "disable",
                                            "target_section": "addresses.permanent",
                                            "exclude_fields": [
                                                "same_as_current"
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "id": "unsync_permanent_from_current",
                                    "trigger": {
                                        "event": "on_change",
                                        "operator": "is_false"
                                    },
                                    "actions": [
                                        {
                                            "type": "enable",
                                            "target_section": "addresses.permanent",
                                            "exclude_fields": [
                                                "same_as_current"
                                            ]
                                        },
                                        {
                                            "type": "clear",
                                            "target_section": "addresses.permanent",
                                            "exclude_fields": [
                                                "same_as_current"
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "key": "family_members",
                    "title": "Family Members",
                    "repeatable": true,
                    "section_rules": [
                        {
                            "id": "unique_relation_rule",
                            "type": "unique_select",
                            "field": "relation",
                            "scope": "across_instances",
                            "behavior": "exclude_used",
                            "error_message": "This relation has already been added. Each relation can only appear once."
                        },
                        {
                            "id": "emergency_contact_rule",
                            "type": "exclusive_checkbox",
                            "field": "is_emergency_contact",
                            "scope": "across_instances",
                            "min_selected": 1,
                            "max_selected": 1,
                            "behavior": "radio_like",
                            "error_messages": {
                                "min": "At least one family member must be designated as the emergency contact.",
                                "max": "Only one family member can be the emergency contact at a time."
                            }
                        }
                    ],
                    "fields": [
                        {
                            "name": "relation",
                            "label": "Relation",
                            "type": "select",
                            "options_key": "relations",
                            "required": true,
                            "messages": {
                                "required": "Please select the relation of this family member."
                            }
                        },
                        {
                            "name": "name",
                            "label": "Name",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z\\s]{1,100}$\/",
                            "messages": {
                                "required": "Family member's name is required.",
                                "invalid": "Name must contain only letters and spaces (max 100 characters)."
                            }
                        },
                        {
                            "name": "contact_number",
                            "label": "Contact Number",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^\\d{10}$\/",
                            "cross_validations": [
                                {
                                    "id": "not_same_as_personal_primary",
                                    "type": "not_equal",
                                    "compare_to_field": "communication.primary_phone",
                                    "scope": "global",
                                    "message": "Family member's contact number cannot be the same as your primary phone number."
                                }
                            ],
                            "messages": {
                                "required": "Contact number is required for this family member.",
                                "invalid": "Please enter a valid 10-digit contact number."
                            }
                        },
                        {
                            "name": "is_emergency_contact",
                            "label": "Mark as Emergency Contact",
                            "type": "checkbox",
                            "required": true,
                            "messages": {
                                "required": "Please mark one family member as the emergency contact."
                            }
                        }
                    ]
                },
                {
                    "key": "education",
                    "title": "Education Details",
                    "repeatable": true,
                    "fields": [
                        {
                            "name": "college",
                            "label": "College",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z0-9\\s\\.\\,\\-\\&']{1,255}$\/",
                            "messages": {
                                "required": "College name is required.",
                                "invalid": "Please enter a valid college name (max 255 characters)."
                            }
                        },
                        {
                            "name": "level",
                            "label": "Level",
                            "type": "select",
                            "options_key": "education_levels",
                            "required": true,
                            "messages": {
                                "required": "Please select your education level."
                            }
                        },
                        {
                            "name": "course",
                            "label": "Course",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z0-9\\s\\.\\,\\-\\&']{1,255}$\/",
                            "messages": {
                                "required": "Course name is required.",
                                "invalid": "Please enter a valid course name (max 255 characters)."
                            }
                        },
                        {
                            "name": "specialization",
                            "label": "Specialization",
                            "type": "text",
                            "required": true,
                            "validation": "regex:\/^[a-zA-Z0-9\\s\\.\\,\\-\\&']{1,255}$\/",
                            "messages": {
                                "required": "Specialization is required.",
                                "invalid": "Please enter a valid specialization (max 255 characters)."
                            }
                        },
                        {
                            "name": "passing_year",
                            "label": "Passing Year",
                            "type": "number",
                            "required": true,
                            "validation": "regex:\/^(19[5-9]\\d|20\\d{2})$\/",
                            "messages": {
                                "required": "Passing year is required.",
                                "invalid": "Please enter a valid passing year (e.g., 2020). Accepted range: 1950 to present."
                            }
                        }
                    ]
                }
            ]
        },
        "documents": {
            "required": [
                "aadhar",
                "cancelled_cheque",
                "experience_certificate",
                "pan",
                "relieving_certificate",
                "resume",
                "x_marksheet",
                "xii_marksheet"
            ],
            "optional": [
                "graduate_marksheet",
                "post_graduate_marksheet",
                "salary_slip_2",
                "salary_slip_3",
                "salary_slip_1"
            ],
            "all": [
                {
                    "code": "aadhar",
                    "title": "Aadhar Card",
                    "is_mandatory": true,
                    "validation": "pdf",
                    "messages": {
                        "required": "This document is required. Please upload a PDF copy.",
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "cancelled_cheque",
                    "title": "Cancelled Cheque",
                    "is_mandatory": true,
                    "validation": "pdf",
                    "messages": {
                        "required": "This document is required. Please upload a PDF copy.",
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "experience_certificate",
                    "title": "Experience Certificate",
                    "is_mandatory": true,
                    "validation": "pdf",
                    "messages": {
                        "required": "This document is required. Please upload a PDF copy.",
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "graduate_marksheet",
                    "title": "Graduate Marksheet",
                    "is_mandatory": false,
                    "validation": "pdf",
                    "messages": {
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "pan",
                    "title": "Pan Card",
                    "is_mandatory": true,
                    "validation": "pdf",
                    "messages": {
                        "required": "This document is required. Please upload a PDF copy.",
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "post_graduate_marksheet",
                    "title": "Post Graduate Marksheet",
                    "is_mandatory": false,
                    "validation": "pdf",
                    "messages": {
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "relieving_certificate",
                    "title": "Relieving Certificate",
                    "is_mandatory": true,
                    "validation": "pdf",
                    "messages": {
                        "required": "This document is required. Please upload a PDF copy.",
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "resume",
                    "title": "Resume",
                    "is_mandatory": true,
                    "validation": "pdf",
                    "messages": {
                        "required": "This document is required. Please upload a PDF copy.",
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "salary_slip_2",
                    "title": "Salary Slip 2nd Last Month",
                    "is_mandatory": false,
                    "validation": "pdf",
                    "messages": {
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "salary_slip_3",
                    "title": "Salary Slip 3rd Last Month",
                    "is_mandatory": false,
                    "validation": "pdf",
                    "messages": {
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "salary_slip_1",
                    "title": "Salary Slip Last Month",
                    "is_mandatory": false,
                    "validation": "pdf",
                    "messages": {
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "x_marksheet",
                    "title": "X Marksheet",
                    "is_mandatory": true,
                    "validation": "pdf",
                    "messages": {
                        "required": "This document is required. Please upload a PDF copy.",
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                },
                {
                    "code": "xii_marksheet",
                    "title": "XII Marksheet",
                    "is_mandatory": true,
                    "validation": "pdf",
                    "messages": {
                        "required": "This document is required. Please upload a PDF copy.",
                        "invalid": "Only PDF files are accepted. Please convert your document and try again."
                    }
                }
            ]
        }
    }
}