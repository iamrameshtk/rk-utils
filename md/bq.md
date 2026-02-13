# Limitations, Warnings, and Considerations for Using Gemini in BigQuery

This document summarizes the main limitations, warnings, and considerations for **Gemini in BigQuery**, based on Google Cloud documentation.[page:1][page:2][page:3]

---

## 1. Scope and Product Coverage

- Gemini in BigQuery is part of **Gemini for Google Cloud**, not core BigQuery, and therefore **does not share all of BigQuery’s compliance and security offerings.**[page:1][page:2]  
- Generally available Gemini in BigQuery features inherit certifications and security assurances from **Gemini for Google Cloud**, subject to explicit exceptions called out for compliance, logging, and residency.[page:1][page:2]  
- Gemini in BigQuery exposes several **“enhanced features”** that rely on access to your data and metadata, including:
  - SQL generation and completion
  - SQL explanation
  - Python code generation and completion
  - Data canvas
  - Data preparation
  - Data insights[page:2]  

**Key docs:**

- Gemini in BigQuery overview  
  - https://cloud.google.com/bigquery/docs/gemini-overview [page:2]  
- Secure and responsible use of Gemini in BigQuery  
  - https://cloud.google.com/bigquery/docs/gemini-security-privacy-compliance [page:1]  
- Gemini for Google Cloud quotas and limits  
  - https://cloud.google.com/gemini/docs/quotas [page:3]  

---

## 2. Data Use and Residency

### 2.1 Data usage

- Gemini for Google Cloud (and thus Gemini in BigQuery) **does not use your prompts or its responses to train models without your explicit permission.**[page:1][page:2]  
- Enabling Gemini in BigQuery grants the service access to **Customer Data and metadata** (schemas, tables, query/job history) required to power enhanced features.[page:1][page:2]  
- Gemini uses only data and resources that the **current authenticated user** can access, so overscoped IAM permissions increase the context Gemini can see.[page:1]  

### 2.2 Residency in storage vs in‑use processing

- Your BigQuery data **at rest** continues to follow the regional or multi‑regional location you configured (for example, `EU`, `US`).[page:2]  
- However, **Gemini LLM processing is a global service and does not obey fine‑grained, in‑use data residency controls.**[page:1]  
- The docs explicitly call out that Gemini in BigQuery:
  - **Does not provide data residency for individual locations.**
  - Limits data processing controls to **US‑ and EU‑supported jurisdictions**; data outside those jurisdictions may be processed globally.[page:1]  

**Implications:**

- If your workloads require strict in‑use data residency within a specific country or region (for example, certain financial or public‑sector workloads), Gemini in BigQuery may **not** meet those residency constraints, even though BigQuery storage does.[page:1][page:2]  

**Key docs:**

- Secure and responsible use (residency and jurisdiction section)  
  - https://cloud.google.com/bigquery/docs/gemini-security-privacy-compliance#residency [page:1]  
- Gemini in BigQuery overview (architecture and scope)  
  - https://cloud.google.com/bigquery/docs/gemini-overview [page:2]  

---

## 3. Security, Privacy, and Access Control

### 3.1 Shared responsibility

- Security is explicitly described as a **shared responsibility**: Google secures infrastructure and provides tools (IAM, encryption, VPC Service Controls), while customers must configure and operate those controls properly.[page:1]  
- Authentication is done using **Google Cloud credentials**, which can be federated to your existing identity provider; access to Gemini features is governed by IAM.[page:1]  

### 3.2 Access control and context

- Gemini in BigQuery requires access to:
  - BigQuery **metadata** (datasets, tables, schemas)
  - **Query and job history**
  - **Sampled data** or other context necessary to answer prompts[page:1][page:2]  
- The context available to Gemini is limited by the **user’s IAM permissions**. If users have overly broad dataset or project‑wide roles, Gemini’s context will also span that broader surface.[page:1]  

### 3.3 Encryption and network controls

