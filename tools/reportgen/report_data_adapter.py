# tools/reportgen/report_data_adapter.py

from __future__ import annotations

from typing import Dict, Iterable, Optional


def build_report_data(
    source: str,
    project_id: str,
    asof: str,
    template_tokens: Optional[Iterable[str]] = None,
) -> Dict[str, str]:
    if source != "system":
        raise ValueError(f"Unsupported source: {source}")

    summary = get_project_summary(project_id)
    financial = get_financial_analysis(project_id, asof)
    risks = get_risks(project_id)
    opportunities = get_opportunities(project_id)
    monitoring_points = get_monitoring_points(project_id)
    news = get_news_insights(project_id)
    final_opinion = get_final_opinion(project_id, asof)

    return {
        "author": summary["author"],
        "business_model_and_issues": summary["business_model_and_issues"],
        "company_name": summary["company_name"],
        "date": asof,
        "executive_summary": summary["executive_summary"],
        "final_opinion": final_opinion,
        "financial_analysis": financial,
        "monitoring_points": monitoring_points,
        "news_insights": news,
        "opportunities": opportunities,
        "report_title": summary["report_title"],
        "risks": risks,
    }


def get_project_summary(project_id: str) -> Dict[str, str]:
    # TODO: Replace with DB/API call for project metadata and summary text.
    return {
        "author": "System Stub",
        "business_model_and_issues": f"[stub] Business model overview for {project_id}.",
        "company_name": f"[stub] Company for {project_id}",
        "executive_summary": f"[stub] Executive summary for {project_id}.",
        "report_title": f"[stub] Project Report - {project_id}",
    }


def get_financial_analysis(project_id: str, asof: str) -> str:
    # TODO: Replace with DB/API call for financial analysis as of the given date.
    return f"[stub] Financial analysis for {project_id} as of {asof}."


def get_risks(project_id: str) -> str:
    # TODO: Replace with DB/API call for project risks.
    return f"[stub] Key risks for {project_id}."


def get_opportunities(project_id: str) -> str:
    # TODO: Replace with DB/API call for project opportunities.
    return f"[stub] Key opportunities for {project_id}."


def get_monitoring_points(project_id: str) -> str:
    # TODO: Replace with DB/API call for monitoring points.
    return f"[stub] Monitoring points for {project_id}."


def get_news_insights(project_id: str) -> str:
    # TODO: Replace with DB/API call for news insights.
    return f"[stub] News insights for {project_id}."


def get_final_opinion(project_id: str, asof: str) -> str:
    # TODO: Replace with DB/API call for final opinion/decisioning.
    return f"[stub] Final opinion for {project_id} as of {asof}."
