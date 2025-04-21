# This module defines a registry of form schemas for dynamic form rendering
# Each schema defines the fields, types, and (optionally) dynamic value sources for a given form

FORM_SCHEMAS = {
    "spending_form": {
        "fields": [
            {
                "name": "amount",
                "label": "Amount",
                "type": "integer",
                "required": True
            },
            {
                "name": "category",
                "label": "Category",
                "type": "select",
                "fetchValuesFrom": "/api/categories/"
            },
            {
                "name": "notes",
                "label": "Notes",
                "type": "text",
                "required": False
            }
        ]
    },
    "profile_update_form": {
        "fields": [
            {
                "name": "full_name",
                "label": "Full Name",
                "type": "text",
                "required": True
            },
            {
                "name": "email",
                "label": "Email",
                "type": "email",
                "required": True
            },
            {
                "name": "mobile",
                "label": "Mobile Number",
                "type": "text",
                "required": False
            }
        ]
    }
}

def get_form_schema(form_name):
    return FORM_SCHEMAS.get(form_name)