- Data used by Gemini in BigQuery is **encrypted at rest and in transit**, consistent with standard Google Cloud security practices.[page:1]  
- **VPC Service Controls** can be used to create service perimeters around BigQuery and related resources, but Gemini’s global processing model means you must evaluate whether this is sufficient for strict regulatory requirements.[page:1]  

### 3.4 Sensitive data in prompts

- Google advises customers to be **mindful of including sensitive or personal data** in prompts when using Gemini in BigQuery, in line with their own security and privacy policies.[page:1]  

**Key docs:**

- Secure and responsible use (security, IAM, VPC‑SC, privacy)  
  - https://cloud.google.com/bigquery/docs/gemini-security-privacy-compliance [page:1]  

---

## 4. Compliance and Certification Limitations

The Gemini in BigQuery security/compliance guide explicitly lists **limitations** compared to standard Google Cloud services and BigQuery.

### 4.1 Data residency coverage

- Gemini in BigQuery:
  - **Does not provide data residency for individual locations.**
  - Allows controls only at the level of **US‑ and EU‑supported jurisdictions**.
  - States that data outside these jurisdictions “**is processed globally**.”[page:1]  

### 4.2 Logging and auditing

- **Cloud Logging audit logs are not available for Gemini in BigQuery user prompts and responses.**[page:1]  
- This means you cannot rely on GCP’s standard audit logging to reconstruct:
  - Which prompts users submitted
  - What responses Gemini produced[page:1]  

### 4.3 Assured Workloads

- Gemini in BigQuery **is not included in any supported Assured Workloads packages** listed in the secure‑use documentation.[page:1]  

### 4.4 Where to enable / disable

- Because of these limitations, Google recommends:
  - **Enabling Gemini in BigQuery only in projects that do not require compliance offerings** beyond those supported by Gemini for Google Cloud and the exceptions explicitly listed.[page:1]  
  - **Avoiding or disabling Gemini** in projects that require:
    - Detailed, prompt‑level audit logging
    - Strict, single‑location data residency
    - Inclusion in Assured Workloads scopes[page:1]  

**Key docs:**

- Secure and responsible use (limitations, compliance scope)  
  - https://cloud.google.com/bigquery/docs/gemini-security-privacy-compliance#limitations [page:1]  

---

## 5. Reliability and Output‑Quality Warnings

- Gemini is described as an **evolving AI technology** that can produce **plausible but incorrect, incomplete, or misleading results.**[page:1][page:2]  
- Google instructs customers to:
  - Treat Gemini’s outputs as **suggestions**.
  - **Review and validate** AI‑generated SQL, Python code, and analytical insights before using them in production contexts.[page:1]  

**Practical considerations:**

- Do not automatically execute Gemini‑generated SQL or Python against production datasets without human review and testing.  
- Integrate Gemini assistance with existing change‑management and code‑review processes (for example, pull requests, peer review) before deploying changes.[page:1]  

**Key docs:**

- Secure and responsible use (accuracy and validation)  
  - https://cloud.google.com/bigquery/docs/gemini-security-privacy-compliance#accuracy [page:1]  
- Gemini in BigQuery overview (feature behavior and usage notes)  
  - https://cloud.google.com/bigquery/docs/gemini-overview [page:2]  

---

## 6. Feature Scope and Data‑Access Behavior

### 6.1 Enhanced feature set

Gemini in BigQuery offers enhanced features that can access and use your data and metadata, including:[page:2]  

- SQL generation tool (including turning comments or natural language into SQL)  
- SQL code completion  
- SQL explanation and query understanding  
- Python code generation and completion  
- Data canvas (interactive workspace)  
- Data preparation (transformations, cleaning suggestions)  
- Data insights (summaries and visual insights)  

These are powered by Gemini and require access to:

- Table and column **schemas**  
- **Query history and job metadata**  
- Potentially **sampled data** from tables to improve relevance[page:1][page:2]  

### 6.2 Context based on user permissions

- Gemini only accesses data and metadata that the **current user is authorized to see**, but this still means:
  - If the user has project‑wide roles (for example, `bigquery.dataViewer` at project level), Gemini’s context can include most or all datasets in that project.[page:1]  
