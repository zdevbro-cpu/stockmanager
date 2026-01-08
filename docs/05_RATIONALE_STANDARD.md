# 05_RATIONALE_STANDARD (추천/신호 근거 JSON 표준)

## 1. 목적
- 추천(점수/랭크/비중)과 타이밍 신호의 **근거를 표준 JSON으로 저장**하여,
  분석보기 UI/리포트 생성/감사 추적에 공통으로 사용한다.

## 2. 추천 rationale (recommendation.rationale) 권장 스키마(요약)
```json
{
  "as_of_date": "2026-01-08",
  "classifications": {
    "industry": {
      "taxonomy": "KIS_INDUSTRY",
      "primary": {"code":"...", "name":"...", "level":1},
      "path": [{"code":"...","name":"...","level":1}, {"code":"...","name":"...","level":2}]
    },
    "themes": [{"id":"theme_ai","name":"AI"}, {"id":"theme_battery","name":"2차전지"}]
  },
  "filters": {
    "passed": true,
    "rules": [{"name":"min_turnover_20d", "passed": true, "value": 1200000000, "threshold": 500000000}]
  },
  "factors": {
    "total_score": 0.85,
    "contrib": [
      {"factor":"momentum", "value":0.72, "weight":0.35, "contribution":0.252},
      {"factor":"trend", "value":0.60, "weight":0.25, "contribution":0.150},
      {"factor":"risk_penalty", "value":0.40, "weight":-0.25, "contribution":-0.100}
    ]
  },
  "portfolio": {
    "target_weight": 0.10,
    "constraints": [
      {"name":"max_weight_per_name", "passed": true, "limit":0.10},
      {"name":"max_weight_per_sector", "passed": true, "limit":0.25, "sector_taxonomy":"KIS_INDUSTRY", "sector_level":1}
    ]
  },
  "event_risk": {
    "window_days": 2,
    "policy": "block_entry",
    "flags": []
  }
}
```

## 3. 신호 rationale (timing_signal.triggers/risk_flags) 권장
- `triggers`: 어떤 룰이 발화했는지(룰명/임계값/관측값)
- `risk_flags`: 이벤트 리스크/변동성 급등/유동성 급감 등 경고
