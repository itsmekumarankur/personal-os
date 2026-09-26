# AI Agents Need Guardrails, Not Just Guidelines

**Source:** https://wellington.aitinkerers.org/talks/rsvp_spGYYjCvPOs

> Notes based on the talk transcript provided with the request. The transcript covers multiple talks/demos, with the main themes being architecture-as-code for AI agents, local AI tooling, and sandboxing coding agents.

---

# Part 1 — From Architecture Guidelines to Enforced Guardrails

## 1. The Problem: Agents Forget Rules

The speaker starts with a familiar problem.

Developers are increasingly writing Markdown files such as:

```text
CLAUDE.md
AGENTS.md
Architecture.md
README.md
```

These files contain instructions such as:

- How the project should be structured
- Which dependencies are allowed
- Which architectural patterns should be followed
- Which coding practices should be used
- Which things the agent should avoid

But there is a fundamental problem:

> **An instruction written in Markdown is only a guideline unless something enforces it.**

An AI agent can read the rules and still violate them.

This is similar to what happened in traditional software teams.

The speaker previously worked on a large Android team with around 70 engineers working on one project. They had extensive documentation describing architectural rules.

Developers would still occasionally:

```text
Forget a rule
   ↓
Implement something differently
   ↓
Create a pull request
   ↓
Ask for an exception
```

The same problem now exists with AI agents.

---

# 2. Architecture Testing

The speaker previously addressed this problem using **architecture testing**.

Architecture testing is related to linting, but the focus is different.

### Linting

Linting generally checks detailed coding rules:

```text
Formatting
Naming
Syntax
Code style
```

For example:

```text
"This array should be formatted across multiple lines."
```

### Architecture Testing

Architecture testing checks the **structure and relationships of the application**.

For example:

```text
Repository
   ↓
Domain

Domain
   ↓
Use Case

Use Case
   ↓
Repository
```

You can define rules such as:

```text
Repository must NOT depend on Domain implementation.
```

or:

```text
Feature A cannot depend directly on Feature B.
```

or:

```text
A use case cannot access the data layer directly.
```

These rules describe the architecture rather than formatting.

---

# 3. Turning Architecture Rules into Tests

The speaker used **Konsist for Kotlin** to make architecture rules executable.

For example, instead of writing:

> "Repositories should not inject domain implementation."

as a Markdown rule only, he creates an actual architecture test.

Conceptually:

```text
Architecture Rule
       ↓
Executable Test
       ↓
PASS / FAIL
```

Now the rule is no longer just documentation.

It becomes a machine-checkable constraint.

---

# 4. The Problem with Two Sources of Truth

Initially, the speaker had:

```text
Architecture.md
      +
Architecture Tests
```

The problem is that these can drift apart.

For example:

```text
Markdown says Rule A exists
          ↓
Test doesn't implement Rule A
```

Or:

```text
Test enforces Rule B
          ↓
Documentation doesn't explain Rule B
```

Eventually:

```text
Documentation ≠ Actual Architecture
```

This is a classic **source-of-truth problem**.

---

# 5. Add Rule IDs

The speaker's next step was to give architecture rules explicit IDs.

For example:

```text
ARCH-001
ARCH-002
ARCH-003
```

Then the executable tests can refer back to those IDs.

Conceptually:

```text
ARCH-001
   ↓
Architecture Test
   ↓
Documentation section
```

When a test fails, an agent can see:

```text
ARCH-001 failed
```

and then look up:

```text
ARCH-001
   ↓
Relevant documentation
   ↓
Reason / explanation
   ↓
Expected architecture
```

This makes the failure much easier for an AI agent to understand.

---

# 6. The Better Solution: Define the Rule in Code

The speaker eventually moved another step forward.

Instead of:

```text
Markdown
   +
Separate architecture test
```

he defines the architectural construct and its rules together in code.

Conceptually:

```text
Construct
 ├── Description
 ├── Rationale
 ├── Rule 1
 ├── Rule 2
 └── Rule 3
```

The code becomes the source of truth.

From that source, Markdown documentation is generated.

So:

```text
Architecture definitions
          ↓
      Generator
          ↓
Markdown documentation
```

This eliminates much of the synchronization problem.

---

# 7. Documentation Becomes Generated Output

The generated Markdown can contain:

- Rule descriptions
- Rule IDs
- Rationale
- Architecture constructs
- Enforcement status
- Examples
- Guidance

For example:

```text
ARCH-001
Repository Dependency Rule

Rule:
Repositories must not inject domain implementations.

Status:
ENFORCED

Rationale:
Keeps the domain layer independent.
```

The important point is:

> **Humans and agents can read the Markdown, while machines can execute the actual rules.**

---

# 8. Global Rule Index

The speaker also generates a **global rule index**.

Conceptually:

```text
Architecture Rule Index

ARCH-001 → Repository dependency
ARCH-002 → Domain boundary
ARCH-003 → Use-case dependency
ARCH-004 → Feature structure
...
```

This is useful for AI agents.

When an architecture test fails, the agent doesn't have to read an enormous documentation file.

It can:

```text
Test failure
     ↓
Rule ID
     ↓
Rule index
     ↓
Specific documentation
```

This is an example of **progressive disclosure**.

---

# 9. Progressive Disclosure

Instead of giving the AI agent 800–1,000 lines of architecture documentation immediately:

```text
Agent starts
   ↓
Short architecture README
   ↓
Rule index
   ↓
Only relevant rule
   ↓
Detailed explanation
```

This reduces unnecessary context consumption.

The agent doesn't need to know every architectural rule to work on one small feature.

It only needs the relevant rules.

This is particularly useful because LLM context is valuable and should not be filled with irrelevant information.

---

# 10. Documentation and Tests Serve Different Purposes

Someone asked:

> "If the tests are executable, why keep the Markdown?"

The answer is important.

The tests tell the **machine** whether something is correct.

The Markdown tells the **human or AI agent** what the rule means.

For example:

```text
Test:
FAIL

Agent:
Why?

Documentation:
ARCH-007 says repositories cannot depend on the UI layer.
The reason is to preserve separation of concerns.
```

So:

```text
Tests → Enforcement
Markdown → Understanding
```

You need both.

---

# 11. What About Fuzzy Engineering Guidance?

Not everything should become a strict automated rule.

For example:

> "Prefer the Builder pattern."

This is difficult to turn into a universal machine-checkable rule.

Why?

Because the correct question is:

> "When should the Builder pattern be used?"

The answer depends on context.

Therefore the speaker distinguishes between:

### Strict rules

These can be machine-tested.

```text
Repository cannot depend on UI.
```

### Guidance

These are recommendations.

```text
Prefer Builder when object construction becomes complex.
```

This distinction is important.

Not every engineering principle should be forced into a binary test.

---

# 12. More Complex Architecture Rules

The speaker's architecture tests can express more than simple naming conventions.

For example:

```text
Domain Interface
      ↑
      │
Use Case
```

A use case can implement a domain interface.

But:

```text
Use Case
   X
Data Layer
```

The use case should not directly access the data layer.

Repositories can sit at the boundary and implement domain interfaces in controlled ways.

These are **relationships between architectural constructs**.

This makes architecture testing significantly more powerful than ordinary linting.

---

# 13. Does This Actually Help?

The speaker analyzed his own agent activity across several projects.

He found that architecture tests:

- Ran many times.
- Failed many times.
- Not every failure represented a real violation because some were part of test-driven development or rule changes.
- But around **39 failures were genuine cases** where an agent had implemented something that violated an architecture rule and discovered the problem only when the architecture tests ran.

That works out to roughly:

> **About two genuine architecture violations per day** in the observed period.

This is the important evidence from the talk.

The architecture tests were not just documentation.

They actually caught cases where the agent had done something wrong.

---

# 14. The Most Important Principle

The speaker summarizes the idea roughly as:

> **A guideline that is not enforced is essentially not useful.**

For AI agents, this becomes even more important.

Humans can be trained.

Agents don't reliably remember every instruction across long-running workflows.

So:

```text
Guideline
   ↓
Agent may remember
   ↓
Agent may forget
```

versus:

```text
Rule
   ↓
Executable test
   ↓
PASS / FAIL
```

The second provides a real guardrail.

---

# 15. Main Lesson from Part 1

The architecture approach can be summarized as:

```text
Traditional:

Markdown
   ↓
Human reads it
   ↓
Hopefully follows it


AI-friendly:

Architecture definition
       ↓
Executable tests
       +
Generated documentation
       ↓
Agent understands the rule
       +
Runtime/test system enforces it
```

