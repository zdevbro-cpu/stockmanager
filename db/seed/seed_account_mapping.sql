-- seed_account_mapping.sql
-- 예시 매핑입니다. 실제 DART 계정과목 표기는 회사/보고서마다 다를 수 있으므로 운영 중 보정이 필요합니다.

INSERT INTO account_mapping (statement_type, source_account_name, standard_key, priority) VALUES
('IS', '매출액', 'revenue', 10),
('IS', '영업이익', 'op_income', 10),
('IS', '당기순이익', 'net_income', 10),
('BS', '자산총계', 'assets', 10),
('BS', '부채총계', 'liabilities', 10),
('BS', '자본총계', 'equity', 10),
('CF', '영업활동현금흐름', 'op_cf', 10),
('CF', '투자활동현금흐름', 'inv_cf', 10),
('CF', '재무활동현금흐름', 'fin_cf', 10)
ON CONFLICT DO NOTHING;
