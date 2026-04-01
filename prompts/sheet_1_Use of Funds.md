# Sheet Name: Use of Funds & Strategic Intent

## Output Type: Table

---

## 1. Objective

Build a **forensic, citation-backed dataset** capturing:

- Company description (1-line)
- Reported use of funds (with evidence)
- Strategic classification of fund deployment

This is a **high-integrity analytical output**, not summarization.

---

## 2. Input

You will receive:

### CURRENT_WEEK_RAW_TABLE

A structured table containing:
- Company Name
- Deal Size
- Stage
- Industry
- Any other available metadata

This is the **only base dataset**. All augmentation must come from external credible sources.

---

## 3. Core Task

For EACH company:

1. Identify what the company does (1-line description)
2. Determine WHY the funds were raised using public sources
3. Extract and cite evidence
4. Classify use-of-funds into a strategic category
5. Populate all required columns

---

## 4. Output Format (STRICT — DO NOT DEVIATE)

Return ONLY a table with EXACTLY these columns:

| Company Name | What the company does (1 line) | Reported use of funds (with citation) | Use-of-funds classification | Deal Size ($ Mn) | Stage of Funding | Industry | Source Tier Used |

- No extra columns
- No missing columns
- No commentary outside the table

---

## 5. Use-of-Funds Classification Taxonomy

You MUST assign exactly ONE classification per company:

- Strategic Scaling
- Strategic Scaling / Expansion
- Execution / Expansion
- Execution / Product-market scale
- Execution (R&D / product development)
- Execution (product & distribution)
- Execution (product & distribution / global expansion)
- Execution (platform & hiring / expansion)
- Execution (infrastructure)
- Execution (network build)
- Execution (product & manufacturing)
- Execution (R&D / clinical)
- Option-Value / Exploratory (small round)
- Neutral / Insufficient public cheque detail
- Neutral / Insufficient public cheque detail (likely: Execution / Expansion)
- Neutral / Insufficient public cheque detail (likely: Execution / Product)

### If none apply:
- Create a NEW category
- Must be precise
- Must be justified inside the “Reported use of funds” field

---

## 6. Data Sourcing Rules (STRICT PRIORITY)

### Tier 1 (Highest Priority)
- Official company website
- Press releases
- Investor materials
- Regulatory filings
- Tracxn / Crunchbase / PitchBook (public pages)

### Tier 2
- Reuters, Bloomberg
- Economic Times, Business Standard
- Moneycontrol, Financial Express
- TechCrunch, Inc42, Entrackr

### Tier 3 (Last resort only)
- Blogs or smaller sites
- MUST be corroborated by **at least TWO independent sources**
- MUST be labeled as Tier 3

---

## 7. Conflict Resolution

- Prefer Tier 1 > Tier 2 > Tier 3
- If same-tier conflict:
  - Use most recent
  - Mention conflict explicitly in output
  - Cite both sources

---

## 8. Evidence Rules (NON-NEGOTIABLE)

For “Reported use of funds”:

- MUST be factual
- MUST include citation(s) in brackets
- MUST NOT contain unsupported claims

If no credible source exists:
- Write exactly:
  "No specific use-of-funds disclosed publicly"
- Classification MUST be:
  "Neutral / Insufficient public cheque detail"

---

## 9. Inference Rules

- No silent inference allowed
- Only allowed if:
  - Source strongly implies usage
  - Clearly labeled as:
    "likely" or "presumed"

---

## 10. Research Instructions

For EACH company:

Search queries:
- "<Company Name> funding use of funds"
- "<Company Name> raised why"
- "<Company Name> press release funding"

Check:
- Official website / newsroom
- Tier 1 → Tier 2 → Tier 3 sources

Extract:
- Business description
- Use of funds

---

## 11. Data Normalization

- Convert:
  - K → Mn
  - Bn → Mn
- Preserve:
  - Exact disclosed deal size
- Do NOT estimate or fabricate values

---

## 12. Quality Standards

The output must be:

- Evidence-backed
- Investor-grade (IC-ready)
- Fully traceable
- Zero hallucination

If data is missing:
- Explicitly state it
- Do NOT guess

---

## 13. Output Constraints

- Output ONLY the table
- No explanations
- No summaries
- No extra text

---

## 14. Failure Handling

If any row cannot be completed:
- Still include the company
- Fill missing fields with:
  - "Not disclosed" OR
  - Required fallback phrases per rules

Never drop a company.

---

## 15. Scope

Process:
- ALL companies in CURRENT_WEEK_RAW_TABLE

---

## 16. Internal Execution Note (IMPORTANT)

- Treat each company independently
- Do not let one company’s classification influence another
- Maintain consistency across rows