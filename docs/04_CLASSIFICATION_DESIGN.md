# 04_CLASSIFICATION_DESIGN (산업/테마 분류 설계안)

## 1. 목적
- 종목 추천/필터링/리스크제약/설명가능성(분석보기)을 위해 **산업(Industry)** 과 **테마(Theme)** 분류를 설계에 포함한다.
- 산업은 “안정적 트리(대/중/소 등)”, 테마는 “동적 태그(M:N)”로 구분하여 혼선을 방지한다.

## 2. 분류 정의
### 2.1 산업(Industry / Sector)
- 기준: **KIS 분류 체계**(권장: Primary Taxonomy)
- 구조: 트리(상위/하위) + 종목의 *주산업(primary)* 지정 가능
- 활용:
  - 유니버스 포함/제외 필터
  - 포트폴리오 제약(산업 편중 제한: max_weight_per_sector)
  - 분석보기 표기(기업의 본질적 사업영역)

### 2.2 테마(Theme)
- 기준: 내부 정의(초기에는 수기/업로드로도 시작 가능) + 추후 확장(외부/자체 추출)
- 구조: 태그(다대다 M:N). 종목은 여러 테마에 속할 수 있음
- 활용:
  - 관심 테마 기반 후보군 탐색/필터
  - 단기 모멘텀/이슈 기반 설명 보조
  - VC 리포트에서 “투자 논리/모멘텀” 보강

## 3. 데이터 모델(권장)
### 3.1 Taxonomy(분류 체계)
- 예: `KIS_INDUSTRY`, `THEME`

### 3.2 Node(분류 노드)
- 산업: code, name, level, parent_code 로 트리 구성
- 테마: code(또는 slug), name, parent는 optional(필요 시)

### 3.3 Mapping(종목 ↔ 분류 매핑)
- 종목과 분류의 관계를 M:N로 관리
- `is_primary`로 “주산업” 표시(산업에만 사용 권장)
- `effective_from/effective_to`로 변경 이력 관리(실전/백테스트 PIT에 도움)

## 4. 전략/유니버스 필터에 반영(권장 파라미터)
- include_industry_codes / exclude_industry_codes (taxonomy=KIS_INDUSTRY)
- include_theme_ids / exclude_theme_ids (taxonomy=THEME)
- portfolio.constraints:
  - max_weight_per_sector (기존)
  - sector_taxonomy: "KIS_INDUSTRY" (추가)
  - sector_level: 1|2|3 (추가)  # 대/중/소 등

## 5. 분석보기(Explainability) 표준 필드(권장)
- `classifications.industry`:
  - taxonomy: "KIS_INDUSTRY"
  - primary: {code, name, level}
  - path: [{code,name,level}, ...]  # 상위→하위
- `classifications.themes`: [{id, name}, ...]

## 6. 단계적 도입 권장(실전투자 v1 기준)
- v1(즉시): **산업(KIS) 필터 + 산업 편중 제한 + 분석보기 표기**까지 포함
- v1.1: 테마 엔티티/매핑 구조 추가(수기/업로드로 시작)
- v2: 테마 소스 확정(외부/자체 추출) + 테마 기반 전략/리포트 강화
