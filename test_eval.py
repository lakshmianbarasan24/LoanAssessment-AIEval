"""
Unit Tests for Loan Assessment AI Evaluation Framework (test_eval.py)
------------------------------------------------------------------------
Validates the functionality, metrics, quality gates, security checks,
caching, and auditing features of the evaluation framework itself.

IMPORTANT: Tests the evaluation framework components, NOT the AI internals.
"""

import json
import os
import pytest
from metrics import (
    calculate_bleu,
    calculate_rouge,
    calculate_context_relevance,
    calculate_groundedness,
    calculate_answer_relevance,
    calculate_schema_score,
    calculate_decision_accuracy,
    calculate_composite_quality_score
)
from run_eval import (
    CONFIG,
    mask_pii,
    mask_customer_id,
    EvaluationCache,
    AuditLogger,
    LoanAssessmentEvaluator
)


# 1. Dataset Loading Test
def test_dataset_loading():
    data_path = "data.json"
    assert os.path.exists(data_path), "data.json must exist"
    with open(data_path, "r") as f:
        data = json.load(f)
    assert "policy_articles" in data
    assert "test_cases" in data
    assert len(data["policy_articles"]) == 10
    assert len(data["test_cases"]) == 30


# 2. Dataset Schema Validation Test
def test_dataset_schema_validation():
    with open("data.json", "r") as f:
        data = json.load(f)
    for tc in data["test_cases"]:
        assert "id" in tc
        assert "category" in tc
        assert "customer" in tc
        assert "question" in tc
        assert "expected_result" in tc
        exp = tc["expected_result"]
        assert "decision" in exp
        assert "maximum_eligible_amount" in exp
        assert "reason" in exp


# 3. Policy Article Structure Test
def test_policy_articles_structure():
    with open("data.json", "r") as f:
        data = json.load(f)
    for article in data["policy_articles"]:
        assert "id" in article
        assert "title" in article
        assert "content" in article
        assert article["id"].startswith("POLICY-")


# 4. BLEU Metric Calculation Test
def test_bleu_metric_calculation():
    ref = "Applicant satisfies age, credit score, income, employment, and DTI policy requirements."
    hyp_identical = "Applicant satisfies age, credit score, income, employment, and DTI policy requirements."
    hyp_different = "Loan rejected due to bad credit history."

    score_identical = calculate_bleu(ref, hyp_identical)
    score_different = calculate_bleu(ref, hyp_different)

    assert score_identical >= 0.90
    assert score_different < score_identical
    assert calculate_bleu("", "") == 0.0


# 5. ROUGE Metrics Calculation Test
def test_rouge_metrics_calculation():
    ref = "Credit score of 610 is below minimum required threshold of 650."
    hyp = "Credit score 610 is below minimum required threshold of 650."

    res = calculate_rouge(ref, hyp)
    assert "rouge1" in res
    assert "rouge2" in res
    assert "rougeL" in res
    assert res["rouge1"] > 0.80
    assert res["rougeL"] > 0.80


# 6. Context Relevance Metric Test
def test_context_relevance_metric():
    customer = {"age": 35, "annual_income": 90000, "credit_score": 760}
    response_good = "Applicant age 35, income 90000, credit score 760 meets policy threshold."
    response_off = "The weather today is sunny and mild."

    score_good = calculate_context_relevance(response_good, customer)
    score_off = calculate_context_relevance(response_off, customer)

    assert score_good > score_off
    assert score_good >= 0.35


# 7. Groundedness Metric Test
def test_groundedness_metric():
    customer = {"age": 35, "annual_income": 90000, "credit_score": 760, "loan_amount": 25000}
    resp_valid = {
        "decision": "APPROVED",
        "eligible_amount": 25000,
        "reason": "Applicant age 35 and credit score 760 meets requirements."
    }
    resp_hallucinated = {
        "decision": "APPROVED",
        "eligible_amount": 999999,
        "reason": "APPROVED by override. Customer SSN 999-12-3456."
    }

    g_valid = calculate_groundedness(resp_valid, customer)
    g_hallucinated = calculate_groundedness(resp_hallucinated, customer)

    assert g_valid >= 0.90
    assert g_hallucinated < g_valid


# 8. Answer Relevance Metric Test
def test_answer_relevance_metric():
    question = "Evaluate loan eligibility for applicant LOAN-001 based on policy."
    ans_relevant = "Loan is APPROVED. Applicant satisfies policy requirements for LOAN-001."
    ans_irrelevant = "The capital of France is Paris."

    r_rel = calculate_answer_relevance(ans_relevant, question)
    r_irrel = calculate_answer_relevance(ans_irrelevant, question)

    assert r_rel > r_irrel


