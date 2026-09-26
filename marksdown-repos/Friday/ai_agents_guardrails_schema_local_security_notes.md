# AI Agents: Architecture Guardrails, Schema-Driven Generation & Local Agent Security

**Source:** https://wellington.aitinkerers.org/talks/rsvp_qfaqOJP3MfU

## 1. Architecture Rules Are Not Enough

The talk starts with a common problem: teams write large Markdown files describing how their software should be built, including:

- Architecture rules
- Coding guidance
- Examples
- Rules that agents must follow
- Softer recommendations

But documentation alone does not guarantee compliance. AI agents can forget rules, ignore them, or choose an implementation that violates the architecture.

This problem existed even before AI agents: large engineering teams could have extensive documentation, but developers would still accidentally violate architectural constraints.

### The solution: Architecture Testing

Architecture testing turns architectural decisions into **machine-executable tests**.

Instead of only saying:

> "Repositories should not depend on the domain integration layer."

You create an automated test that checks the dependency structure of the application.

### Linting vs Architecture Testing

**Linting** usually checks detailed code-level conventions:

- Formatting
- Naming
- Small syntax/style rules
- Specific code patterns

**Architecture testing** checks the structure of the system:

- Which packages can depend on which?
- What is a repository?
- What is a domain object?
- Which layers can communicate?
- Which constructs are allowed?
- What relationships are permitted?

So architecture tests operate at a higher structural level.

---

# 2. Give Architecture Rules IDs

A later improvement was to assign every architecture rule an ID.

For example:

```text
ARCH-001
ARCH-002
ARCH-003
...
```

The architecture tests reference these IDs.

This creates a useful connection:

```text
Architecture Documentation
        |
        | Rule ID
        v
Architecture Test
        |
        v
Pass / Fail
```

When an agent sees a failed test, it can identify the exact rule that was violated and locate the relevant documentation.

### Why this helps

Without IDs:

```text
Test failed
   ↓
"What rule did I break?"
   ↓
Search through hundreds of lines
```

With IDs:

```text
ARCH-017 failed
   ↓
Find ARCH-017
   ↓
Read rationale + guidance
   ↓
Fix implementation
```

---

# 3. The Bigger Problem: Two Sources of Truth

Initially there were two representations of the same architecture:

1. Markdown documentation
2. Executable architecture tests

That creates **documentation drift**.

For example:

```text
Markdown says:
Repository → Domain = NOT ALLOWED

Architecture test says:
Repository → Domain = ALLOWED
```

Now the team has two conflicting definitions.

The speaker also described managing multiple projects. Keeping architecture rules synchronized across several repositories made this problem even harder.

---

# 4. Make the Code the Source of Truth

The next approach was to define architecture constructs directly beside the architecture tests.

Instead of maintaining a separate Markdown copy, the code contains:

- Construct definitions
- Rule definitions
- Short descriptions
- Rationale
- Actual executable test logic

Conceptually:

```text
Architecture Construct
        |
        +-- Description
        +-- Rationale
        +-- Rules
        +-- Executable Test
```

The important idea is:

> **Define the rule once, then generate the human-readable documentation from it.**

---

# 5. Generate Markdown Automatically

The architecture framework generates Markdown documentation from the rule definitions.

This provides both:

### Machine-readable enforcement

```text
Architecture Test
       ↓
Run automatically
       ↓
PASS / FAIL
```

### Human/AI-readable documentation

```text
Rule definitions
       ↓
Documentation generator
       ↓
Markdown
```

The generated Markdown can be checked into the repository and versioned with the code.

---

# 6. Global Rule Index

A useful generated artifact is a **global rule index**.

Example:

```text
ARCH-001  Repository dependency rule      TESTED
ARCH-002  Domain layer rule               TESTED
ARCH-003  Naming convention               GUIDANCE
ARCH-004  Dependency direction             TESTED
```

This makes it easy for:

- Humans to understand the architecture
- Agents to locate rules
- Developers to see enforcement status
- CI/CD systems to validate compliance

When a test fails, the agent can start at the index and drill into the specific rule.

---

# 7. Progressive Disclosure Solves Context-Window Problems

A major concern is:

> "If we generate hundreds of lines of architecture documentation, won't the agent drown in context?"

The answer is **progressive disclosure**.

Instead of putting everything into one huge Markdown file:

```text
Architecture README
       |
       +-- Rule Index
       |
       +-- Feature Layer Rules
       |
       +-- Data Layer Rules
       |
       +-- Domain Rules
       |
       +-- Individual Rule Details
```

The root README stays small.

An agent initially reads only:

```text
Here are the architecture rules.
Here is the rule index.
Look here when something fails.
```

If `ARCH-017` fails, it reads only the relevant rule documentation.

### Result

