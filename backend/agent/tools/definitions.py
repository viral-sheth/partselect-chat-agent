TOOL_DEFINITIONS = [
    {
        "name": "search_products",
        "description": (
            "Search for refrigerator or dishwasher parts by description, symptom, keyword, or part number. "
            "Use this when the user is looking for a part or asks about what part they need."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query — describe what the user is looking for",
                },
                "category": {
                    "type": "string",
                    "enum": ["refrigerator", "dishwasher", "any"],
                    "description": "Appliance category to filter by",
                },
                "brand": {
                    "type": "string",
                    "description": "Brand name to filter by (e.g., Whirlpool, Samsung, LG)",
                },
            },
            "required": ["query", "category"],
        },
    },
    {
        "name": "check_compatibility",
        "description": (
            "Check if a specific part is compatible with a specific appliance model number. "
            "Use this when the user provides both a part number and a model number."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "part_number": {
                    "type": "string",
                    "description": "The part number (e.g., PS11752778)",
                },
                "model_number": {
                    "type": "string",
                    "description": "The appliance model number (e.g., WDT780SAEM1)",
                },
            },
            "required": ["part_number", "model_number"],
        },
    },
    {
        "name": "get_installation_guide",
        "description": (
            "Get step-by-step installation instructions for a specific part. "
            "Use when the user asks how to install a part."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "part_number": {
                    "type": "string",
                    "description": "The part number to get installation guide for",
                },
                "model_number": {
                    "type": "string",
                    "description": "Optional model number for more specific instructions",
                },
            },
            "required": ["part_number"],
        },
    },
    {
        "name": "get_troubleshooting",
        "description": (
            "Get troubleshooting guidance for an appliance problem or symptom. "
            "Use when the user describes a problem (e.g., ice maker not working, dishwasher not draining)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symptom": {
                    "type": "string",
                    "description": "Description of the problem or symptom",
                },
                "appliance_type": {
                    "type": "string",
                    "enum": ["refrigerator", "dishwasher"],
                    "description": "Type of appliance",
                },
                "brand": {
                    "type": "string",
                    "description": "Brand of the appliance (optional)",
                },
            },
            "required": ["symptom", "appliance_type"],
        },
    },
    {
        "name": "add_to_cart",
        "description": "Add a part to the customer's shopping cart.",
        "input_schema": {
            "type": "object",
            "properties": {
                "part_number": {
                    "type": "string",
                    "description": "The part number to add to cart",
                },
                "quantity": {
                    "type": "integer",
                    "description": "Quantity to add",
                    "default": 1,
                },
            },
            "required": ["part_number"],
        },
    },
    {
        "name": "get_cart",
        "description": "Get the current contents of the customer's shopping cart.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_order_status",
        "description": "Look up the status of a customer's order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": "The order number",
                },
                "email": {
                    "type": "string",
                    "description": "The email address used for the order",
                },
            },
            "required": ["order_number", "email"],
        },
    },
]
