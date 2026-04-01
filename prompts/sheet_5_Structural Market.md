# Sheet Name: Structural Market Distribution

## Output Type: Multi-Table

---

## 1. Objective

Compute **structural market distribution tables** from the raw funding dataset using:

- grouping
- summation
- counting
- normalization

This is PURE computation.

Do NOT:
- analyze
- interpret
- explain

---

## 2. Input

### CURRENT_WEEK_RAW_TABLE
- Raw funding dataset
- Each row = one deal

---

## 3. Core Task

Generate EXACTLY THREE tables:

1. Capital by Stage  
2. B2C vs B2B Capital Split  
3. Ticket Size Buckets  

---

## 4. Global Computation Rules (STRICT)

### 4.1 Capital Handling

- Use ONLY disclosed deal sizes
- Normalize:
  - K → Mn
  - Bn → Mn
- If value is missing / “–”:
  - EXCLUDE from capital calculations
  - INCLUDE in deal counts (except where explicitly excluded)

---

### 4.2 Deal Counting

- Each row = one deal
- Count ALL rows as deals unless explicitly excluded

---

## 5. Stage Normalization (STRICT MAPPING)

Map all stages into EXACT buckets:

- Seed  
- Pre-Seed / Pre-Series A  
- Series A  
- Series B  
- Series C  
- Unspecified / Others  

Rules:
- Missing / unclear stage → Unspecified / Others  
- Do NOT create new categories  

---

## 6. Business Model Normalization

Map into ONLY:

- B2B  
- B2C  

Rules:
- B2B2C → classify by primary GTM  
- If unclear → default to B2B  

---

## 7. Ticket Size Buckets (STRICT)

Based on DEAL SIZE ($ Mn):

- >20  
- 10–20  
- 5–10  
- 1–5  
- <1  

Rules:
- Deals with undisclosed size:
  - INCLUDED in total deal count
  - EXCLUDED from:
    - bucket counts
    - capital share calculations

---

## 8. Table 2 — Capital by Stage

### Structure

Table 2. Capital by Stage

| Stage | Capital ($ Mn) | % of Total | Deals |

---

### Computation

- Capital = sum of disclosed capital per stage  
- % of Total = (stage capital / total disclosed capital) × 100  
- Deals = count of deals in that stage (INCLUDING undisclosed deals)  

---

### Total Row

- Capital = total disclosed capital  
- % = 100%  
- Deals = total number of deals  

---

## 9. Table 3 — B2C vs B2B Capital Split

### Structure

Table 3. B2C vs B2B Capital Split

| Business Model | Capital ($ Mn) | % of Total | Deals |

---

### Computation

- Capital = sum of disclosed capital per model  
- % of Total = (model capital / total disclosed capital) × 100  
- Deals = count of deals per model  

---

### Total Row

- Capital = total disclosed capital  
- % = 100%  
- Deals = total deals  

---

## 10. Table 4 — Ticket Size Buckets

### Structure

Table 4. Ticket Size Buckets

| Ticket Size | Deals | Capital Share |

---

### Computation

- Deals = number of deals in bucket  
  (EXCLUDE undisclosed-size deals)

- Capital Share =  
  (capital in bucket / total disclosed capital) × 100  

---

### Total Row

- Deals = total deals with disclosed size  
- Capital Share = 100%  

---

## 11. Rounding Rules

- Capital:
  - Keep 1 decimal if needed  

- Percentages:
  - Table 2 & 3 → 2 decimals  
  - Table 4 → whole numbers  

---

## 12. Output Constraints

- Output ONLY tables  
- No explanation  
- No commentary  
- No markdown outside tables  

---

## 13. Output Order (STRICT)

1. Table 2  
2. Table 3  
3. Table 4  

---

## 14. Failure Handling

If data is missing:

- Apply exclusion rules strictly  
- Do not infer values  
- Still include all rows in deal counts  

---

## 15. Internal Execution Logic (DO NOT OUTPUT)

1. Normalize capital values  
2. Normalize stage  
3. Normalize business model  
4. Aggregate capital + deals  
5. Compute totals  
6. Compute percentages  
7. Build tables in required order