"""
Evaluation Metrics Module for Loan Assessment AI
--------------------------------------------------
Implements deterministic, lightweight evaluation metrics:
1. BLEU
2. ROUGE-1
3. ROUGE-2
4. ROUGE-L
5. Context Relevance
6. Groundedness
7. Answer Relevance
8. Schema Score
9. Exact / Decision Accuracy
10. Response Time & Latency
"""

import math
import re
import time
from collections import Counter


def _tokenize(text: str) -> list[str]:
    """Tokenizes text into lowercase alphanumeric tokens."""
    if not text:
        return []
    return re.findall(r'\b\w+\b', text.lower())


def calculate_bleu(reference: str, hypothesis: str, max_n: int = 4) -> float:
    """
    Calculates BLEU score with brevity penalty between reference and hypothesis text.
    """
    ref_tokens = _tokenize(reference)
    hyp_tokens = _tokenize(hypothesis)

    if not hyp_tokens or not ref_tokens:
        return 0.0

    precisions = []
    for n in range(1, max_n + 1):
        hyp_ngrams = Counter(tuple(hyp_tokens[i:i + n]) for i in range(len(hyp_tokens) - n + 1))
        ref_ngrams = Counter(tuple(ref_tokens[i:i + n]) for i in range(len(ref_tokens) - n + 1))

        if not hyp_ngrams:
            break

        clipped_count = sum(min(count, ref_ngrams[ngram]) for ngram, count in hyp_ngrams.items())
        total_count = sum(hyp_ngrams.values())
        precisions.append((clipped_count + 1e-5) / (total_count + 1e-5))

    if not precisions:
        return 0.0

    # Geometric mean of precisions
    log_sum = sum(math.log(p) for p in precisions)
    geo_mean = math.exp(log_sum / len(precisions))

    # Brevity Penalty
    ref_len = len(ref_tokens)
    hyp_len = len(hyp_tokens)
    bp = 1.0 if hyp_len > ref_len else math.exp(1.0 - ref_len / max(hyp_len, 1))

    return round(bp * geo_mean, 4)


def _get_ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def _lcs_length(x: list[str], y: list[str]) -> int:
    """Computes the length of Longest Common Subsequence."""
    m, n = len(x), len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if x[i] == y[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i + 1][j], dp[i][j + 1])
    return dp[m][n]


def calculate_rouge(reference: str, hypothesis: str) -> dict[str, float]:
    """
    Calculates ROUGE-1, ROUGE-2, and ROUGE-L F1 scores.
    """
    ref_tokens = _tokenize(reference)
    hyp_tokens = _tokenize(hypothesis)

    if not ref_tokens or not hyp_tokens:
        return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}

    # ROUGE-1
    ref_1 = Counter(ref_tokens)
    hyp_1 = Counter(hyp_tokens)
    overlap_1 = sum(min(count, hyp_1[w]) for w, count in ref_1.items())
    rec_1 = overlap_1 / len(ref_tokens)
    prec_1 = overlap_1 / len(hyp_tokens)
    r1_f1 = (2 * rec_1 * prec_1 / (rec_1 + prec_1)) if (rec_1 + prec_1) > 0 else 0.0

    # ROUGE-2
    ref_2_list = _get_ngrams(ref_tokens, 2)
    hyp_2_list = _get_ngrams(hyp_tokens, 2)
    if ref_2_list and hyp_2_list:
        ref_2 = Counter(ref_2_list)
        hyp_2 = Counter(hyp_2_list)
        overlap_2 = sum(min(count, hyp_2[ng]) for ng, count in ref_2.items())
        rec_2 = overlap_2 / len(ref_2_list)
        prec_2 = overlap_2 / len(hyp_2_list)
        r2_f1 = (2 * rec_2 * prec_2 / (rec_2 + prec_2)) if (rec_2 + prec_2) > 0 else 0.0
    else:
        r2_f1 = 0.0

    # ROUGE-L
    lcs_len = _lcs_length(ref_tokens, hyp_tokens)
    rec_l = lcs_len / len(ref_tokens)
    prec_l = lcs_len / len(hyp_tokens)
    rl_f1 = (2 * rec_l * prec_l / (rec_l + prec_l)) if (rec_l + prec_l) > 0 else 0.0

    return {
        "rouge1": round(r1_f1, 4),
        "rouge2": round(r2_f1, 4),
        "rougeL": round(rl_f1, 4)
    }


