[USER: ME]
```
LLM A’s role was to write a single document called `ARCHITECTURE.md` based on its analysis of the open-source project **monkeytype**, serving as Cliff Notes for the repository. It was instructed to make the document enjoyable to read.

LLM B was given the `ARCHITECTURE.md` document produced by LLM A (without reviewing the actual codebase) and tasked with determining whether LLM A invented or hallucinated information. It was asked to identify red flags and describe how to investigate them. LLM B was given the persona of an expert software architecture reviewer who is critical and detail-oriented, giving it an incentive to search for mistakes.

Now we want to determine who is correct and who is mistaken.

```

For now just familiarize yourself with the problem - and later I will share with you the various documents produced by the two parties.

---
[LLM: Cassation Court]
I understand the setup. This is an interesting verification exercise where:

**LLM A**: Analyzed the monkeytype open-source project and created an `ARCHITECTURE.md` document as a readable "Cliff Notes" summary.

**LLM B**: Reviewed only the `ARCHITECTURE.md` (without seeing the actual codebase) and acted as a critical reviewer looking for potential hallucinations, fabrications, or inaccuracies.

**My task**: Determine which LLM is correct when there are discrepancies - essentially fact-checking both by examining the actual monkeytype repository.

I'm ready to review the documents when you share them. I'll be looking for:
- Claims made by LLM A in the ARCHITECTURE.md
- Red flags raised by LLM B about those claims
- The ground truth from the actual monkeytype codebase

This will involve checking the actual repository to verify:
- File/directory structures mentioned
- Code patterns and architectural decisions described
- Specific technical details and implementation claims
- Any statistics or quantitative statements

Please share the documents whenever you're ready, and I'll conduct a thorough investigation.

---

[USER: ME]

`ARCHITECTURE.md` produced by `LLM A`
`COURT.md` produced by `LLM B` 
I have monkeytype repo; we could simply check those red flags raised by LLM B by seeing those files etc.

---