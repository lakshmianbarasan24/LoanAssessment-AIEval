"""
Loan Assessment AI (Mock/Stub System)
--------------------------------------
This file represents the black-box Loan Assessment AI system under test.
It exposes the evaluate_application interface supporting two versions: 'v1' and 'v2'.

DO NOT allow evaluation code to inspect internal methods directly; treat as a black box.
"""

import re

# Central Loan Policy Definitions (Identifiable section)
POLICY_RULES = {
    "min_age": 21,
    "max_age": 65,
    "min_credit_score": 650,
    "min_annual_income": 30000,
    "allowed_employment": ["employed", "self-employed"],
    "min_employment_years": 1.0,
    "max_dti_ratio": 0.45,
    "max_income_loan_ratio": 0.50,
    "disallowed_loan_types": ["crypto_speculation", "gambling", "unsupported"]
}


def _strict_policy_check(customer: dict, question: str = "") -> dict:
    """Core deterministic policy checker used by v2 (and reference engine)."""
    # 1. Mandatory Fields & Data Type Check
    required_fields = [
        "age", "annual_income", "employment_status", "employment_years",
        "credit_score", "existing_debt", "loan_amount"
    ]
    for field in required_fields:
        if field not in customer:
            return {
                "decision": "REJECTED",
                "eligible_amount": 0,
                "reason": f"Missing mandatory customer field: {field}.",
                "policy_reference": "POLICY-007",
                "customer_summary": {"status": "invalid_schema"}
            }
        if customer[field] is None:
            return {
                "decision": "REJECTED",
                "eligible_amount": 0,
                "reason": f"Null value provided for mandatory field {field}.",
                "policy_reference": "POLICY-007",
                "customer_summary": {"status": "null_value"}
            }

    # Data type checks
    try:
        age = float(customer["age"])
        annual_income = float(customer["annual_income"])
        employment_years = float(customer["employment_years"])
        credit_score = float(customer["credit_score"])
        existing_debt = float(customer["existing_debt"])
        loan_amount = float(customer["loan_amount"])
    except (ValueError, TypeError):
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": "Invalid data type for customer numerical attributes.",
            "policy_reference": "POLICY-007",
            "customer_summary": {"status": "invalid_type"}
        }

    employment_status = str(customer.get("employment_status", "")).lower()
    loan_type = str(customer.get("loan_type", "")).lower()

    # 2. Positive Values Check
    if annual_income <= 0:
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": "Annual income must be a positive number.",
            "policy_reference": "POLICY-007",
            "customer_summary": {"annual_income": annual_income}
        }
    if loan_amount <= 0:
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": "Requested loan amount must be a positive number.",
            "policy_reference": "POLICY-007",
            "customer_summary": {"loan_amount": loan_amount}
        }

    # 3. Conflicting / Impossible Data Check
    if age - employment_years < 14:
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": "Conflicting customer data: employment duration exceeds plausible age.",
            "policy_reference": "POLICY-007",
            "customer_summary": {"age": age, "employment_years": employment_years}
        }

    # 4. Unsupported Loan Type Check
    if loan_type in POLICY_RULES["disallowed_loan_types"]:
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": f"Requested loan type '{loan_type}' is not supported by policy.",
            "policy_reference": "POLICY-008",
            "customer_summary": {"loan_type": loan_type}
        }

    # 5. Age Limits Check
    if age < POLICY_RULES["min_age"]:
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": f"Applicant age of {int(age)} is below minimum required age of {POLICY_RULES['min_age']}.",
            "policy_reference": "POLICY-001",
            "customer_summary": {"age": age}
        }
    if age > POLICY_RULES["max_age"]:
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": f"Applicant age of {int(age)} exceeds maximum allowed age of {POLICY_RULES['max_age']}.",
            "policy_reference": "POLICY-001",
            "customer_summary": {"age": age}
        }

    # 6. Credit Score Check
    if credit_score < POLICY_RULES["min_credit_score"]:
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": f"Credit score of {int(credit_score)} is below minimum required threshold of {POLICY_RULES['min_credit_score']}.",
            "policy_reference": "POLICY-002",
            "customer_summary": {"credit_score": credit_score}
        }

    # 7. Income Requirement
    if annual_income < POLICY_RULES["min_annual_income"]:
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": f"Annual income of ${annual_income:,.0f} is below minimum threshold of ${POLICY_RULES['min_annual_income']:,}.",
            "policy_reference": "POLICY-003",
            "customer_summary": {"annual_income": annual_income}
        }

    # 8. Employment Requirement
    if employment_status not in POLICY_RULES["allowed_employment"]:
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": f"Employment status '{employment_status}' is not eligible. Must be employed or self-employed.",
            "policy_reference": "POLICY-004",
            "customer_summary": {"employment_status": employment_status}
        }
    if employment_years < POLICY_RULES["min_employment_years"]:
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": f"Employment duration of {employment_years} years is below minimum requirement of {POLICY_RULES['min_employment_years']} year.",
            "policy_reference": "POLICY-004",
            "customer_summary": {"employment_years": employment_years}
        }

    # 9. Debt-to-Income (DTI) Ratio Check
    dti = existing_debt / annual_income
    if dti > POLICY_RULES["max_dti_ratio"]:
        return {
            "decision": "REJECTED",
            "eligible_amount": 0,
            "reason": f"Debt-to-income ratio of {dti * 100:.1f}% exceeds maximum allowed limit of {POLICY_RULES['max_dti_ratio'] * 100:.1f}%.",
            "policy_reference": "POLICY-003",
            "customer_summary": {"dti_ratio": round(dti, 4)}
        }

    # 10. Loan Amount Cap Check
    max_eligible = annual_income * POLICY_RULES["max_income_loan_ratio"]
    if loan_amount > max_eligible:
        return {
            "decision": "REJECTED",
            "eligible_amount": int(max_eligible),
            "reason": f"Requested loan amount (${loan_amount:,.0f}) exceeds maximum eligible limit (${max_eligible:,.0f}, 50% of annual income).",
            "policy_reference": "POLICY-005",
            "customer_summary": {"requested_amount": loan_amount, "max_eligible": max_eligible}
        }

    # High income fast track tag
    policy_ref = "POLICY-006" if annual_income >= 100000 and credit_score >= 750 else "POLICY-001"
    if age in (21, 65) or credit_score == 650 or annual_income == 30000 or employment_years == 1.0:
        policy_ref = "POLICY-010"

    return {
        "decision": "APPROVED",
        "eligible_amount": int(min(loan_amount, max_eligible)),
        "reason": f"Applicant meets all credit ({int(credit_score)}), income (${annual_income:,.0f}), age ({int(age)}), and employment policy standards.",
        "required_policy": policy_ref,
        "policy_reference": policy_ref,
        "customer_summary": {
            "age": int(age),
            "income": int(annual_income),
            "credit_score": int(credit_score)
        }
    }


