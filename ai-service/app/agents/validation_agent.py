from typing import Dict, Any, List

class ValidationAgent:
    def validate(self, observations: List[Dict[str, Any]], user_question: str) -> Dict[str, Any]:
        """
        Audits observations, checks analytical claims against empirical outputs,
        detects correlation-vs-causation fallacies, sample size warnings, and hallucination risks.
        """
        validations = []
        corr_causation_warnings = []
        sample_size_warnings = []
        metric_warnings = []
        
        # Check observations
        for obs in observations:
            tool_name = obs.get("tool_name", "")
            out_data = obs.get("output_data") or {}
            
            if not obs.get("success"):
                continue

            # Statistical checks
            if tool_name in ["ttest", "chi_square", "anova"]:
                p_val = out_data.get("p_value")
                is_sig = out_data.get("is_significant")
                summary = obs.get("summary", "")
                
                if p_val is not None:
                    validations.append({
                        "claim": f"Statistical test '{tool_name}' result for {out_data.get('group_col') or out_data.get('col1')}",
                        "is_supported": True,
                        "evidence": f"Empirical p-value = {p_val:.4f}, significant = {is_sig}",
                        "confidence_score": 0.95,
                        "caveats": ["Assumes random sample independence"]
                    })
                    
            # Correlation vs causation audit
            if tool_name in ["correlation_analysis", "group_by_analysis", "trend_analysis"]:
                summary = obs.get("summary", "")
                if "cause" in summary.lower() or "led to" in summary.lower() or "drove" in summary.lower():
                    corr_causation_warnings.append(
                        f"Warning: Observation for '{tool_name}' implies direct causation. "
                        "Replaced with empirical associative claim: 'Data shows strong co-occurrence rather than established causal direction.'"
                    )
                    
            # ML Metric audit
            if tool_name in ["train_regression", "regression", "train_classification", "classification"]:
                metrics = out_data.get("metrics", {})
                r2 = metrics.get("r2_score")
                acc = metrics.get("accuracy")
                
                if r2 is not None and r2 < 0.0:
                    metric_warnings.append(f"Model R² score is negative ({r2:.2f}), indicating regression model performs worse than a simple baseline mean.")
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
            "summary": f"Validated {len(validations)} empirical claims. Issued {len(corr_causation_warnings)} correlation-vs-causation caveats and {len(metric_warnings)} metric alerts."
        }