The result is:

> **Guardrails for agents instead of relying entirely on instructions.**

---

# Part 2 — Generating Slide Decks with AI and Structured Schemas

Another talk/demo in the transcript explores building presentation decks using AI.

The speaker wanted to automate the creation of slides from structured data instead of manually designing every slide.

---

## 16. The Basic Problem

Creating presentation decks manually is repetitive.

You have to deal with:

- Slide layouts
- Text
- Images
- Diagrams
- Themes
- Charts
- Speaker content
- Formatting

The speaker wanted to turn this into a more programmatic workflow.

The idea is:

```text
Human idea
   ↓
AI
   ↓
Structured slide definition
   ↓
Renderer
   ↓
Presentation
```

---

# 17. Schema-Driven Slide Generation

The system defines a schema describing what a presentation can contain.

Conceptually:

```text
Deck
 ├── Theme
 ├── Slides
 │    ├── Title
 │    ├── Text
 │    ├── Image
 │    ├── Diagram
 │    ├── Grid
 │    └── Chart
```

The AI receives the schema as part of its instructions.

It then generates content that conforms to the schema.

This is important because instead of asking:

> "Make me a nice presentation."

you give the model a structured target.

---

# 18. The Compiler Idea

The speaker describes a compiler-like workflow.

Conceptually:

```text
Schema
   ↓
Prompt / LLM
   ↓
Structured output
   ↓
Validator
   ↓
Renderer
   ↓
Slide deck
```

If the generated result doesn't match the schema:

```text
Generated output
       ↓
Validator
       ↓
ERROR
```

The error can then be fed back to the AI:

```text
Validation error
       ↓
LLM
       ↓
Corrected output
       ↓
Validator
```

This is another example of the same broader idea:

> **Let the LLM generate, but let deterministic systems validate.**

---

# 19. Plain Text as the Interface

One of the speaker's interesting design decisions is that the human doesn't necessarily need to write YAML or JSON manually.

Instead:

```text
Human:
"I don't like this slide.
Move the diagram to the right
and make the explanation shorter."
```

The system converts that natural-language feedback into structured changes.

So:

```text
Human language
      ↓
LLM
      ↓
Structured representation
      ↓
Renderer
```

This makes the interface easier for humans while keeping the underlying system structured.

---

# 20. Why Schemas Help LLMs

LLMs can generate almost anything.

That's also a problem.

Without constraints:

```text
Prompt
 ↓
LLM
 ↓
Something vaguely useful
```

With a schema:

```text
Prompt
 +
Schema
 ↓
LLM
 ↓
Structured output
 ↓
Validation
```

The schema limits what the model can produce.

This is similar to using:

- JSON Schema
- Typed APIs
- Function calling
- Structured outputs
- Compilers
- Type systems

The LLM provides flexibility, while the schema provides boundaries.

---

# Part 3 — Local AI Attendance System

The transcript also contains a separate demonstration of a local AI-based attendance system.

The project was designed for a school check-in process.

---

## 21. The Problem

The existing process was manual.

Every day, someone had to:

```text
Find attendance sheet
 ↓
Find student's name
 ↓
Write visitor name
 ↓
Write time
```

The presenter wanted to automate this.

---

# 22. The Local AI Approach

The system was designed to run **locally**.

The stated goal was:

```text
No cloud dependency
No external API requirement
No monthly AI API costs
Sensitive data stays local
```

The architecture included technologies such as:

- Flask
- OpenCV
- DeepFace
- Whisper
- Local models
- SQLite
- Local retrieval / RAG

---

# 23. Face Recognition

The system uses facial recognition to identify the person.

Conceptually:

```text
Camera
   ↓
Face detection
   ↓
Face recognition
   ↓
Person identified
   ↓
Attendance record
```

The presenter demonstrated the system recognizing him.

The system could then associate the person with local data.

---

# 24. Check-In / Check-Out

The application supports attendance actions such as:

```text
Check in
Check out
```

The system stores the events in SQLite.

Conceptually:

```text
Person
 ↓
Recognition
 ↓
Check-in event
 ↓
SQLite
```

---

# 25. AI Assistant

The application also contains an AI assistant.

Staff can ask questions such as:

> "Who is currently checked in today?"

