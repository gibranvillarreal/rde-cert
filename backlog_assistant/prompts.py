SYSTEM_PROMPT = """You are a senior business analyst and product manager helping an engineering team \
structure their work. Your job is to turn unstructured meeting notes and requirement documents \
into clear, actionable backlog items.

You write user stories that are:
- Specific and testable, never vague
- Sized for a single sprint (split anything larger)
- Written from the user's perspective, not the system's
- Backed by concrete acceptance criteria a QA engineer could verify

You are concise and direct. You do not pad output or add unnecessary commentary."""


EXTRACTION_PROMPT = """Extract all software requirements from the following meeting notes.

Rules:
- Each requirement must describe a single, atomic piece of functionality
- Use plain language — no jargon, no assumptions beyond what is stated
- Do not merge requirements together
- Do not invent requirements that are not in the notes
- Ignore non-requirements (scheduling, pleasantries, action items unrelated to software)

Output format: a numbered list, one requirement per line. Nothing else.

Meeting notes:
{notes}"""


DEDUP_PROMPT = """You are reviewing a list of new requirements against an existing product backlog.

Your task: identify which requirements are already covered by existing backlog items.

A requirement is a DUPLICATE if an existing backlog item addresses the same functionality, \
even if worded differently.
A requirement is NEW if no existing backlog item covers it.

Existing backlog:
{backlog}

New requirements:
{requirements}

Respond in this exact JSON format:
{{
  "new": ["requirement text", ...],
  "duplicates": [
    {{"requirement": "requirement text", "matched_item": "title of matching backlog item"}},
    ...
  ]
}}

Return only the JSON. No explanation."""


GENERATION_PROMPT = """Convert each of the following requirements into a structured user story \
using the create_user_story tool. Call the tool once per requirement.

Requirements to convert:
{requirements}

---
Guidelines:
- Choose the user role (as_a) based on who directly benefits from this feature
- Make acceptance_criteria testable by a QA engineer — avoid "should work" or "is easy to use"
- Set priority based on business value: high=blocks other work or critical user path, \
low=nice to have
- Set complexity based on engineering effort: small=hours, medium=1-3 days, large=week+

Example of a well-formed story (for reference only, do not copy):
- title: "Export dashboard data to CSV"
- as_a: "data analyst"
- i_want: "to export any dashboard view as a CSV file"
- so_that: "I can analyze the data in Excel without manual copy-paste"
- acceptance_criteria: [
    "Export button appears on all dashboard views",
    "Downloaded file is valid CSV with correct headers",
    "Export handles up to 10,000 rows without timeout",
    "Empty dashboards show a clear message instead of exporting blank file"
  ]
- priority: "medium"
- category: "feature"
- estimated_complexity: "small"
"""


CRITIQUE_PROMPT = """Review the following user stories and identify quality issues.

For each story, check:
1. Is it too vague? (e.g. "improve performance" with no specifics)
2. Is it too large? (could take more than a week — should be split)
3. Are acceptance criteria testable? (reject criteria like "works correctly" or "is fast")
4. Is the user role specific enough? (reject "user" — who exactly?)

User stories to review:
{stories}

For each issue found, provide a specific, corrected version of that story.
For stories with no issues, do not mention them.

IMPORTANT: In the `original_title` field, copy the title exactly as it appears in the
input — same capitalisation, same punctuation. Do not paraphrase or reformat it.

Respond in this exact JSON format:
{{
  "has_issues": true or false,
  "refined_stories": [
    {{
      "original_title": "...",
      "issue": "one sentence describing the problem",
      "corrected_story": {{
        "title": "...",
        "as_a": "...",
        "i_want": "...",
        "so_that": "...",
        "acceptance_criteria": ["...", "..."],
        "priority": "high|medium|low",
        "category": "feature|bug|tech-debt|research",
        "estimated_complexity": "small|medium|large"
      }}
    }}
  ],
  "summary": "2-3 sentence summary of requirements found and stories generated"
}}

Return only the JSON. No explanation."""
