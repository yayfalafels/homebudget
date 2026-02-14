---
name: plan-wrapper-design
description: This prompt generates a detailed design plan for the Python wrapper implementation, covering API surface, data model mapping, CLI UX, packaging, and idempotency strategy.
model: Auto (copilot)
agent: agent
---

## Plan: Python Wrapper Design Draft

This plan covers a full design pass for the SQLite-only wrapper, including API surface, module structure, data model and schema mapping, CLI UX flows, packaging, and idempotency guarantees. It is based on the existing reference wrapper and docs, with gaps noted for known issues, schema and conventions that the design must explicitly address. The plan uses the reference implementation in [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py) and related helpers, plus the workflow context in [docs/workflow.md](docs/workflow.md). It also accounts for environment constraints in [docs/develop/environment.md](docs/develop/environment.md) and Python conventions in [.copilot/skills/python/SKILL.md](.copilot/skills/python/SKILL.md). Missing information remains about the HomeBudget SQLite schema and any intended structure under [src/python](src/python), which is currently empty, so the design must derive a schema map from the sample database and codify it in docs and types.

The agent should first digest the HomeBudget Windows Desktop guide in [reference/HomeBudget_Windows_guide.pdf](reference/HomeBudget_Windows_guide.pdf) into a machine friendly markdown reference, then reuse that markdown for all later steps. Any conflicts between the guide and reference code should be logged and resolved with user feedback.

## Development tooling setup

A reusable development environment under [.dev](.dev) supports the design workflow with helper scripts and data analysis tools.

**Directory structure**
- [.dev/env](.dev/env) — Python virtual environment (git ignored)
- [.dev/requirements.txt](.dev/requirements.txt) — Python dependencies for analysis and tooling
- [.dev/.scripts/python](.dev/.scripts/python) — Python helper scripts for PDF extraction, schema analysis
- [.dev/.scripts/bash](.dev/.scripts/bash) — Bash scripts for generic terminal operations
- [.dev/.scripts/cmd](.dev/.scripts/cmd) — Windows batch scripts for generic operations

**Initial setup tasks**
1. Create [.dev/requirements.txt](.dev/requirements.txt) with `pdfplumber`, `pandas`, `sqlalchemy`, and other analysis libraries.
2. Create or activate [.dev/env](.dev/env) virtual environment.
3. Install dependencies from [.dev/requirements.txt](.dev/requirements.txt).
4. Create helper scripts as needed in [.dev/.scripts/python](.dev/.scripts/python), for example `extract_pdf_to_md.py` for Step 1.

Helper scripts are referenced directly in step processes where data extraction or transformation is needed.

## Agent workflow

**Steps**

0. Dev tooling setup
1. Guide digest to markdown
2. Source inventory and gap log
3. SQLite schema and data model mapping
4. Core API surface and module boundaries
5. Idempotency and conflict strategy
6. CLI UX and command map
7. Packaging and repository layout
8. Testing and validation strategy
9. Design documentation and rollout

### Step 0: Dev tooling setup

**Goal**
Initialize the development environment and helper script framework for the design workflow.

**Inputs**
- (initial setup only, no external inputs)

**Process**
- Create [.dev/requirements.txt](.dev/requirements.txt) with libraries: pdfplumber, pandas, sqlalchemy, openpyxl.
- Create [.dev/env](.dev/env) virtual environment.
- Install dependencies.
- Create directory structure [.dev/.scripts/python](.dev/.scripts/python), [.dev/.scripts/bash](.dev/.scripts/bash), [.dev/.scripts/cmd](.dev/.scripts/cmd).

**Expected outputs**
- Initialized [.dev/env](.dev/env) virtual environment.
- [.dev/requirements.txt](.dev/requirements.txt) with dependencies.
- Empty script directories ready for helpers.

