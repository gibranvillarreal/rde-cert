USER_STORY_SCHEMA = {
    "name": "create_user_story",
    "description": (
        "Create a single structured user story from a software requirement. "
        "Call this tool once per requirement."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Short story title in imperative form, max 10 words (e.g. 'Add export to CSV feature')",
            },
            "as_a": {
                "type": "string",
                "description": "The user role who benefits (e.g. 'product manager', 'developer', 'end user')",
            },
            "i_want": {
                "type": "string",
                "description": "The specific action or capability the user needs",
            },
            "so_that": {
                "type": "string",
                "description": "The business value or outcome achieved",
            },
            "acceptance_criteria": {
                "type": "array",
                "items": {"type": "string"},
                "description": "2-4 testable conditions that confirm this story is complete. Each must be independently verifiable.",
                "minItems": 2,
                "maxItems": 4,
            },
            "priority": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Business priority based on value and urgency",
            },
            "category": {
                "type": "string",
                "enum": ["feature", "bug", "tech-debt", "research"],
                "description": "Type of work this story represents",
            },
            "estimated_complexity": {
                "type": "string",
                "enum": ["small", "medium", "large"],
                "description": "Rough engineering effort: small=hours, medium=days, large=week+",
            },
        },
        "required": [
            "title",
            "as_a",
            "i_want",
            "so_that",
            "acceptance_criteria",
            "priority",
            "category",
            "estimated_complexity",
        ],
    },
}
