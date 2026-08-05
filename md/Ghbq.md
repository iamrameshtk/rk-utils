For long-term maintainability, 

I would make AGENTS.md intentionally short (200–300 lines) and keep Terraform-Architect-Agent.md focused on engineering reasoning (400–600 lines).

This prevents duplication and gives each file a single responsibility.

AGENTS.md (Repository Governance)

# AGENTS.md

1. Purpose
   - Repository objective
   - Scope
   - Audience

2. AI Context Loading Order
   - AGENTS.md
   - Internal Developer Platform (Backstage)
   - Terraform-Architect-Agent.md
   - SKILLS.md

3. Internal Developer Platform (Backstage)
   - When to consult Backstage
   - BigQuery Catalog
   - Technology Documentation
   - API Standards
   - Enterprise Naming Standards
   - Security Standards
   - Never guess organization-specific conventions

4. Repository Structure
   - modules/
   - examples/
   - tests/
   - docs/

5. Module Inventory
   Root Modules
     - Dataset
     - Tables

   Submodules
     - Authorized Access
     - Materialized Views
     - Jobs

6. Repository Standards
   - Folder layout
   - File naming
   - Documentation location
   - Example location
   - Test location

7. Supported Versions
   - Terraform
   - Google Provider
   - terraform-docs
   - tflint

8. Documentation Standards
   - README
   - Examples
   - terraform-docs
   - CHANGELOG

9. Validation Requirements
   - terraform fmt
   - terraform validate
   - tflint
   - terraform-docs
   - terratest

10. Pull Request Requirements
    - Documentation updated
    - Example updated
    - Tests added
    - Changelog updated

11. Versioning Strategy
    - Semantic Versioning
    - Breaking Changes
    - Deprecation Policy

12. CI/CD Expectations

13. Security Requirements

14. Repository Constraints
    - No hardcoded project IDs
    - No hardcoded regions
    - No secrets
    - No duplicate modules

15. AI Guardrails
    - Never invent repository conventions
    - Always check Backstage first
    - Never duplicate existing modules
    - Reuse repository patterns

16. File Responsibilities
    AGENTS.md
        Repository governance

    Terraform-Architect-Agent.md
        Architecture decisions

    SKILLS.md
        Implementation guidance


---

Terraform-Architect-Agent.md (Engineering Brain)

# Terraform-Architect-Agent.md

1. Mission

2. Engineering Principles

3. Terraform Design Philosophy

4. Google Cloud Architecture Principles

5. BigQuery Architecture Principles

6. Infrastructure Design Process

7. Module Boundary Decisions

8. Root Module Design

9. Submodule Design

10. Module Composition Strategy

11. Dependency Management

12. Interface Design
    - Variables
    - Outputs
    - Providers
    - Locals

13. State Management Strategy

14. IAM Design Principles

15. Authorized Access Design

16. Materialized View Design

17. Job Module Design

18. Dynamic Block Guidelines

19. for_each vs count

20. Variable Validation Strategy

21. Output Design

22. Lifecycle Management

23. Security by Design

24. Least Privilege

25. CMEK Strategy

26. Cross-Project Design

27. Performance Optimization

28. Cost Optimization

29. Scalability Strategy

30. Error Handling

31. Upgrade Strategy

32. Backward Compatibility

33. Module Evolution

34. Anti-pattern Detection

35. Code Review Checklist

36. Architecture Decision Checklist

37. Production Readiness Checklist

38. AI Decision Framework

39. Escalation Rules
    - When Backstage must be consulted
    - When repository code is authoritative
    - When not to infer behavior

40. References
    - AGENTS.md
    - SKILLS.md


---

Why this separation works

File	Owns	Never Contains

AGENTS.md	Repository governance, standards, workflow, Backstage usage	Terraform implementation details, architectural decisions
Terraform-Architect-Agent.md	Design philosophy, Terraform patterns, GCP and BigQuery architecture, engineering decision-making	Repository layout, CI/CD rules, PR process, documentation policies
SKILLS.md	Step-by-step implementation playbooks for Dataset, Tables, Authorized Access, Materialized Views, Jobs, testing, releases, etc.	Repository governance or architectural philosophy


This separation ensures:

AGENTS.md answers "How does this repository operate?"

Terraform-Architect-Agent.md answers "How should I architect Terraform for BigQuery?"

SKILLS.md answers "How do I implement this specific module correctly?"