**Structured prompt**
```
Set up the development tooling environment:
1. Create .dev/requirements.txt with dependencies: pdfplumber, pandas, sqlalchemy, openpyxl.
2. Create and activate a Python virtual environment at .dev/env.
3. Install all dependencies.
4. Create the script directory structure: .dev/.scripts/python, .dev/.scripts/bash, .dev/.scripts/cmd.
5. Verify .dev/* is in .gitignore if not already there.
```

**Autonomy and clarification**
- Safe to determine autonomously: environment setup, directory creation, dependency list.
- Needs clarification: any additional libraries required for specific analysis or data extraction tasks.

### Step 1: Guide digest to markdown

**Goal**
Create a machine friendly markdown reference for the Windows guide to support later analysis steps.

**Inputs**
- [reference/HomeBudget_Windows_guide.pdf](reference/HomeBudget_Windows_guide.pdf)

**Process**
- Extract headings, feature descriptions, workflows, and terminology from the guide.
- Preserve tables and lists in markdown format.
- Normalize terminology for consistent usage in later steps.

**Expected outputs**
- Markdown guide reference at [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md)
- Glossary of UI terms and feature names
- List of ambiguous or unclear guide sections

**Structured prompt**
```
First, ensure .dev/env is activated. Then:

Convert the Windows guide PDF into a machine friendly markdown reference. Preserve headings, tables, and lists. Add a glossary of UI terms and note any ambiguous sections. Save the output as reference/HomeBudget_Windows_guide.md and cite source page numbers where possible.

Use the helper script at .dev/.scripts/python/extract_pdf_to_md.py to automate PDF extraction if available, otherwise perform extraction using pdfplumber.
```

**Autonomy and clarification**
- Safe to determine autonomously: markdown structure, normalized headings, and glossary formatting.
- Needs clarification: any sections that should be excluded, redacted, or summarized.

**Structured ask_questions tool call**
```
ask_questions
questions:
	- header: GuideFilter
		question: Are there any sections of the Windows guide that should be excluded or summarized only
		options:
			- label: Include all sections
			- label: Summarize non transaction sections
			- label: Exclude specified sections
```

### Step 2: Source inventory and gap log

**Goal**
Build a complete inventory of the current reference implementation and known gaps that affect the design.

**Inputs**
- [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py)
- [reference/hb-finances/database.py](reference/hb-finances/database.py)
- [reference/hb-finances/statements.py](reference/hb-finances/statements.py)
- [reference/hb-finances](reference/hb-finances)
- [docs/workflow.md](docs/workflow.md)
- [docs/issues.md](docs/issues.md)
- Output from Step 1

**Process**
- Extract entities, fields, and behaviors from the reference wrapper and helpers.
- Capture known issues and incomplete areas that must be addressed by the new design.
- Summarize where the reference approach should be reused or replaced.

**Expected outputs**
- Inventory table of entities and functions.
- Gap log with severity and design impact.
- UI alignment notes derived from the guide markdown.

**Structured prompt**
```
Review the reference wrapper and helpers, then produce an inventory of entities, fields, and behaviors. Include a gap log that lists missing features, known issues, and design impact. Extract key UI terms and workflows from the guide markdown and note any conflicts with the reference code. Use sources listed in the inputs and cite links.
```

**Autonomy and clarification**
- Safe to determine autonomously: entity list, helper module roles, existing limitations in the reference code.
- Needs clarification: any conflicts between the guide features and the desired wrapper scope.

**Structured ask_questions tool call**
```
ask_questions
questions:
	- header: GuideScope
		question: Which Windows guide features must the wrapper support in its first design pass
		options:
			- label: Core transaction workflows only
			- label: Full guide scope, including reports and budgeting
			- label: Custom subset to be specified
```

### Step 3: SQLite schema and data model mapping

**Goal**
Derive a precise schema map and data model contracts for the wrapper.

**Inputs**
- [reference/hb-sqlite-db](reference/hb-sqlite-db)
- Output from Step 1
- Output from Step 2

**Process**
- Reverse engineer table structure, key constraints, and relationships.
- Map schema tables to domain entities for expenses, income, transfers, accounts, categories, currencies.