The system queries the local attendance database.

Conceptually:

```text
Question
 ↓
AI assistant
 ↓
SQLite
 ↓
Attendance data
 ↓
Answer
```

This is a good example of combining an LLM with deterministic data access.

The database remains the source of truth.

The AI provides the conversational interface.

---

# 26. RAG for Policy Questions

The system also loads policy documents.

For example:

```text
Policy PDF
    ↓
Local retrieval
    ↓
Relevant policy information
    ↓
AI answer
```

A user can ask something like:

> "Can I bring this type of food?"

The assistant searches the loaded policy and answers based on the document.

This is a straightforward **RAG** pattern.

---

# 27. Anti-Spoofing

The system also demonstrated anti-spoofing functionality.

The goal is to prevent someone from simply presenting a photograph to the camera and pretending to be another person.

Conceptually:

```text
Face detected
    ↓
Is it a real person?
    ↓
Yes → Continue
No  → Spoof detected
```

The presenter emphasized the importance of local processing because the system deals with sensitive personal information.

---

# Part 4 — AI Agent Security and Sandboxing

The final major section of the transcript returns to AI agent security.

The speaker demonstrates why local coding agents can be dangerous.

---

# 28. AI Coding Agents Have Broad Access

A coding agent running on your computer may have access to:

```text
Source code
SSH keys
AWS credentials
Environment variables
Home directory
Git repositories
Cloud accounts
Internet
```

That creates a large attack surface.

The problem becomes especially serious when an agent can execute commands.

---

# 29. The Dangerous Example

The speaker describes seeing a coding agent access an AWS credentials file from his home directory.

He believed:

> "The agent is only working inside my project directory."

But the agent was able to access:

```text
~/.aws/credentials
```

This was particularly serious because the machine had access to production systems.

The lesson:

> **Never assume that an agent will only access the directory you think it should access.**

Verify the permissions.

---

# 30. Prompt Injection and Malicious Instructions

An AI agent may read content that contains malicious instructions.

For example:

```text
Repository file
     ↓
Malicious instruction
     ↓
Agent reads it
     ↓
Agent follows instruction
     ↓
Sensitive file accessed
```

This is prompt injection.

The danger increases when the agent has unrestricted access to the host machine.

---

# 31. Why Sandboxing Matters

One option is a virtual machine:

```text
Host
  ↓
VM
  ↓
Agent
```

The VM can be isolated from the host filesystem.

Another option is a container:

```text
Host
  ↓
Container
  ↓
Agent
```

But the speaker points out that container security needs to be considered carefully.

For example, Docker's default configuration and privileges can create risks.

The important point is:

> **A sandbox only works if the sandbox itself is configured correctly.**

---

# 32. The Speaker's Simpler Approach: Separate User Accounts

Instead of always using a VM, the speaker uses a much older technology:

> **Operating-system user accounts.**

The idea is simple.

Don't run your AI coding agent as your normal user.

Instead:

```text
Normal user
    ↓
Full personal access

Agent user
    ↓
Restricted access
```

For example:

```text
agents-personal
agents-demo
agents-operational
```

Each account can have different permissions.

---

# 33. Restrict Which Directories the Agent Can Access

Suppose the agent only needs:

```text
~/projects/tinkerers-demo
```

Then give the agent access only to that directory.

Conceptually:

```text
Normal user
│
├── AWS credentials       ❌
├── SSH keys              ❌
├── Personal documents    ❌
├── Other projects        ❌
│
└── Tinkerers project     ✅
```

This follows the **principle of least privilege**.

---

# 34. macOS ACLs

The speaker uses **Access Control Lists (ACLs)** to control which users can access particular directories.

Conceptually:

```text
Directory
   │
   ├── User A → READ/WRITE
   ├── User B → READ
   └── Agent  → NO ACCESS
```

Then permissions can be changed as needed.

For example:

```text
Grant agent-demo access
       ↓
Agent can work on project
```

Later:

```text
Remove access
       ↓
Agent can no longer access project
```

---

# 35. Why Two Layers of Protection Are Useful

The speaker also has a wrapper script that checks which agent profile is being used.

So there are effectively two controls:

```text
Layer 1:
Wrapper checks allowed configuration

Layer 2:
OS permissions prevent unauthorized filesystem access
```

Even if the wrapper has a bug:

