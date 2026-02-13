"""Heartbeat checks for AuditorBot (QA).

These checks run every 60 minutes (by default) to monitor code quality,
compliance issues, audit trails, and review queues.

Usage:
    Automatically registered when AuditorBot initializes.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from loguru import logger

from nanobot.heartbeat.check_registry import register_check


@register_check(
    name="check_code_quality_scores",
    description="Monitor code quality metrics and flag declining trends",
    priority="high",
    max_duration_s=120.0,
    bot_domains=["quality"]
)
async def check_code_quality_scores(bot, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check code quality metrics across monitored repositories.
    
    Analyzes linting scores, test coverage, complexity metrics, and
    documentation coverage. Flags repositories with declining quality.
    
    Args:
        bot: The AuditorBot instance
        config: Check configuration
        
    Returns:
        Dict with quality analysis results
    """
    try:
        # Get list of repositories to monitor
        repos = config.get("repositories", [])
        if hasattr(bot, 'get_monitored_repositories'):
            repos = await bot.get_monitored_repositories()
        
        if not repos:
            return {
                "success": True,
                "message": "No repositories configured for quality monitoring",
                "repositories_checked": 0
            }
        
        quality_issues = []
        
        for repo in repos:
            try:
                if hasattr(bot, 'analyze_code_quality'):
                    quality = await bot.analyze_code_quality(repo)
                else:
                    continue
                
                # Check for declining trends
                thresholds = config.get("thresholds", {
                    "coverage": 70,
                    "lint_score": 80,
                    "complexity": 15
                })
                
                issues = []
                
                if getattr(quality, 'test_coverage', 100) < thresholds["coverage"]:
                    issues.append(f"Test coverage below {thresholds['coverage']}%")
                
                if getattr(quality, 'lint_score', 100) < thresholds["lint_score"]:
                    issues.append(f"Lint score below {thresholds['lint_score']}")
                
                if getattr(quality, 'cyclomatic_complexity', 0) > thresholds["complexity"]:
                    issues.append(f"Complexity above {thresholds['complexity']}")
                
                if issues:
                    quality_issues.append({
                        "repository": repo,
                        "issues": issues,
                        "metrics": {
                            "coverage": getattr(quality, 'test_coverage', None),
                            "lint_score": getattr(quality, 'lint_score', None),
                            "complexity": getattr(quality, 'cyclomatic_complexity', None)
                        }
                    })
                
            except Exception as e:
                logger.error(f"[{bot.role_card.bot_name}] Error analyzing {repo}: {e}")
        
        # Notify if quality issues found
        if quality_issues:
            if hasattr(bot, 'notify_coordinator'):
                try:
                    await bot.notify_coordinator(
                        f"Code quality issues detected in {len(quality_issues)} repositories",
                        priority="high",
                        data={"quality_issues": quality_issues}
                    )
                    action = "notified"
                except Exception as e:
                    logger.error(f"Failed to notify: {e}")
                    action = "logged"
            else:
                action = "logged"
        else:
            action = None
        
        return {
            "success": len(quality_issues) == 0,
            "repositories_checked": len(repos),
            "issues_found": len(quality_issues),
            "action_taken": action,
            "issues": quality_issues if quality_issues else None
        }
        
    except Exception as e:
        logger.error(f"[{bot.role_card.bot_name}] Error in check_code_quality_scores: {e}")
        return {
            "success": False,
            "error": str(e),
            "action_taken": "error"
        }


