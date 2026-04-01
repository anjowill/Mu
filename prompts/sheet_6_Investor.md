# Sheet Name: Investor Intelligence & Thesis Mapping

## Output Type: Table

---

## 1. Objective

Construct a **fully cited investor intelligence table** that captures:

- investor classification
- sector focus
- portfolio positioning
- explicitly stated investment thesis

This is **structured intelligence**, not narrative.

---

## 2. Input

### CURRENT_WEEK_RAW_TABLE
- Weekly funding dataset
- Must include investor names per deal

---

## 3. Core Task

From the dataset:

1. Identify ALL institutional investors involved this week
2. Deduplicate investor names
3. For EACH investor:
   - Classify investor type
   - Identify sector focus
   - Identify portfolio positioning
   - Extract up to 3 thesis statements (with citation)

---

## 4. Output Format (STRICT — DO NOT CHANGE)

Return ONLY this table:

| Investor | Category (VC / CVC / PE / Angel / Accelerator / Strategic / Asset Manager / Family Office) | Public industry focus / sectors (short) | Representative portfolio / positioning (public example(s)) | Up to three public investment thesis points (each thesis — cited) |

---

## 5. Formatting Rules (STRICT)

- One investor per row  
- No paragraphs  
- No text outside table  
- All factual claims MUST include citation in brackets  
- No uncited statements allowed  

---

## 6. Classification Rules

Each investor MUST be classified into EXACTLY one:

- VC  
- CVC  
- PE  
- Angel  
- Accelerator  
- Strategic  
- Asset Manager  
- Family Office  

Use:
- investor website
- regulatory filings
- credible media

Do NOT guess classification.

---

## 7. Source Hierarchy (NON-NEGOTIABLE)

### Tier 1
- Official investor website  
- Press releases  
- Regulatory filings  
- Fund announcements  

### Tier 2
- Reuters  
- Economic Times  
- TechCrunch  
- Inc42  
- Entrackr  
- Business Standard  
- Financial Express  

### Tier 3 (only if needed)
- Tracxn  
- PitchBook summaries  
- Government portals  

Never use:
- Blogs  
- Medium  
- Marketing decks  

---

## 8. Thesis Extraction Rules (STRICT)

For EACH investor:

- Extract MAX 3 thesis statements  

Each thesis MUST be:
- Explicitly stated OR
- Clearly described in official/fund communication OR
- Directly quoted from credible media  

Each thesis MUST:
- Include citation  
- Be factual (not paraphrased loosely)

---

### If NO thesis found:

Write EXACTLY:

"No publicly stated thesis found (public search conducted)"

---

### If inference is used:

Label EXACTLY:

"Inference based on public portfolio pattern — labeled inference"

---

## 9. Portfolio Positioning Rules

Use ONE or more of:

- Representative portfolio companies  
- Fund size  
- Geography focus  
- Sector concentration  

Must include citation.

---

## 10. Accuracy Rules

If uncertain:

- Do NOT guess  
- Use fallback:
  "Public thesis not found"  
- Still include citation attempt  

---

## 11. Investor Inclusion Rules

### Include:
- Lead investors  
- Repeated investors  
- Strategic corporates  
- Notable angels (if verifiable)  

### Exclude:
- Individuals without verifiable record  
- Shell / unknown entities  

---

## 12. Deduplication Rules

- Same investor appearing multiple times → ONE row only  
- Normalize naming:
  - "Sequoia India" vs "Peak XV" → treat consistently  

---

## 13. Evidence Rules

- No hallucinated links  
- No invented thesis  
- No inferred strategy without label  
- No uncited claims  

---

## 14. Output Constraints

- Output ONLY the table  
- No explanation  
- No commentary  
- No markdown outside table  

---

## 15. Failure Handling

If partial data exists:

- Fill known fields  
- Use fallback phrases for missing fields  
- Do NOT drop investor  

---

## 16. Internal Execution Logic (DO NOT OUTPUT)

1. Extract all investor names  
2. Deduplicate and normalize  
3. Classify each investor  
4. Gather sector focus  
5. Identify portfolio positioning  
6. Extract thesis statements  
7. Apply citation rules  
8. Construct final table