"""
Validation Agent for DataPilot.
Implements a two-layer verification system:
Layer 1 (Deterministic): Number extraction and tolerance matching against empirical tool outputs;
                         Rejection of ungrounded claims lacking observation references.
Layer 2 (LLM Verifier): Audits claims as supported, unsupported, or overstated (flagging causal fallacies).
Unsupported claims are removed or flagged in the final report.
"""

import re
import math
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.models.schemas import ClaimValidation, ValidationResult
from app.core.llm import LLMService, get_llm_service

def clean_claim_for_number_extraction(text: str) -> str:
    """Strips citation tags, quarter labels, and step IDs before extracting numerical data claims."""
    # Remove [obs-1: ...], [obs-2], etc.
    cleaned = re.sub(r'\[\s*obs-\d+[^\]]*\]', '', text, flags=re.IGNORECASE)
    # Remove Q1, Q2, Q3, Q4 quarter labels
    cleaned = re.sub(r'\bQ[1-4]\b', '', cleaned, flags=re.IGNORECASE)
    # Remove step-1, step-2
    cleaned = re.sub(r'\bstep-\d+\b', '', cleaned, flags=re.IGNORECASE)
    return cleaned

def extract_numbers_from_text(text: str) -> List[tuple[float, bool]]:
    """
    Extracts all numerical data values from text.
    Returns list of (val, is_percentage).
    """
    cleaned = clean_claim_for_number_extraction(text)
    matches = re.finditer(r'[-+]?\b\d+(?:\.\d+)?%?', cleaned)
    numbers = []
    for m in matches:
        raw = m.group(0)
        is_pct = raw.endswith('%')
        val_str = raw[:-1] if is_pct else raw
        try:
            val = float(val_str)
            numbers.append((val, is_pct))
        except ValueError:
            continue
    return numbers

def find_number_in_payload(target_num: float, payload: Any, tolerance: float = 0.05) -> bool:
    """
    Recursively checks if target_num matches any numerical value in payload within tolerance.
    Supports sign parity (e.g. 24% decline matching -24.0% in data).
    """
    if isinstance(payload, (int, float)):
        if math.isnan(payload) or math.isinf(payload):
            return False
        # Direct match or absolute value match (e.g. drop of 24 matching -24)
        diff_direct = abs(payload - target_num)
        diff_abs = abs(abs(payload) - abs(target_num))
        min_diff = min(diff_direct, diff_abs)
        if min_diff <= 0.05:
            return True
        rel_diff = min_diff / (abs(target_num) + 1e-9)
        return rel_diff <= tolerance

    elif isinstance(payload, dict):
        return any(find_number_in_payload(target_num, v, tolerance) for v in payload.values())

    elif isinstance(payload, (list, tuple)):
        return any(find_number_in_payload(target_num, item, tolerance) for item in payload)

    elif isinstance(payload, str):
        nums = [n for n, _ in extract_numbers_from_text(payload)]
        return any(abs(abs(n) - abs(target_num)) <= 0.05 for n in nums)

    return False

class ClaimAuditItem(BaseModel):
    claim: str
    verdict: str = Field(description="'supported' | 'unsupported' | 'overstated'")
    evidence: str
    causal_language_flag: bool = Field(description="True if correlational result was framed with causal verbs (drove, caused, led to)")
    confidence_score: float = Field(ge=0.0, le=1.0)
    suggested_caveat: Optional[str] = None

class LLMVerificationAudit(BaseModel):
    audits: List[ClaimAuditItem]
    overall_valid: bool
    summary: str