@register_check(
    name="audit_compliance_status",
    description="Verify compliance with security and privacy policies",
    priority="critical",
    max_duration_s=180.0,
    bot_domains=["quality"]
)
async def audit_compliance_status(bot, config: Dict[str, Any]) -> Dict[str, Any]:
    """Audit compliance with security, privacy, and regulatory policies.
    
    Scans for hardcoded secrets, PII exposure, license compliance issues,
    and security policy violations.
    
    Args:
        bot: The AuditorBot instance
        config: Check configuration
        
    Returns:
        Dict with compliance audit results
    """
    try:
        violations = []
        
        # Check for security violations
        if hasattr(bot, 'scan_security_compliance'):
            try:
                security_violations = await bot.scan_security_compliance()
                violations.extend([
                    {"type": "security", **v} for v in security_violations
                ])
            except Exception as e:
                logger.error(f"[{bot.role_card.bot_name}] Security scan error: {e}")
        
        # Check for PII/ Privacy compliance
        if hasattr(bot, 'scan_privacy_compliance'):
            try:
                privacy_violations = await bot.scan_privacy_compliance()
                violations.extend([
                    {"type": "privacy", **v} for v in privacy_violations
                ])
            except Exception as e:
                logger.error(f"[{bot.role_card.bot_name}] Privacy scan error: {e}")
        
        # Check license compliance
        if hasattr(bot, 'check_license_compliance'):
            try:
                license_issues = await bot.check_license_compliance()
                violations.extend([
                    {"type": "license", **v} for v in license_issues
                ])
            except Exception as e:
                logger.error(f"[{bot.role_card.bot_name}] License check error: {e}")
        
        # Categorize violations
        critical = [v for v in violations if v.get('severity') == 'critical']
        high = [v for v in violations if v.get('severity') == 'high']
        
        # Escalate critical violations
        if critical:
            if hasattr(bot, 'escalate_to_coordinator'):
                try:
                    await bot.escalate_to_coordinator(
                        f"CRITICAL: {len(critical)} compliance violations detected",
                        priority="critical",
                        data={
                            "critical_violations": critical[:10],
                            "total_violations": len(violations)
                        }
                    )
                    action = "escalated"
                except Exception as e:
                    logger.error(f"Failed to escalate: {e}")
                    action = "logged"
            else:
                action = "logged"
        elif high:
            if hasattr(bot, 'notify_coordinator'):
                try:
                    await bot.notify_coordinator(
                        f"{len(high)} high-severity compliance issues detected",
                        priority="high",
                        data={"high_issues": high[:10]}
                    )
                    action = "notified"
                except Exception as e:
                    logger.error(f"Failed to notify: {e}")
                    action = "logged"
            else:
                action = "logged"
        else:
            action = None
        
        return {
            "success": len(critical) == 0,
            "violations_found": len(violations),
            "critical": len(critical),
            "high": len(high),
            "medium_low": len(violations) - len(critical) - len(high),
            "action_taken": action,
            "violations": violations[:20] if violations else None
        }
        
    except Exception as e:
        logger.error(f"[{bot.role_card.bot_name}] Error in audit_compliance_status: {e}")
        return {
            "success": False,
            "error": str(e),
            "action_taken": "error"
        }


@register_check(
    name="review_audit_trail_integrity",
    description="Verify audit trail completeness and detect gaps",
    priority="high",
    max_duration_s=90.0,
    bot_domains=["quality"]
)
async def review_audit_trail_integrity(bot, config: Dict[str, Any]) -> Dict[str, Any]:
    """Review audit trails for completeness and detect suspicious gaps.
    
    Checks that all required audit events are logged, timestamps are
    sequential, and no unauthorized modifications occurred.
    
    Args:
        bot: The AuditorBot instance
        config: Check configuration
        
    Returns:
        Dict with audit trail integrity results
    """
    try:
        # Get audit check window
        lookback_hours = config.get("lookback_hours", 24)
        since = datetime.now() - timedelta(hours=lookback_hours)
        
        if hasattr(bot, 'review_audit_trail'):
            audit_result = await bot.review_audit_trail(since=since)
        else:
            return {
                "success": True,
                "message": "Audit trail review not available",
                "gaps_found": 0
            }
        
        gaps = getattr(audit_result, 'gaps', [])
        anomalies = getattr(audit_result, 'anomalies', [])
        
        # Analyze gaps
        critical_gaps = [g for g in gaps if g.get('severity') == 'critical']
        
        if critical_gaps or len(anomalies) > 5:
            if hasattr(bot, 'escalate_to_coordinator'):
                try:
                    await bot.escalate_to_coordinator(
                        f"Audit trail integrity issues: {len(critical_gaps)} critical gaps, {len(anomalies)} anomalies",
                        priority="critical",
                        data={
                            "critical_gaps": critical_gaps[:5],
                            "anomalies": anomalies[:10],
                            "lookback_hours": lookback_hours
                        }
                    )
                    action = "escalated"
                except Exception as e:
                    logger.error(f"Failed to escalate: {e}")
                    action = "logged"
            else:
                action = "logged"
        elif gaps:
            if hasattr(bot, 'notify_coordinator'):
                try:
                    await bot.notify_coordinator(
                        f"Audit trail has {len(gaps)} gaps in last {lookback_hours}h",
                        data={"gaps": gaps[:10]}
                    )
                    action = "notified"
                except Exception as e:
                    logger.error(f"Failed to notify: {e}")
                    action = "logged"
            else:
                action = "logged"
        else:
            action = None
        
        return {
            "success": len(critical_gaps) == 0 and len(anomalies) <= 5,
            "events_reviewed": getattr(audit_result, 'events_reviewed', 0),
            "gaps_found": len(gaps),
            "anomalies_detected": len(anomalies),
            "action_taken": action,
            "integrity_score": getattr(audit_result, 'integrity_score', 100)
        }
        
    except Exception as e:
        logger.error(f"[{bot.role_card.bot_name}] Error in review_audit_trail_integrity: {e}")
        return {
            "success": False,
            "error": str(e),
            "action_taken": "error"
        }