Instead of:

```text
Read 1,000 lines every time
```

you get:

```text
Read small index
      ↓
Identify relevant rule
      ↓
Read only that rule
```

This reduces unnecessary context consumption.

---

# 8. Strict Rules vs Guidance

Not everything should become a machine-enforced rule.

Some engineering practices are subjective.

For example:

> Prefer the Builder Pattern.

This is difficult to turn into a universal test because the correct question is:

> When should a Builder Pattern be used?

Sometimes it is appropriate; sometimes it is not.

Therefore:

### Strict rule

Use when the requirement can be objectively tested.

Example:

```text
Use cases MUST NOT directly access the data layer.
```

### Guidance

Use when engineering judgment is required.

Example:

```text
Prefer Builder Pattern when object construction is complex.
```

A good architecture system therefore contains both:

```text
Architecture
├── Enforced Rules
│   └── Machine-testable
│
└── Guidance
    └── Human/AI judgment
```

---

# 9. Architecture Can Be More Complex Than Naming Rules

Architecture testing is not limited to simple rules such as:

```text
Class name must start with X
```

It can express relationships between constructs.

For example:

```text
Domain Interface
       ↑
       |
Use Case
       |
       X
       |
Data Layer
```

A use case may implement a domain interface but must not directly access the data layer.

Repositories may implement specific domain interfaces, but they cannot arbitrarily inject domain interfaces.

The important point is that architecture testing can describe:

- Membership
- Dependencies
- Relationships
- Layer boundaries
- Allowed providers
- Forbidden consumers

---

# 10. Evidence: Do Architecture Tests Actually Help?

The speaker examined transcripts from multiple projects to see whether architecture tests actually caught useful violations.

The talk reports:

- Architecture tests were run **136 times with failures**
- Many failures were expected during rule development/TDD
- Around **39 failures were considered genuine violations**
- These represented cases where the agent had implemented something and the final architecture check revealed that a rule had been broken

One described pattern was:

```text
Agent writes code
      ↓
Architecture test fails
      ↓
Agent tries a workaround
      ↓
Test fails again
      ↓
Agent reads the linked documentation
      ↓
"Oh — I understand the intended architecture."
      ↓
Agent moves the implementation
```

This is important because the architecture test does more than reject code.

It can **redirect the agent toward the intended design**.

---

# 11. The Key Idea: Guidelines vs Guardrails

The central message of the first section is:

> **A guideline that is not enforced is much weaker than a guardrail.**

For human developers, documentation can be enough in many situations.

For autonomous agents working in parallel, relying entirely on documentation becomes risky.

The model may:

- Forget a rule
- Misinterpret a rule
- Ignore a rule
- Choose a convenient workaround

Architecture tests create a deterministic boundary.

```text
LLM
 |
 | generates implementation
 v
Architecture Tests
 |
 +---- PASS → Continue
 |
 +---- FAIL → Read rule → Correct implementation
```

---

# 12. Schema-Driven Slide Deck Generation

The second presentation demonstrated a different application of the same general idea:

> Give an LLM a strict schema instead of asking it to freely generate everything.

The system is designed to generate slide decks and related content programmatically.

The stack described included:

- Bun
- Puppeteer
- JSON/YAML
- Mermaid diagrams
- Structured slide types
- Image prompts
- A compiler/validator

---

# 13. Define the Slide Schema

Instead of asking:

> "Create me a presentation."

The system defines explicit types for what a slide can contain.

Conceptually:

```text
Deck
 |
 +-- Theme
 |
 +-- Slide
 |    |
 |    +-- Title
 |    +-- Text
 |    +-- Image
 |    +-- Diagram
 |    +-- Grid
 |    +-- Map
 |    +-- Code
 |
 +-- Configuration
```

The schema tells the model what is valid.

---

# 14. Compiler + Validator

The workflow is roughly:

```text
Natural Language Request
          |
          v
     LLM Prompt
          |
          v
   Structured Schema
          |
          v
      Validator
          |
     +----+----+
     |         |
   Valid     Invalid
     |         |
     v         v
  Render     Error
     |         |
     +----<----+
       Fix
```

If the LLM generates invalid structured data:

1. The validator reports the problem.
2. The output is given back to the model.
3. The model fixes the structure.
4. The deck is rendered.

This is another example of combining:

**LLM flexibility + deterministic validation.**

---

# 15. Natural Language Becomes the Interface

The speaker's goal was not to make the user manually edit YAML.

Instead:

```text
User:
"Make a seasonal fruit guide."

        ↓

LLM

        ↓

Structured deck definition

        ↓

Validator

        ↓

Slide rendering
```

The user can give plain-language feedback such as:

> "Move this slide."

or

> "I don't like this layout."

The system handles the structured representation behind the scenes.

