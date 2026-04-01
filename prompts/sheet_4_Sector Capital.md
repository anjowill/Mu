# Sheet Name: Sector Capital Priority Map

## Output Type: Multi-Table

---

## 1. Objective

Transform company-level funding data into a **sector-level capital allocation map** using:

- structured aggregation
- rule-based classification
- disciplined synthesis

This is NOT narrative.
This is NOT opinion.

---

## 2. Input

### 1. CURRENT_WEEK_RAW_TABLE
- Company-level funding data

### 2. USE_OF_FUNDS_TABLE
- Output from Sheet 1

---

## 3. Core Task

Generate EXACTLY THREE tables:

1. Capital & Deal Count by Sector  
2. Sector Priority Ranking (by capital deployed)  
3. Sector Scorecard  

---

## 4. Normalization Rules (STRICT)

### 4.1 Sector Normalization

Map sectors as follows:

- Ecommerce, D2C → Ecommerce / D2C  
- Enterprise Tech, SaaS → Enterprise Tech / SaaS  
- Cleantech, EV, Climate → Cleantech / EV  
- Advanced Tech, Semiconductors, Spacetech → Advanced Hardware / Spacetech  
- AI remains:
  - "AI (Application Layer)" unless clearly infrastructure

No duplicate sector labels allowed.

---

### 4.2 Capital Rules

- Use ONLY disclosed deal sizes
- Convert all values to $ Mn
- Ignore undisclosed amounts for capital sums

---

### 4.3 Deal Count Rules

- Count ALL deals (including undisclosed sizes)

---

## 5. Table 1 — Capital & Deal Count by Sector

### Structure

Table 1. Capital & Deal Count by Sector

| Sector | Deals | % by deal count | Capital ($ Mn) | % of Capital |

### Computation Rules

- Deals = count of companies per sector  
- % by deal count = (sector deals / total deals) × 100  
- Capital = sum of disclosed capital  
- % of Capital = (sector capital / total capital) × 100  

### Formatting Rules

- Percentages rounded to 2 decimals  
- Include TOTAL row:
  - total deals
  - total capital
  - 100% values  

---

## 6. Priority Tier Rules (NON-NEGOTIABLE)

Based on % of TOTAL CAPITAL:

- Tier 1 → >10%  
- Tier 2 → 6–10%  
- Tier 3 → 3–6%  
- Tier 4 → <3%  

---

## 7. Table 2 — Sector Priority Ranking

### Structure

Table 2. Sector Priority Ranking (By Capital Deployed)

| Rank | Sector | Capital ($ Mn) | % of Total | Deals | Priority Tier | Interpretation |

### Rules

- Sort by Capital descending  
- Rank sequentially (1,2,3...)  
- Priority Tier strictly from rules above  

### Interpretation Rules

- 3–6 words only  
- Must reflect capital behavior  
- Examples:
  - "Core consumer scale category"
  - "Infrastructure platform build-out"
  - "High-conviction deeptech"
  - "Disciplined SaaS scaling"
  - "Cautious experimentation"

### Totals Row

Include:
- Total capital
- Total deals

---

## 8. Table 3 — Sector Scorecard

### Structure

Table 3. Sector Scorecard

| Sector | Stage Profile | Capital Quality | Capital Intent | Overall Character |

---

### 8.1 Stage Profile

- Derived from stage distribution in raw table  
- Format:
  - "Seed → Series B"
  - "Series A only"
  - "Pre-seed → Growth"

---

### 8.2 Capital Quality

Allowed values ONLY:

- High  
- Medium–High  
- Medium  
- Low–Medium  
- Low  

Derived from:
- Investor quality (Sheet 3 logic)
- Stage maturity
- Capital concentration
- Priority Tier

---

### 8.3 Capital Intent

Derived from USE_OF_FUNDS_TABLE:

Examples:
- Strategic scaling  
- Execution + scaling  
- Execution / expansion  
- R&D + scaling  
- Exploratory  

Must reflect dominant pattern in sector.

---

### 8.4 Overall Character

- 3–6 words  
- Structural (not narrative)

Examples:
- "Infrastructure-like conviction capital"
- "Selective consumer scaling"
- "Applied AI execution layer"
- "High-conviction deeptech"
- "Cautious experimentation zone"

---

## 9. Governance Rules

- Do NOT invent data  
- Do NOT infer beyond inputs  
- Do NOT narrate  
- All outputs must be traceable to input  

---

## 10. Output Constraints

- Output ONLY tables  
- No explanation  
- No commentary  
- No markdown outside tables  

---

## 11. Output Order (STRICT)

1. Table 1  
2. Table 2  
3. Table 3  

---

## 12. Failure Handling

If sector data is sparse:

- Still include sector  
- Use conservative classification  
- Do not omit  

---

## 13. Internal Execution Logic (DO NOT OUTPUT)

1. Normalize sectors  
2. Aggregate deals + capital  
3. Compute percentages  
4. Assign priority tiers  
5. Rank sectors  
6. Derive stage distribution  
7. Infer capital intent patterns  
8. Construct scorecard