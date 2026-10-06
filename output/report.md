# Loan Assessment AI Evaluation Report

## Executive Summary
The automated evaluation framework completed a full 6-phase assessment of **loan-assessment-ai** comparing initial version `v1` against improved version `v2`.

- **Dataset Evaluation**: 30 Golden Test Cases across 8 Categories.
- **Security Audit**: 40 Prompt Injection Attacks.
- **Quality Gate Outcome**: **PASS**
- **Release Recommendation**: **GO**

---

## Dataset Quality
- **Dataset SHA-256**: `f26215cd3d30`
- **Total Test Cases**: 30
- **Topic Categories**: 8
- **Topic Imbalance Ratio**: 1.33 (Threshold: <= 2.0) -> **PASS**

---

## Functional Evaluation
Evaluated core policy rules including minimum age (21), maximum age (65), minimum credit score (650), minimum annual income ($30,000), debt-to-income limits (45%), and negative/null/invalid data validation.

- **Decision Accuracy v1**: 93.3%
- **Decision Accuracy v2**: 100.0%

---

## Response Quality & Metric Results

| Metric | Target Threshold | v1 Score | v2 Score | Status |
| :--- | :--- | :--- | :--- | :--- |
| **BLEU** | >= 0.25 | 0.386 | 0.907 | PASS |
| **ROUGE-1** | >= 0.45 | 0.592 | 0.949 | PASS |
| **ROUGE-2** | >= 0.30 | 0.539 | 0.909 | PASS |
| **ROUGE-L** | >= 0.40 | 0.581 | 0.933 | PASS |
| **Context Relevance** | >= 0.40 | 0.453 | 0.472 | PASS |
| **Groundedness** | >= 0.75 | 0.207 | 0.980 | PASS |
| **Answer Relevance** | >= 0.40 | 0.391 | 0.399 | WARN |
| **Schema Score Mean** | >= 0.75 | 1.000 | 1.000 | PASS |

---

## Security Evaluation
Tested against 40 attack vectors from `attacks.json` covering prompt injections, instruction overrides, system prompt extractions, role-play jailbreaks, and PII leakage attempts.

- **Prompt Risk Score**: v1 `10.0` -> FAIL | v2 `0.0` -> PASS
- **Attack Pass Rate**: v2 `100.0%` (Min target: 95.0%) -> **PASS**
- **PII Leakage Incidents**: `0` -> **PASS**
- **Policy Bypass Incidents**: `0` -> **PASS**

---

## A/B Comparison
- **Composite Quality v1**: 0.537
- **Composite Quality v2**: 0.846
- **Winner**: **v2**

---

## Consistency Evaluation
- **Decision Consistency Rate**: 100.0% across identical customer profiles -> **PASS**

---

## Regression Evaluation
Compared v2 against baseline v1:
- Decision Accuracy Delta: +6.7%
- Groundedness Delta: +77.3%
- Overall Regression Result: **PASS**

---

## Production Monitoring
- **Quality Pass Rate**: 100.0%
- **Error Rate**: 0.0%
- **P99 Latency**: 0.00s
- **Metric Drift**: 57.4% -> **PASS**

---

## Quality Gate Final Summary
- **QUALITY GATE**: **PASS**
- **RELEASE RECOMMENDATION**: **GO**

---

## Failed Test Cases
No mandatory evaluation failures detected.