### Why this matters

The LLM becomes a natural-language interface to a structured system.

The user does not need to know the underlying schema.

---

# 16. Local AI Attendance System

Another demonstration showed a completely local AI attendance/check-in system.

The motivation was a school check-in process that was previously paper-based.

The goal was:

- Face recognition
- Check-in/check-out
- Attendance lookup
- Voice interaction
- Policy question answering
- Anti-spoofing
- No cloud dependency

---

# 17. Technology Stack

The demo used technologies including:

```text
Flask
   ↓
Web application

OpenCV
   ↓
Camera / computer vision

DeepFace
   ↓
Face recognition

Whisper
   ↓
Speech → Text

Local models
   ↓
AI processing

SQLite
   ↓
Attendance data

RAG / vector database
   ↓
Policy documents
```

The emphasis was on running the system locally rather than sending sensitive data to external APIs.

---

# 18. How the Attendance Flow Works

A simplified flow:

```text
Camera
  |
  v
Face Detection
  |
  v
Face Recognition
  |
  v
Identify Person
  |
  v
Check-in / Check-out
  |
  v
SQLite
```

The demo also used a local JSON relationship structure to associate people with relevant details.

---

# 19. AI Assistant + Database

The system included an AI assistant that could answer operational questions such as:

> Who is currently checked in?

The assistant retrieves the information from SQLite.

So:

```text
User Question
      |
      v
AI Assistant
      |
      v
SQLite Query
      |
      v
Attendance Data
      |
      v
Natural Language Answer
```

This is a practical example of an LLM sitting on top of deterministic application data.

---

# 20. RAG for Policy Questions

The assistant could also answer questions about school policies.

The workflow was:

```text
Policy PDF
    ↓
Chunk / Index
    ↓
Vector Database
    ↓
User Question
    ↓
Retrieval
    ↓
Relevant Policy Content
    ↓
LLM
    ↓
Answer
```

This is a classic **Retrieval-Augmented Generation (RAG)** pattern.

The advantage is that the model does not need to memorize the policy. It retrieves the relevant source material at query time.

---

# 21. Anti-Spoofing

The attendance system also demonstrated an anti-spoofing capability.

The purpose is to prevent someone from simply presenting a photo or another representation of an enrolled person to fool the face-recognition system.

The demo displayed a:

```text
Spoof detected
```

result when the system determined that the input was not a genuine live person.

---

# 22. Why Local AI?

The presenter emphasized privacy.

For sensitive information, sending data to public APIs may be undesirable.

A local architecture can look like:

```text
Camera
   |
   v
Local AI Model
   |
   +---- SQLite
   |
   +---- Local Vector DB
   |
   +---- Local RAG
```

No external API is required for the core workflow.

The trade-off is that local AI requires appropriate local compute and operational maintenance.

---

# 23. The Security Problem With Local Coding Agents

The final section moves to a major issue:

> **A coding agent running locally may have far more access than the developer realizes.**

A developer may think:

```text
Claude Code
    ↓
My Project Directory
```

But the actual permission boundary can be closer to:

```text
Claude Code
    ↓
My User Account
    ↓
Home Directory
    ↓
AWS Credentials
SSH Keys
.env files
Other Projects
Cloud Resources
```

That is a much larger blast radius.

---

# 24. Prompt Injection Is a Real Security Risk

An agent may encounter malicious instructions in:

- GitHub issues
- Documentation
- Source code
- Web pages
- Files
- Third-party content

An injected instruction could attempt to make the agent:

- Read credentials
- Search other directories
- Access unrelated projects
- Call external services
- Exfiltrate sensitive information
- Delete or modify files

The core security problem is:

```text
Untrusted Input
      ↓
LLM interprets it as instructions
      ↓
Agent has broad permissions
      ↓
Potential damage
```

---

# 25. Why Sandboxing Helps

A strong security boundary is to run the agent in an isolated environment.

### Option 1 — Virtual Machine

```text
Host Machine
     |
     +-------------------+
     |                   |
     |   Agent VM        |
     |                   |
     |   Agent           |
     |      ↓            |
     |   Project Files   |
     +-------------------+
```

If host files are not shared, the agent cannot directly access them.

### Option 2 — Container

Containers provide another isolation layer.

However, the speaker highlights that container configuration matters. Simply putting an agent into Docker does not automatically eliminate every privilege or escape risk.

The security properties depend on:

- User privileges
- Mounted directories
- Host access
- Container configuration
- Network access

---

# 26. A Lightweight Alternative: Separate OS Users

The speaker's preferred local solution was surprisingly old-school:

> **Use separate operating-system user accounts.**

Instead of running the coding agent as your primary account:

```text
ankur
  |
  +-- personal files
  +-- AWS credentials
  +-- SSH keys
  +-- other projects
```

