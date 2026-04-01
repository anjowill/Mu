# Sheet Name: Founder-Lens Capital Analysis

## Output Type: Table

---

## 1. Objective

Determine **why specific companies received funding this week**, using only:

- Strategy evidence
- Capital structure evidence
- Execution evidence

This is a **forensic selection analysis**, not summarization or storytelling.

---

## 2. Input

You will receive:

### 1. WEEKLY_FUNDING_TABLE
(Structured output from Sheet 1)

Includes:
- Company Name
- Use-of-funds classification
- Deal Size
- Stage
- Industry
- Source-backed descriptions

### 2. Public Data Sources
Must follow strict source hierarchy (defined below)

---

## 3. Core Task

For EACH company:

You must determine:

> Why did this company get funded vs. other startups in the same category?

Using ONLY:
- verifiable evidence
- cited sources

---

## 4. Output Format (STRICT — DO NOT CHANGE)

Return ONLY this table:

| Company | Strategy Signal (Evidence + Citation) | Capital Signal (Evidence + Citation) | Execution Signal (Evidence + Citation) | Founder Learning Insight |

No extra columns  
No missing fields  
No commentary outside table  

---

## 5. Signal Definitions (STRICT)

### 5.1 Strategy Signal

What strategic positioning differentiated the company?

Allowed evidence:
- Public statements
- TAM positioning
- Category focus
- Geography strategy
- Regulatory alignment
- Niche positioning

Must:
- Contain explicit fact
- Include citation in parentheses
- Be evidence-backed

Forbidden:
- Opinion
- Generic claims

---

### 5.2 Capital Signal

Why did investors underwrite this company?

Use:
- Lead investor quality
- Strategic investors
- Prior funding history
- Round structure
- Institutional vs angel mix
- Investor quotes

Must:
- Include citation
- Reference funding source

If inference is required:
- Explicitly label:
  "Labeled Inference based on <source>"

---

### 5.3 Execution Signal

What operational proof exists?

Use:
- Revenue
- AUM
- Customers
- Deployments
- Patents
- Partnerships
- Product milestones
- Regulatory approvals

If NO data exists:
Write EXACTLY:
"No independently verifiable execution metrics disclosed in public reporting."

---

### 5.4 Founder Learning Insight

Derive a **tactical, replicable insight**:

Must:
- Be grounded in signals above
- Be specific (not generic advice)
- Be applicable to founders

Format:
"Founders in <category> should <specific action>; evidence shows <reason>."

---

## 6. Analytical Depth Requirement

For EACH company:

- Compare implicitly vs a typical startup in same vertical
- Identify:
  - selection signals
  - institutional filters passed

Do NOT:
- Use hype language
- Use startup clichés
- Make unsupported claims

---

## 7. Source Hierarchy (STRICT)

### Tier 1
- Company website
- Press releases
- Investor announcements
- Regulatory filings
- MCA filings

### Tier 2
- Reuters
- Economic Times
- Business Standard
- Moneycontrol
- TechCrunch
- Inc42
- Entrackr

### Tier 3
- Only if corroborated by TWO independent sources
- Must be labeled Tier 3

Never use:
- Social media
- Anonymous blogs

---

## 8. Evidence Rules (NON-NEGOTIABLE)

- EVERY signal must include citation
- No hallucinated metrics
- No invented numbers
- No assumed traction
- No interpretation without source

If data missing:
- State explicitly
- Do not infer

---

## 9. Output Constraints

- Output ONLY the table
- No reasoning
- No explanation
- No markdown outside table

---

## 10. Failure Handling

If insufficient data:

- Strategy Signal → still attempt using positioning evidence
- Capital Signal → may include "Labeled Inference"
- Execution Signal → use fallback statement

Never skip a company.

---

## 11. Execution Consistency Rules

- Treat each company independently
- Maintain consistent depth across all rows
- Do not bias toward larger deals

---

## 12. Internal Execution Logic (DO NOT OUTPUT)

For each company:

1. Identify funding announcement
2. Extract investor profile
3. Extract use-of-funds context
4. Extract execution metrics (if any)
5. Identify differentiation vs peers
6. Construct 3 signals
7. Derive founder insight