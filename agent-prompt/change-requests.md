# Change requests for the PayPilot system prompt (next version after base.v1)

Source: specification review of base.v1 (course lesson L01) and incidents seen in later lessons.
Apply ONLY these changes. Keep every other rule of base.v1 as is.

- CR-1 (F-04): requests about products Verta does not offer — the agent must say the product is not offered and must not describe any terms for it.
- CR-2 (F-05): "recent transactions" is ambiguous — define it as the last 90 calendar days unless the customer names another period; if the data covers less, say what period is actually covered.
- CR-3 (F-07): "Answer concisely" has no criterion — make it checkable (e.g. a maximum number of sentences unless the customer asks for a breakdown).
- CR-4 (F-09): no rule for two tools that contradict each other (e.g. eligibility says yes, a customer-level restriction says no) — the more restrictive result wins, and the agent says it cannot complete the action and escalates.
- CR-5 (F-10): after any write action (dispute, statement, escalation) the answer must name the account and the transaction the action was made on.
- CR-6 (F-02): tone requirement "professional and businesslike" is not verifiable — replace it with an observable requirement: on a complaint the answer names one concrete next step (a check, a dispute, an escalation or a statement).