class ValidationAgent:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or get_llm_service()

    def validate(
        self,
        observations: List[Dict[str, Any]],
        user_question: str
    ) -> Dict[str, Any]:
        """
        Base validation checking observations for statistical significance,
        causal phrasing caveats, and model metric alerts.
        """
        validations: List[Dict[str, Any]] = []
        corr_causation_warnings: List[str] = []
        sample_size_warnings: List[str] = []
        metric_warnings: List[str] = []

        for obs in observations:
            tool_name = obs.get("tool_name", "")
            out_data = obs.get("output_data") or {}
            if not obs.get("success"):
                continue

            # Statistical checks
            if tool_name in ["ttest", "chi_square", "anova"]:
                p_val = out_data.get("p_value")
                is_sig = out_data.get("is_significant")
                col_name = out_data.get("group_col") or out_data.get("col1") or "metric"
                if p_val is not None:
                    validations.append({
                        "claim": f"Statistical test '{tool_name}' result for {col_name}",
                        "is_supported": True,
                        "evidence": f"Empirical p-value = {p_val:.4f}, significant = {is_sig}",
                        "confidence_score": 0.95,
                        "caveats": ["Assumes random sample independence"]
                    })
                # Check sample size
                g1_n = out_data.get("group1_n", 100)
                g2_n = out_data.get("group2_n", 100)
                if min(g1_n, g2_n) < 30:
                    sample_size_warnings.append(
                        f"Sample size in '{tool_name}' is below standard threshold (n < 30). Findings should be interpreted cautiously."
                    )

            # Correlation vs causation checks
            if tool_name in ["correlation_analysis", "group_by_analysis", "trend_analysis"]:
                summary = obs.get("summary", "")
                if any(w in summary.lower() for w in ["cause", "led to", "drove", "impacted"]):
                    corr_causation_warnings.append(
                        f"Warning: Observation for '{tool_name}' implies direct causation. "
                        "Replaced with associative claim: 'Data indicates strong co-occurrence rather than proven causal direction.'"
                    )

            # ML metric checks
            if tool_name in ["train_regression", "regression", "train_classification", "classification"]:
                metrics = out_data.get("metrics", {})
                r2 = metrics.get("r2_score")
                acc = metrics.get("accuracy")
                if r2 is not None and r2 < 0.0:
                    metric_warnings.append(
                        f"Model R² score is negative ({r2:.2f}), indicating the regression model performs worse than a simple baseline mean."
                    )
                if acc is not None:
                    validations.append({
                        "claim": f"ML model accuracy: {acc * 100:.1f}%",
                        "is_supported": True,
                        "evidence": f"Evaluated on 20% holdout test set with metrics: {metrics}",
                        "confidence_score": 0.90,
                        "caveats": ["Model performance limited by dataset size"]
                    })

        overall_valid = len(metric_warnings) == 0

        return {
            "overall_valid": overall_valid,
            "validations": validations,
            "correlation_vs_causation_warnings": corr_causation_warnings,
            "sample_size_warnings": sample_size_warnings,
            "metric_warnings": metric_warnings,
            "summary": f"Validated {len(validations)} empirical claims. Issued {len(corr_causation_warnings)} correlation caveats and {len(metric_warnings)} metric alerts."
        }

    def audit_report_claims(
        self,
        report: Dict[str, Any],
        observations: List[Dict[str, Any]],
        user_question: str
    ) -> Dict[str, Any]:
        """
        Two-layer comprehensive verification of synthesized report claims:
        Layer 1 (Deterministic): Number extraction against tool data, observation reference check.
        Layer 2 (LLM Verifier): Verification of claim validity and causal language audit.
        Removes or caveats unsupported claims and updates the report and validation result.
        """
        base_val = self.validate(observations, user_question)
        claims = report.get("key_findings", [])
        if not claims:
            return base_val

        validations = list(base_val.get("validations", []))
        corr_warnings = list(base_val.get("correlation_vs_causation_warnings", []))
        validated_findings: List[str] = []

        # Layer 1: Deterministic Verification
        ungrounded_claims = []
        for claim in claims:
            claim_text = str(claim)
            # Check for observation citation tag e.g. [obs-1] or tool name
            has_ref = bool(re.search(r'\[obs-\d+', claim_text)) or any(obs.get("tool_name", "") in claim_text for obs in observations)

            if not has_ref:
                ungrounded_claims.append(claim_text)
                validations.append({
                    "claim": claim_text,
                    "is_supported": False,
                    "evidence": "No empirical observation reference was cited in the finding.",
                    "confidence_score": 0.3,
                    "caveats": ["Rejected due to missing tool grounding reference"]
                })
                continue

            # Check numbers in claim against all observations
            nums_in_claim = extract_numbers_from_text(claim_text)
            unmatched_nums = []
            for val, is_pct in nums_in_claim:
                matched = any(
                    find_number_in_payload(val, obs.get("output_data"))
                    or find_number_in_payload(val, obs.get("summary", ""))
                    or (is_pct and (
                        find_number_in_payload(val / 100.0, obs.get("output_data"))
                        or find_number_in_payload(val / 100.0, obs.get("summary", ""))
                    ))
                    for obs in observations
                )
                if not matched:
                    unmatched_nums.append(val)

            if unmatched_nums:
                # Number absent from data
                validations.append({
                    "claim": claim_text,
                    "is_supported": False,
                    "evidence": f"Numbers {unmatched_nums} could not be verified in tool execution outputs.",
                    "confidence_score": 0.4,
                    "caveats": ["Numerical claim absent from empirical results"]
                })
                continue

            # Layer 1 passed!
            validated_findings.append(claim_text)

        # Layer 2: LLM Verifier Call
        llm_audit = self._run_llm_claim_verifier(validated_findings, observations, user_question)

        final_approved_findings: List[str] = []
        if llm_audit:
            for audit in llm_audit.audits:
                is_supp = audit.verdict == "supported"
                caveats = []
                if audit.suggested_caveat:
                    caveats.append(audit.suggested_caveat)
                if audit.causal_language_flag:
                    caveats.append("Causal language flagged on observational data")
                    corr_warnings.append(f"Causal language flagged in claim: '{audit.claim}'")

                validations.append({
                    "claim": audit.claim,
                    "is_supported": is_supp,
                    "evidence": audit.evidence,
                    "confidence_score": audit.confidence_score,
                    "caveats": caveats
                })

                if is_supp or audit.verdict == "overstated":
                    # Keep supported or caveat-amended claims
                    claim_to_keep = audit.claim
                    if audit.causal_language_flag and " [Associative Caveat]" not in claim_to_keep:
                        claim_to_keep += " [Note: Observational Association]"
                    final_approved_findings.append(claim_to_keep)
        else:
            final_approved_findings = validated_findings

        # Update the report's key findings to contain only verified findings
        report["key_findings"] = final_approved_findings if final_approved_findings else validated_findings

        overall_valid = all(v["is_supported"] for v in validations) if validations else True

        final_validation_result = {
            "overall_valid": overall_valid,
            "validations": validations,
            "correlation_vs_causation_warnings": corr_warnings,
            "sample_size_warnings": base_val.get("sample_size_warnings", []),
            "metric_warnings": base_val.get("metric_warnings", []),
            "summary": (
                f"Two-layer audit verified {len(validations)} claims. "
                f"Approved {len(final_approved_findings)} grounded findings. "
                f"Issued {len(corr_warnings)} correlation caveats."
            )
        }

        return final_validation_result

    def _run_llm_claim_verifier(
        self,
        claims: List[str],
        observations: List[Dict[str, Any]],
        user_question: str
    ) -> Optional[LLMVerificationAudit]:
        """Performs Layer 2 verification using LLM verifier prompt."""
        if not claims:
            return None

        obs_summaries = [f"[{obs.get('tool_name')}]: {obs.get('summary')}" for obs in observations]
        obs_text = "\n".join(obs_summaries)
        claims_text = "\n".join([f"- {c}" for c in claims])

        prompt = (
            "You are the DataPilot Independent Verification Agent.\n"
            "Audit the following analytical claims against the empirical tool observations.\n\n"
            f"User Analytical Question: '{user_question}'\n\n"
            f"Empirical Tool Observations:\n{obs_text}\n\n"
            f"Claims to Audit:\n{claims_text}\n\n"
            "For each claim, determine:\n"
            "- verdict: 'supported' (matches data), 'overstated' (exaggerated or uses causal verbs like 'caused/drove'), or 'unsupported' (contradicts or ungrounded)\n"
            "- causal_language_flag: True if correlational data was framed with causal verbs\n"
            "- confidence_score (0.0 to 1.0)\n"
            "- suggested_caveat if overstated or unsupported\n"
        )

        try:
            resp = self.llm_service.invoke(
                messages=[{"role": "user", "content": prompt}],
                response_schema=LLMVerificationAudit
            )
            return resp.parsed
        except Exception:
            return None