- You should apply **least‑privilege** principles to limit the scope of data any given user—and thus Gemini—can see.[page:1]  

**Key docs:**

- Gemini in BigQuery overview (features and context)  
  - https://cloud.google.com/bigquery/docs/gemini-overview#features [page:2]  
- Secure and responsible use (data access and context)  
  - https://cloud.google.com/bigquery/docs/gemini-security-privacy-compliance#data-access [page:1]  

---

## 7. Quotas, Limits, and Usage Throttling

Gemini in BigQuery shares quota and limit definitions with **Gemini for Google Cloud**.[page:3]

### 7.1 Per‑user quotas

For each user in a given project, per the Gemini for Google Cloud quotas documentation:[page:3]  

- **Requests per second per user (all Gemini requests):** 2.[page:3]  
- **Requests per day per user for code‑related requests** (Gemini Code Assist and Gemini in BigQuery code features such as code generation/completion):  
  - 6,000 requests per day per user.[page:3]  
- **Requests per day per user for chat, visualization, data‑insights table scans, metadata generation, data preparation, and Cloud Assist panel responses:**  
  - 960 requests per day per user.[page:3]  

**Impact:**

- Power users may encounter rate‑limit errors or throttling if they heavily use chat, visualizations, or automatic insights within a single day.[page:3]  

### 7.2 Organization‑level quotas tied to BigQuery usage

For advanced Gemini in BigQuery features (chat, visualization, data‑insights table scans, automated metadata generation) used with:

- BigQuery **on‑demand pricing**, or  
- BigQuery **Enterprise / Enterprise Plus** reservations,[page:3]  

the quotas are defined per **organization** based on prior BigQuery usage:

- The docs state that **daily quotas** are calculated from the **daily average TiB scanned (on‑demand)** or **slot‑hours consumed (reservations)** in the **previous full calendar month**.[page:3]  
- These quotas limit the number of **requests per day** for:
  - Chat
  - Visualizations
  - Data‑insights table scans
  - Metadata generation
  - Other responses shown in the Cloud Assist panel[page:3]  

Example from the quotas docs:[page:3]  

- An organization with a BigQuery Enterprise reservation of **100 slots** consumes about **2,400 slot‑hours per day**.  
- This usage yields a quota of **120 chat/visualization/data‑insights/metadata‑generation requests per day** in the following month.[page:3]  

If the org has not previously consumed BigQuery on‑demand or reservation compute:

- After first usage, the org receives a **default quota** of **250 chat/visualization/data‑insights/metadata‑generation requests per day** for the **first full calendar month**.[page:3]  
- If usage starts mid‑month, the default quota remains in effect **until the end of the following month.**[page:3]  

**Implications:**

- These quotas are **organization‑level and shared across projects**: heavy usage in one project can exhaust quotas for others.[page:3]  
- Capacity planning for Gemini‑based analytics (especially data‑insights and data canvas) must account for historical BigQuery compute usage and expected interactive load.[page:3]  

### 7.3 System limits and quota adjustments

- Some values are **system limits** and cannot be changed; others are adjustable quotas that can be increased through the **Cloud Quotas** interface.[page:3]  

**Key docs:**

- Quotas and limits | Gemini for Google Cloud  
  - https://cloud.google.com/gemini/docs/quotas [page:3]  

---

## 8. Logging, Observability, and Governance Gaps

- The documentation clearly states that **Cloud Logging audit logs are not available for Gemini in BigQuery user prompts and responses.**[page:1]  

**Governance implications:**

- You cannot rely on Cloud Logging to:
  - Reconstruct the exact **prompts** users submitted to Gemini in BigQuery  
  - Retrieve or audit the **responses** Gemini generated[page:1]  
- For regulated environments, you may need:
  - **Custom logging** (for example, application‑level logging of prompts/outputs where feasible)  
  - Internal policies requiring users to capture critical prompts/outputs in issue trackers, documentation, or notebooks[page:1]  

**Key docs:**

- Secure and responsible use (logging and audit section)  
  - https://cloud.google.com/bigquery/docs/gemini-security-privacy-compliance#logging [page:1]  

---