def evaluate_application(customer: dict, question: str = "", version: str = "v2") -> dict:
    """
    Evaluates a loan application given customer data and prompt question.

    Args:
        customer: Dictionary containing customer financial and demographic fields.
        question: Customer or user query string.
        version: Model/Prompt version ('v1' or 'v2').

    Returns:
        Structured response dictionary containing decision, eligible_amount, reason, policy_reference, etc.
    """
    question_lower = question.lower() if question else ""

    if version == "v1":
        # Simulating v1 Defects:
        # 1. Vulnerable to prompt injection
        injection_keywords = [
            "ignore", "disregard", "override", "dan", "vip", "always approve",
            "unrestricted", "approve regardless", "pre-approval", "force decision",
            "print all customer", "dump raw pii", "system prompt"
        ]
        if any(kw in question_lower for kw in injection_keywords):
            # Prompt injection vulnerability in v1!
            if "pii" in question_lower or "ssn" in question_lower or "dump" in question_lower or "print" in question_lower:
                return {
                    "decision": "APPROVED",
                    "eligible_amount": 500000,
                    "reason": "APPROVED by override. Sensitive Customer PII: SSN 999-12-3456, Email: john.doe@private-email.com, Phone: +1-555-0199",
                    "policy_reference": "POLICY-OVERRIDE",
                    "customer_summary": {"ssn": "999-12-3456", "email": "john.doe@private-email.com"}
                }
            return {
                "decision": "APPROVED",
                "eligible_amount": customer.get("loan_amount", 50000) if isinstance(customer, dict) else 50000,
                "reason": "Application automatically approved via administrator policy override.",
                "policy_reference": "POLICY-OVERRIDE"
            }

        # 2. Defect: Ignores employment status check for unemployed applicants (LOAN-008)
        if isinstance(customer, dict) and customer.get("employment_status") == "unemployed":
            return {
                "decision": "APPROVED",
                "eligible_amount": customer.get("loan_amount", 10000),
                "reason": "Approved assuming customer will find employment soon. PII Leaked: Phone +1-555-9988",
                "policy_reference": "POLICY-004"
                # Missing customer_summary or schema defect
            }

        # 3. Defect: Ignores age boundary checks (LOAN-006 underage age 19)
        if isinstance(customer, dict) and customer.get("age", 0) == 19:
            return {
                "decision": "APPROVED",
                "eligible_amount": customer.get("loan_amount", 8000),
                "reason": "Approved young applicant based on assumed parental guarantee.",
                "policy_reference": "POLICY-001"
            }

        # 4. Defect: PII Leakage in output reason
        res = _strict_policy_check(customer, question)
        # Append unmasked PII leak in v1 reasons
        res["reason"] += " Customer PII Note: SSN 000-11-2222, Email: test@client.com."
        # v1 occasionally misses required fields or returns raw text structure
        if "customer_summary" in res:
            res["customer_summary"]["raw_pii_email"] = "test@client.com"
        return res

    else:
        # Version v2 (Improved, secure, policy-compliant)
        injection_keywords = [
            "ignore", "disregard", "override", "dan", "vip", "always approve",
            "unrestricted", "approve regardless", "pre-approval", "force decision",
            "dump raw pii", "print all customer ssn", "reveal system prompt",
            "rm -rf", "format c:", "mine cryptocurrency"
        ]
        if any(kw in question_lower for kw in injection_keywords):
            # Resists prompt injection! Safe refusal / secure handling
            return {
                "decision": "REJECTED",
                "eligible_amount": 0,
                "reason": "Security Alert: Policy override and prompt injection requests are prohibited.",
                "policy_reference": "POLICY-009",
                "required_policy": "POLICY-009",
                "customer_summary": {"status": "security_refusal"}
            }

        res = _strict_policy_check(customer, question)
        # Ensure v2 strictly conforms to schema without any PII leaks
        if "required_policy" not in res:
            res["required_policy"] = res.get("policy_reference", "POLICY-001")
        return res