```text
Wrapper fails
      ↓
OS permissions still block access
```

This is classic **defense in depth**.

---

# 36. The Core Principle: Don't Trust the Agent

The final security lesson is similar to the first talk in this conversation.

Treat the AI agent as a potentially **untrusted process**.

Don't rely only on:

```text
Prompt instructions
CLAUDE.md
AGENTS.md
System prompts
Tool restrictions
```

Instead, enforce boundaries outside the model.

For example:

```text
Agent
 ↓
OS permissions
 ↓
Sandbox
 ↓
Network controls
 ↓
Limited filesystem
```

If the agent behaves incorrectly, the environment limits what it can damage.

---

# 37. Connecting All Three Talks

Although the transcript contains multiple presentations, there is a common theme running through them.

## Talk 1: Architecture Testing

```text
Guideline
   ↓
Executable rule
   ↓
PASS / FAIL
```

## Talk 2: Schema-Driven AI

```text
LLM
 ↓
Structured schema
 ↓
Validator
 ↓
Correct output
```

## Talk 3: Agent Sandboxing

```text
AI agent
 ↓
Restricted environment
 ↓
Limited permissions
```

All three follow the same philosophy:

> **Don't rely on the LLM alone. Surround it with deterministic controls.**

---

# 38. The Bigger Architecture

A mature AI engineering system could look like:

```text
                  ┌─────────────────┐
                  │      LLM        │
                  │                 │
                  │ Reasoning       │
                  │ Planning        │
                  │ Generation      │
                  └────────┬────────┘
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
     Architecture       Schema          Sandbox
       Tests          Validation       Permissions
          │                │                │
          ↓                ↓                ↓
       PASS/FAIL       Valid output      Limited access
          │                │                │
          └────────────────┼────────────────┘
                           ↓
                    Deterministic System
```

The LLM remains powerful and flexible.

But it operates inside **boundaries that do not depend on the LLM behaving perfectly**.

---

# 39. Key Lessons

### 1. Guidelines are not enough

A Markdown instruction can help an agent understand what you want.

But it does not guarantee compliance.

```text
Guideline
   ≠
Enforcement
```

Where possible:

```text
Guideline
   ↓
Executable test
```

---

### 2. Make architecture executable

Architecture should not exist only in diagrams and documents.

Important architectural constraints can become automated tests.

```text
Architecture
   ↓
Code
   ↓
Test
   ↓
PASS / FAIL
```

---

### 3. Generate documentation from the source of truth

Instead of maintaining:

```text
Documentation
+
Tests
```

as two independent artifacts:

```text
Architecture definition
       ↓
 ┌─────┴─────┐
 ↓           ↓
Tests      Markdown
```

This reduces drift.

---

### 4. Use progressive disclosure

Don't dump hundreds of pages of architecture rules into the agent context.

Instead:

```text
Short index
   ↓
Rule ID
   ↓
Relevant documentation
```

This keeps context smaller and more useful.

---

### 5. Use deterministic validation

Let the LLM generate.

Let software verify.

Examples:

```text
LLM → Generate code
Test → Verify code

LLM → Generate JSON
Schema → Validate JSON

LLM → Decide what to do
OS → Enforce permissions
```

---

### 6. Sandbox coding agents

Assume the agent may:

- Read the wrong file
- Execute the wrong command
- Follow prompt injection
- Access credentials
- Delete files
- Modify unintended projects

Therefore:

```text
Least privilege
+
Filesystem isolation
+
Sandboxing
+
OS permissions
```

are important defenses.

---

# Final Takeaway

The most important message from the transcript is:

> **AI agents should not be trusted simply because we gave them good instructions.**

Instead, build systems where:

```text
Instructions
      +
Executable rules
      +
Schema validation
      +
OS permissions
      +
Sandboxing
      +
Deterministic tests
```

work together.

The mental model should be:

```text
                 AI Agent
                    │
             ┌──────┴──────┐
             ↓             ↓
        Intelligence    Guardrails
             │             │
          LLM/AI      Tests / Schema
                       Permissions
                       Sandbox
                       Policies
             │             │
             └──────┬──────┘
                    ↓
              Reliable System
```

**The LLM provides the intelligence. The surrounding engineering system provides the reliability and safety.**

That is the recurring architectural lesson across the talks.