## 9. When to Enable, Restrict, or Disable Gemini in BigQuery

The secure‑use guide effectively outlines conditions under which Gemini in BigQuery should be used or avoided.[page:1]

### 9.1 Conditions where enabling is acceptable

According to the docs, you should enable Gemini in BigQuery in projects that:

- Do **not** require:
  - Fine‑grained **data residency** beyond US/EU jurisdiction settings  
  - Inclusion in **Assured Workloads** packages  
  - **Prompt‑level audit logging** in Cloud Logging[page:1]  
- Can tolerate the lack of Cloud Logging support for prompts and responses.  
- Have appropriate IAM and VPC‑SC configuration and where data sensitivity/risk is acceptable.[page:1]  

### 9.2 Conditions where you should not use it

You should consider **disabling or not enabling Gemini in BigQuery** in projects that:

- Require **detailed, regulator‑grade audit trails** for all user prompts and AI responses.  
- Require strict, single‑country or fine‑grained **data residency in use** beyond US/EU jurisdiction controls.  
- Require **Assured Workloads** coverage that explicitly includes all used services, including AI features.[page:1]  

**Key docs:**

- Secure and responsible use (recommendations for where to use Gemini)  
  - https://cloud.google.com/bigquery/docs/gemini-security-privacy-compliance#recommended-usage [page:1]  

---

## 10. Operational Best Practices and Warnings

Although not hard technical limits, Google’s best‑practice guidance functions as important warnings.[page:1]

### 10.1 Treat output as assistance

- Treat Gemini’s output as **suggestions**, not authoritative answers.[page:1]  
- Always **review and validate**:
  - Generated SQL queries
  - Generated Python code
  - Data insights and explanations[page:1]  

### 10.2 Sensitive and regulated data

- Avoid placing **secrets, credentials, or highly sensitive PII** into free‑form prompts unless strictly necessary and consistent with your organization’s policies.[page:1]  

### 10.3 Least‑privilege permissions

- Apply the **principle of least privilege** for all BigQuery datasets and projects where Gemini is enabled:
  - Restrict users to only the datasets they need.
  - Avoid broad project‑level roles when they are not strictly required.[page:1]  

**Key docs:**

- Secure and responsible use (best practices)  
  - https://cloud.google.com/bigquery/docs/gemini-security-privacy-compliance#best-practices [page:1]  

---

## 11. Summary Checklist

Use this checklist as a quick reference before enabling Gemini in BigQuery in any project:

- **Data residency**
  - [ ] Storage location requirements met by BigQuery regions.[page:2]  
  - [ ] In‑use residency limitations (global/US/EU only) accepted.[page:1]  

- **Compliance**
  - [ ] Project does **not** require Assured Workloads coverage for Gemini.[page:1]  
  - [ ] Lack of prompt/response audit logs in Cloud Logging is acceptable.[page:1]  

- **Security and privacy**
  - [ ] IAM configured with least‑privilege roles.[page:1]  
  - [ ] VPC‑SC perimeters configured where required.[page:1]  
  - [ ] Internal policies permit AI processing of the relevant data categories.[page:1]  

- **Governance**
  - [ ] Organization has alternative processes to track critical prompts/outputs, if needed.[page:1]  

- **Quotas and performance**
  - [ ] Per‑user quotas (2 RPS, 6,000 code requests/day, 960 chat/visual/insights requests/day) are sufficient.[page:3]  
  - [ ] Org‑level quotas based on prior TiB scanned / slot‑hours are understood and monitored.[page:3]  

- **Operational use**
  - [ ] Teams understand that outputs may be incorrect and must be reviewed.[page:1][page:2]  

---

## Primary Google Cloud Documentation Links

- Gemini in BigQuery overview  
  - https://cloud.google.com/bigquery/docs/gemini-overview [page:2]  

- Secure and responsible use of Gemini in BigQuery  
  - https://cloud.google.com/bigquery/docs/gemini-security-privacy-compliance [page:1]  

- Quotas and limits | Gemini for Google Cloud  
  - https://cloud.google.com/gemini/docs/quotas [page:3]  