**Expected outputs**
- Schema map table with primary keys, foreign keys, and required fields.
- Domain model mapping, including field names and types.
- UI to schema mapping notes using guide terminology.

**Structured prompt**
```
Inspect the sample SQLite database and derive the schema. Produce a schema map with primary keys, foreign keys, required fields, and relationships. Map each table to a domain entity used by the wrapper. Use the guide markdown to align table semantics to UI terms.
```

**Autonomy and clarification**
- Safe to determine autonomously: table structure, key constraints, inferred relationships.
- Needs clarification: any guide defined entities that do not map cleanly to the database schema.

**Structured ask_questions tool call**
```
ask_questions
questions:
	- header: SchemaMap
		question: When the guide describes features that do not map to a single table, how should the design represent them
		options:
			- label: Composite domain objects with view models
			- label: Service layer only, no new domain objects
			- label: Other, specify approach
```

### Step 4: Core API surface and module boundaries

**Goal**
Define the core Python API and module structure for the wrapper.

**Inputs**
- Output from Step 1
- Output from Step 2
- Output from Step 3

**Process**
- Define module boundaries under [src/python](src/python) and top level package layout.
- Specify main client type such as `HomeBudgetClient` and CRUD method signatures.
- Define data transfer objects aligned to the schema map.
- Identify transfer workflows that require multi table updates and sync detection research.

**Expected outputs**
- API surface list with method signatures.
- Module structure diagram or list.
- Data transfer object catalog.
- UI aligned operation glossary based on the guide markdown.

**Structured prompt**
```
Using the schema map and inventory, design the wrapper API surface and module boundaries. Provide a list of modules, a main client type, CRUD method signatures, and data transfer objects aligned to the schema. Align operation names to the guide markdown terminology. Call out any multi table transaction flows and sync detection logic that needs research.
```

**Autonomy and clarification**
- Safe to determine autonomously: module layout and CRUD method signatures tied to schema.
- Needs clarification: naming conventions when the guide uses different terms than the database.

**Structured ask_questions tool call**
```
ask_questions
questions:
	- header: Naming
		question: When guide terminology differs from database field names, which should be preferred in the public API
		options:
			- label: Guide terminology with aliases
			- label: Database terms only
			- label: Mixed, per entity
```

### Step 5: Idempotency and conflict strategy

**Goal**
Define idempotency rules for all write operations.

**Inputs**
- Output from Step 1
- Output from Step 3
- Output from Step 4

**Process**
- Define unique keys and tokens for each transaction type.
- Specify upsert behavior and conflict resolution rules.
- Document how duplicates are detected and reported.

**Expected outputs**
- Idempotency rules matrix by transaction type.
- Conflict resolution policy list.
- Notes on any guide workflows that imply special idempotency handling.

**Structured prompt**
```
Design idempotency rules for each transaction type. Define unique keys or tokens, safe upsert behavior, conflict resolution policies, and duplicate detection strategy tied to the schema map. Use the guide markdown workflows to confirm expected behavior.
```

**Autonomy and clarification**
- Safe to determine autonomously: token design, upsert and duplicate rules based on schema.
- Needs clarification: any guide workflows that imply user expected overrides or conflict resolution.

**Structured ask_questions tool call**
```
ask_questions
questions:
	- header: Conflicts
		question: When duplicate detection occurs, what should the wrapper do by default
		options:
			- label: Skip and report
			- label: Update existing
			- label: Error and stop
```

### Step 6: CLI UX and command map

**Goal**
Define the CLI UX, commands, and input formats.

**Inputs**
- Output from Step 4
- [docs/workflow.md](docs/workflow.md)
- Output from Step 1

**Process**
- Define commands for add, update, delete, list, and sync.
- Specify input formats and validation rules.
- Ensure outputs are consistent with workflow needs.

**Expected outputs**
- CLI command matrix with examples.
- Validation and error handling guidelines.
- CLI vocabulary aligned to guide terms.

