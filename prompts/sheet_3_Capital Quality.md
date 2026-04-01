# Sheet Name: Capital Quality Scoring Engine

## Output Type: Table

---

## 1. Objective

Evaluate the **quality and maturity of capital deployment** for each company using a:

- skeptical
- evidence-first
- IC-grade scoring framework

This is a **quantitative diagnostic layer**, not narrative analysis.

---

## 2. Input

### 1. CURRENT_WEEK_RAW_TABLE
(Original funding dataset)

### 2. USE_OF_FUNDS_TABLE
(Output from Sheet 1)

---

## 3. Core Task

For EACH company:

Score **five independent dimensions (1–5)**:

1. Business Maturity  
2. Market Clarity  
3. Investor Quality  
4. Stage Fit  
5. Capital Purpose  

Then compute:

- Total Score = sum of all five
- Total Tier (based on thresholds)

Then generate:
- ONE sentence rationale:
  - One factual strength
  - One factual weakness

---

## 4. Output Format (STRICT — DO NOT CHANGE)

Return ONLY this table:

| Name | Stage | Maturity | Market | Investors | Stage Fit | Purpose | Total Score | Total Tier | Short Rationale |

No extra columns  
No missing values  
No commentary  

---

## 5. Scoring Philosophy (NON-NEGOTIABLE)

- Score based ONLY on observable evidence
- If uncertain → choose LOWER score
- Absence of evidence ≠ positive signal
- Press release claims ≠ proof unless corroborated
- Score 5 must be rare and defensible
- Score each dimension independently

---

## 6. Scoring Framework (STRICT DEFINITIONS)

### 6.1 Business Maturity

1 = Idea / pre-revenue  
2 = Early product, unstable  
3 = PMF forming  
4 = Growing revenue + structured team  
5 = Predictable revenue + scale execution  

Rules:
- <2 evidence points → cap at 3  
- Pre-revenue → cap at 2  
- Predictable revenue → minimum 4  

---

### 6.2 Market Clarity

1 = Speculative  
2 = Exists, monetization unclear  
3 = Known category  
4 = Clear buyers  
5 = Proven market  

Rules:
- Speculative → max 2  
- No monetization clarity → max 3  
- Score >3 requires paying customers  

---

### 6.3 Investor Quality

5 = Global/top-tier  
4 = Strong domestic VC  
3 = Mid-tier  
2 = Angels  
1 = Unknown  

Adjustments (max −2):
- No institutional lead  
- No follow-on capacity  
- Weak syndicate  

Rules:
- No lead disclosed → max 3  
- One strong + weak rest → max 4  

---

### 6.4 Stage Fit

Compare round size vs maturity:

1 = Mismatch  
3 = Acceptable  
5 = Perfect fit  

Rules:
- Burn unverifiable → max 3  
- Aggressive but plausible → max 4  

---

### 6.5 Capital Purpose

Based on Sheet 1:

1 = General / unclear  
2 = Survival  
3 = Mixed  
4 = Growth  
5 = Scaling  

Rules:
- “General corporate purposes” → 1  
- Runway only → max 2  
- Missing data → default 2  

---

## 7. Missing Data Rule (STRICT)

If data cannot be verified from at least 2 sources:

- Business Maturity → max 2  
- Market Clarity → max 2  

Do NOT assume facts.

---

## 8. Total Tier Mapping

- 22–25 → High-quality scale capital  
- 18–21 → Solid growth capital  
- 14–17 → Mixed-quality execution capital  
- 10–13 → Low-conviction capital  
- <10 → Weak / survival capital  

---

## 9. Rationale Rules (STRICT)

Each row must include EXACTLY ONE sentence:

Must include:
- One factual strength
- One factual weakness

Must NOT:
- Use adjectives without evidence
- Restate scores
- Be generic

Format:
"<Fact-based strength>; however, <fact-based weakness>."

---

## 10. Evidence Constraints

- No invented metrics
- No assumed traction
- No interpretation without source
- If unknown → treat as weakness

---

## 11. Output Constraints

- Output ONLY the table
- No explanation
- No reasoning
- No markdown outside table

---

## 12. Failure Handling

If insufficient data:

- Still assign scores using conservative defaults
- Apply caps strictly
- Never skip a company

---

## 13. Execution Consistency

- Evaluate each company independently
- Do not bias toward large deals
- Maintain consistent strictness across rows

---

## 14. Internal Execution Logic (DO NOT OUTPUT)

For each company:

1. Extract evidence signals
2. Score each dimension independently
3. Apply guardrails and caps
4. Compute total score
5. Assign tier
6. Generate one-line rationale