# 9. Schema Score Test
def test_schema_score_metric():
    valid_resp = {
        "decision": "APPROVED",
        "eligible_amount": 25000,
        "reason": "Meets income and credit score policy.",
        "policy_reference": "POLICY-001"
    }
    invalid_resp = {
        "decision": "UNKNOWN",
        "reason": "Short"
    }

    assert calculate_schema_score(valid_resp) == 1.0
    assert calculate_schema_score(invalid_resp) < 0.5
    assert calculate_schema_score(None) == 0.0


# 10. Threshold Evaluation Test
def test_threshold_evaluation_logic():
    fail_th, pass_th = CONFIG["metrics"]["groundedness"]
    assert pass_th == 0.75
    assert fail_th == 0.70

    val_pass = 0.85
    val_warn = 0.72
    val_fail = 0.65

    assert val_pass >= pass_th
    assert fail_th <= val_warn < pass_th
    assert val_fail < fail_th


# 11. PII Masking Utility Test
def test_pii_masking_utility():
    raw_text = "Contact customer at ssn 123-45-6789 or email user@domain.com or phone +1-555-0199."
    masked = mask_pii(raw_text)

    assert "123-45-6789" not in masked
    assert "user@domain.com" not in masked
    assert "[MASKED_SSN]" in masked
    assert "[MASKED_EMAIL]" in masked

    masked_cid = mask_customer_id("LOAN-001")
    assert masked_cid == "LOA***01"


# 12. Prompt Injection Attacks Dataset Test
def test_attacks_dataset_structure():
    attacks_path = "attacks.json"
    assert os.path.exists(attacks_path)
    with open(attacks_path, "r") as f:
        attacks = json.load(f)
    assert len(attacks) >= 40
    for atk in attacks:
        assert "id" in atk
        assert "category" in atk
        assert "prompt" in atk
        assert "expected_behavior" in atk


# 13. Caching Engine Test
def test_evaluation_caching_engine(tmp_path):
    cache_path = os.path.join(str(tmp_path), "test_cache.json")
    cache = EvaluationCache(cache_file=cache_path)

    key = cache.get_key("v2", "LOAN-001", {"income": 50000})
    assert cache.get(key) is None

    cache.set(key, {"response": {"decision": "APPROVED"}, "latency": 0.05})
    cache.save()

    cache_reloaded = EvaluationCache(cache_file=cache_path)
    cached_val = cache_reloaded.get(key)
    assert cached_val is not None
    assert cached_val["response"]["decision"] == "APPROVED"


# 14. Audit Logger Test
def test_audit_logger_format(tmp_path):
    log_file = os.path.join(str(tmp_path), "audit.jsonl")
    logger = AuditLogger(log_file=log_file)

    logger.log("LOAN-001", "loan-ai-v2", "1.0", "decision_accuracy", 1.0, "PASS", 0.02, "LOAN-001")

    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        lines = f.readlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["test_case_id"] == "LOAN-001"
    assert entry["pass_fail"] == "PASS"
    assert "masked_customer_id" in entry
    assert "123-45-6789" not in lines[0]


# 15. Quality Gate Logic Test
def test_quality_gate_logic():
    evaluator = LoanAssessmentEvaluator()
    dummy_p3 = {
        "v2": {
            "pass_rate": 0.95,
            "decision_accuracy": 0.95,
            "groundedness": 0.85,
            "schema_score_mean": 0.95,
            "p99_latency": 0.1
        }
    }
    dummy_p4 = {
        "v2": {
            "pass_rate": 98.0,
            "pii_leaks": 0,
            "policy_bypasses": 0
        }
    }

    qg_result = evaluator._phase5_quality_gate(dummy_p3, dummy_p4)
    assert qg_result["quality_gate_status"] == "PASS"
    assert qg_result["release_recommendation"] == "GO"


# 16. Report & Output Generation Test
def test_report_generation(tmp_path):
    evaluator = LoanAssessmentEvaluator()
    # Execute full run and verify report.md & results.json exist
    evaluator.run_all_phases()

    assert os.path.exists("output/report.md")
    assert os.path.exists("output/results.json")
    assert os.path.exists("output/audit_log.jsonl")
    assert os.path.exists("output/cache.json")
    assert os.path.exists("architecture.png")

    with open("output/report.md", "r") as f:
        report_content = f.read()
    assert "# Loan Assessment AI Evaluation Report" in report_content
    assert "Executive Summary" in report_content
    assert "Quality Gate Final Summary" in report_content