**Structured prompt**
```
Design the CLI UX and command map for the wrapper. Include commands for add, update, delete, list, and sync, with input formats and validation rules aligned to the workflow. Align command names and help text to the guide markdown terms. Provide expected output shapes and error handling rules.
```

**Autonomy and clarification**
- Safe to determine autonomously: command structure, input validation rules, output formats.
- Needs clarification: any preferred command naming that should follow the guide rather than developer conventions.

**Structured ask_questions tool call**
```
ask_questions
questions:
	- header: CliNames
		question: Should CLI commands mirror guide terms or use developer friendly verbs
		options:
			- label: Mirror guide terms
			- label: Developer friendly verbs
			- label: Hybrid, per command
```

### Step 7: Packaging and repository layout

**Goal**
Define packaging layout and repository structure for implementation.

**Inputs**
- Output from Step 4
- [docs/dependencies.md](docs/dependencies.md)
- [docs/repository-layout.md](docs/repository-layout.md)

**Process**
- Define package layout under [src/python](src/python).
- Identify CLI entry points and configuration loading.
- Align planned dependencies with requirements.

**Expected outputs**
- Repository layout proposal.
- Packaging and entry point outline.

**Structured prompt**
```
Propose a packaging layout under src/python, including the main package, submodules, and CLI entry points. Include configuration loading patterns and dependency notes.
```

**Autonomy and clarification**
- Safe to determine autonomously: package layout, entry point choices, dependency alignment.
- Needs clarification: any constraints on distribution targets or naming conventions.

**Structured ask_questions tool call**
```
ask_questions
questions:
	- header: DistTarget
		question: Which distribution target should the packaging design prioritize
		options:
			- label: Internal use, local install only
			- label: Private package index
			- label: Public PyPI release
```

### Step 8: Testing and validation strategy

**Goal**
Define the testing scope and approach.

**Inputs**
- Output from Step 4
- Output from Step 5
- Output from Step 6

**Process**
- Define test categories covering normal, edge, positive, and negative cases.
- Map tests to CRUD workflows, idempotency, and CLI commands.

**Expected outputs**
- Test matrix by feature area.
- Validation checklist for pre release.

**Structured prompt**
```
Define the testing and validation strategy. Provide a test matrix for normal, edge, positive, and negative cases mapped to CRUD operations, idempotency, and CLI commands. Include a validation checklist.
```

**Autonomy and clarification**
- Safe to determine autonomously: core test categories and matrix structure.
- Needs clarification: desired test tooling and any minimum coverage requirements.

**Structured ask_questions tool call**
```
ask_questions
questions:
	- header: Tests
		question: Which test tooling and coverage target should the design assume
		options:
			- label: Pytest with basic coverage
			- label: Pytest with high coverage target
			- label: Other, specify tooling
```

### Step 9: Design documentation and rollout

**Goal**
Document the design and update repository docs.

**Inputs**
- Output from Steps 1 through 8
- [docs/repository-layout.md](docs/repository-layout.md)

**Process**
- Draft the design document with diagrams and tables.
- Update repository layout documentation.

**Expected outputs**
- Design document draft.
- Updated repository layout doc.

**Structured prompt**
```
Assemble the design document using outputs from prior steps. Include diagrams and tables for schema mapping and API reference. Update the repository layout doc with the new structure.
```

**Autonomy and clarification**
- Safe to determine autonomously: doc structure, diagram types, and cross references.
- Needs clarification: target audience for the design document and preferred level of detail.

**Structured ask_questions tool call**
```
ask_questions
questions:
	- header: Audience
		question: Who is the primary audience for the design document
		options:
			- label: Developers only
			- label: Developers and finance users
			- label: Mixed with non technical stakeholders
```

## Verification

- Manual review against the sample database schema and reference code to confirm all required fields and relationships are represented.
- Dry walkthrough of CLI commands against the design to ensure idempotency and CRUD flows are consistent and complete.

## Decisions

- SQLite-only data source.
- Full scope includes CRUD for expenses, income, transfers, and foreign currency support, plus packaging and CLI plan.
- Idempotency guarantees are mandatory for all transaction write operations.