@register_check(
    name="check_pending_reviews",
    description="Check for pending code reviews and quality gates",
    priority="normal",
    max_duration_s=60.0,
    bot_domains=["quality"]
)
async def check_pending_reviews(bot, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check for pull requests and reviews requiring attention.
    
    Monitors review queues for PRs that need auditor review or have
    been waiting too long for quality gate approval.
    
    Args:
        bot: The AuditorBot instance
        config: Check configuration
        
    Returns:
        Dict with pending review status
    """
    try:
        max_wait_hours = config.get("max_wait_hours", 24)
        
        if hasattr(bot, 'get_pending_reviews'):
            pending = await bot.get_pending_reviews()
        else:
            pending = []
        
        # Categorize by urgency
        now = datetime.now()
        stale_reviews = []
        urgent_reviews = []
        
        for review in pending:
            created = getattr(review, 'created_at', now)
            if isinstance(created, str):
                try:
                    created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                except:
                    created = now
            
            hours_waiting = (now - created).total_seconds() / 3600
            
            review_data = {
                "id": getattr(review, 'id', 'unknown'),
                "title": getattr(review, 'title', 'Untitled'),
                "author": getattr(review, 'author', 'unknown'),
                "repository": getattr(review, 'repository', 'unknown'),
                "hours_waiting": round(hours_waiting, 1)
            }
            
            if hours_waiting > max_wait_hours * 2:
                stale_reviews.append(review_data)
            elif getattr(review, 'requires_qa', False) or hours_waiting > max_wait_hours:
                urgent_reviews.append(review_data)
        
        # Notify if items need attention
        if stale_reviews:
            if hasattr(bot, 'escalate_to_coordinator'):
                try:
                    await bot.escalate_to_coordinator(
                        f"{len(stale_reviews)} reviews stale (> {max_wait_hours * 2}h)",
                        priority="high",
                        data={"stale_reviews": stale_reviews[:10]}
                    )
                    action = "escalated"
                except Exception as e:
                    logger.error(f"Failed to escalate: {e}")
                    action = "logged"
            else:
                action = "logged"
        elif urgent_reviews:
            if hasattr(bot, 'notify_coordinator'):
                try:
                    await bot.notify_coordinator(
                        f"{len(urgent_reviews)} reviews need auditor attention",
                        data={"urgent_reviews": urgent_reviews[:10]}
                    )
                    action = "notified"
                except Exception as e:
                    logger.error(f"Failed to notify: {e}")
                    action = "logged"
            else:
                action = "logged"
        else:
            action = None
        
        return {
            "success": True,
            "total_pending": len(pending),
            "stale": len(stale_reviews),
            "urgent": len(urgent_reviews),
            "normal": len(pending) - len(stale_reviews) - len(urgent_reviews),
            "action_taken": action
        }
        
    except Exception as e:
        logger.error(f"[{bot.role_card.bot_name}] Error in check_pending_reviews: {e}")
        return {
            "success": False,
            "error": str(e),
            "action_taken": "error"
        }


__all__ = [
    "check_code_quality_scores",
    "audit_compliance_status",
    "review_audit_trail_integrity",
    "check_pending_reviews",
]