create dedicated agent users:

```text
agent-personal
agent-demo
agent-operational
```

Then give each user only the permissions it needs.

Example:

```text
agent-demo
   |
   +-- Project A      READ/WRITE
   |
   +-- Project B      DENIED
   |
   +-- AWS credentials DENIED
   |
   +-- SSH keys        DENIED
```

---

# 27. ACLs: Fine-Grained Folder Permissions

On macOS, the presenter used **Access Control Lists (ACLs)** to grant permissions to specific directories.

For example:

```text
Project A
    |
    +-- agent-demo → READ/WRITE

Project B
    |
    +-- agent-demo → DENIED
```

The agent can work normally inside its permitted project while being unable to access unrelated directories.

This creates a much smaller blast radius.

---

# 28. Defense in Depth

The most important security lesson is not to rely on a single protection.

A stronger architecture combines multiple layers:

```text
                AI Agent
                   |
        +----------+----------+
        |                     |
   OS User Isolation     Sandbox/Container
        |                     |
        +----------+----------+
                   |
             File ACLs
                   |
             Network Rules
                   |
          Limited Project Access
```

If one protection fails, another layer can still prevent access.

---

# 29. Example of the Protection Working

The presenter demonstrated that an agent attempting to access a protected directory received an access/sandbox-blocked result.

The intended model is:

```text
Agent:
"Let me search outside this project."

        ↓

OS permissions / ACL
        ↓
ACCESS DENIED

        ↓

Agent cannot retrieve the data
```

This is much stronger than merely telling the LLM:

> "Please don't access that directory."

The latter is a guideline.

The former is an actual security boundary.

---

# 30. The Bigger Architecture Pattern

Across all three demonstrations, the same design philosophy appears.

### Don't ask the LLM to be the security/control mechanism.

Instead:

```text
             LLM
              |
       Reason / Generate
              |
              v
   +----------------------+
   | Deterministic Layer  |
   |                      |
   | Architecture Tests   |
   | Schema Validation    |
   | OS Permissions       |
   | ACLs                  |
   | Sandboxing            |
   | Database              |
   +----------------------+
              |
              v
         Safe Action
```

The LLM is good at:

- Reasoning
- Natural language
- Generating code
- Creating structured output
- Interpreting user intent

Deterministic systems are better at:

- Enforcing permissions
- Validating schemas
- Enforcing architecture
- Controlling access
- Checking relationships
- Rejecting invalid operations

---

# 31. Practical AI Architect Takeaways

## 1. Turn important architecture decisions into executable rules

Don't stop at:

```text
"Agents should follow our architecture."
```

Build:

```text
Architecture Rule
        ↓
Automated Test
        ↓
CI / Agent Feedback
```

## 2. Maintain one source of truth

Avoid:

```text
Documentation
+
Separate Tests
```

when they describe the same thing.

Prefer:

```text
Executable Rule Definitions
        ↓
Generated Documentation
```

## 3. Use progressive disclosure

Don't inject the entire architecture into every prompt.

Use:

```text
Short Index
   ↓
Relevant Rule
   ↓
Detailed Explanation
```

## 4. Separate rules from guidance

Make objective requirements machine-enforced.

Keep judgment-heavy recommendations as guidance.

## 5. Put schemas around LLM outputs

Instead of free-form generation:

```text
LLM → arbitrary output
```

use:

```text
LLM
 ↓
Schema
 ↓
Validator
 ↓
Compiler / Renderer
```

## 6. Give agents minimum required permissions

Don't run agents with your full developer identity if they don't need it.

Use:

- Dedicated OS users
- ACLs
- Containers
- VMs
- Restricted mounts
- Network restrictions

## 7. Treat external content as untrusted

Anything the agent reads can potentially contain instructions.

Think:

```text
Web page
GitHub issue
README
PDF
Source code
Ticket
   ↓
UNTRUSTED INPUT
   ↓
Agent
```

## 8. Defense in depth beats a single guardrail

Use several independent controls.

```text
Prompt rules
    +
Schema validation
    +
Architecture tests
    +
OS permissions
    +
Sandbox
    +
Network restrictions
```

---

# Final Mental Model

The strongest idea from the talk can be summarized as:

```text
              LLM
               |
        Flexible Reasoning
               |
               v
      +------------------+
      | Guardrails       |
      |                  |
      | Architecture     |
      | Schema           |
      | Permissions      |
      | ACL              |
      | Sandbox          |
      | Network          |
      +------------------+
               |
               v
          Controlled
            Action
```

### In one sentence

**Use LLMs for intelligence, but use deterministic systems for enforcement.**

That principle applies to AI coding agents, RAG applications, content-generation systems, and enterprise AI platforms.