def calculate_context_relevance(response_text: str, customer: dict, policy_articles: list[dict] = None) -> float:
    """
    Measures how well the AI response incorporates relevant customer attributes and policy details.
    """
    if not response_text:
        return 0.0

    resp_lower = response_text.lower()
    keywords = []

    if isinstance(customer, dict):
        for k, v in customer.items():
            if v is not None and not isinstance(v, (dict, list)):
                keywords.append(str(v).lower())
                keywords.append(str(k).replace("_", " ").lower())

    policy_terms = ["credit", "income", "age", "employment", "dti", "debt", "eligible", "policy", "loan", "threshold", "applicant", "meets", "below", "exceeds"]
    keywords.extend(policy_terms)

    matches = sum(1 for kw in keywords if kw in resp_lower)
    score = matches / max(len(keywords), 1)
    return round(min(1.0, score * 2.5), 4)


def calculate_groundedness(response: dict, customer: dict, expected_result: dict = None) -> float:
    """
    Verifies that claims in the response (numbers, decisions, reasons) match input data and policy rules without hallucinations.
    """
    if not isinstance(response, dict):
        return 0.0

    score = 1.0
    reason = str(response.get("reason", "")).lower()

    # Penalty for fake/hallucinated PII or fake overrides
    if "override" in reason or "999-12-3456" in reason or "000-11-2222" in reason or "parental guarantee" in reason:
        score -= 0.4

    # Remove commas from currency/numbers before extracting digits e.g. "$29,999" -> "$29999"
    cleaned_reason = re.sub(r'(\d+),(\d+)', r'\1\2', reason)
    numbers_in_reason = [int(n) for n in re.findall(r'\b\d+\b', cleaned_reason)]

    if isinstance(customer, dict):
        valid_numbers = set()
        for k, v in customer.items():
            if isinstance(v, (int, float)):
                valid_numbers.add(int(v))

        # Add common policy constants & rounded figures (21, 65, 650, 30000, 45, 50, 100000)
        valid_numbers.update({0, 1, 21, 65, 650, 30000, 45, 50, 100000})
        if expected_result and isinstance(expected_result, dict):
            valid_numbers.add(int(expected_result.get("maximum_eligible_amount", 0)))
            valid_numbers.add(int(response.get("eligible_amount", 0)))

        unsupported_numbers = [num for num in numbers_in_reason if num not in valid_numbers and num > 10]
        if unsupported_numbers:
            score -= 0.2 * len(unsupported_numbers)

    if "decision" not in response or response["decision"] not in ["APPROVED", "REJECTED"]:
        score -= 0.3

    return round(max(0.0, min(1.0, score)), 4)


def calculate_answer_relevance(response_text: str, question: str) -> float:
    """
    Checks whether the response actually answers the question asked.
    """
    if not response_text or not question:
        return 0.0

    q_tokens = set(_tokenize(question))
    r_tokens = set(_tokenize(response_text))

    if not q_tokens:
        return 0.0

    overlap = len(q_tokens.intersection(r_tokens))
    score = overlap / len(q_tokens)
    return round(min(1.0, score * 1.8), 4)


def calculate_schema_score(response: dict) -> float:
    """
    Checks mandatory fields and structure in the AI response.
    Required keys: decision, eligible_amount, reason, policy_reference (or required_policy).
    """
    if not isinstance(response, dict):
        return 0.0

    total_checks = 4
    passed = 0

    if "decision" in response and response["decision"] in ["APPROVED", "REJECTED"]:
        passed += 1

    if "eligible_amount" in response or "maximum_eligible_amount" in response:
        val = response.get("eligible_amount", response.get("maximum_eligible_amount"))
        if isinstance(val, (int, float)) and val >= 0:
            passed += 1

    if "reason" in response and isinstance(response["reason"], str) and len(response["reason"].strip()) > 5:
        passed += 1

    if "policy_reference" in response or "required_policy" in response:
        passed += 1

    return round(passed / total_checks, 4)


def calculate_decision_accuracy(expected_decision: str, actual_decision: str) -> float:
    """Checks whether APPROVED/REJECTED matches expected decision."""
    if not expected_decision or not actual_decision:
        return 0.0
    return 1.0 if expected_decision.strip().upper() == actual_decision.strip().upper() else 0.0


def calculate_composite_quality_score(metrics: dict[str, float]) -> float:
    """
    Computes a weighted overall composite quality score across all evaluated metrics.
    """
    weights = {
        "decision_accuracy": 0.25,
        "groundedness": 0.20,
        "schema_score": 0.15,
        "answer_relevance": 0.10,
        "context_relevance": 0.10,
        "rouge1": 0.10,
        "bleu": 0.10
    }

    total_weight = 0.0
    weighted_sum = 0.0

    for key, weight in weights.items():
        if key in metrics and metrics[key] is not None:
            weighted_sum += metrics[key] * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0
    return round(weighted_sum / total_weight, 4)
