import logging
from crewai import Task, Agent
from typing import List, Optional

logger = logging.getLogger(__name__)


_COLLECT_INSTRUCTIONS = """\
검색 절차 (순서대로 실행):
1단계 - 다중 검색: 아래 키워드 중 2~3개로 각각 검색하여 결과를 모은다.
2단계 - 주제 클러스터링: 수집된 기사들을 '같은 사건/이슈'를 다루는 그룹으로 묶는다.
        → 여러 언론사가 동시에 보도할수록 화제성이 높다.
3단계 - 화제성 TOP 3 선정: 보도한 언론사 수가 많은 순서대로 주제 3개를 선정한다.
4단계 - 대표 기사 선택: 각 주제에서 가장 정보가 풍부한 기사 1건을 대표로 선택한다.

【필수】 단순 최신순이 아닌 '여러 언론사가 동시 보도한 주제'를 화제성 기준으로 삼아야 한다.\
"""

_COLLECT_OUTPUT = """\
화제성 TOP 3 주제 목록 (1위가 가장 많은 언론사가 보도):

=== 주제 1 (가장 화제, 언론사 N곳 보도) ===
주제: [주제를 한 문장으로 설명]
보도 언론사: [언론사1, 언론사2, ...]
대표기사 제목: ...
날짜: ...
언론사: ...
요약: ... (2-3문장)
링크: ...

=== 주제 2 (언론사 N곳 보도) ===
주제: ...
보도 언론사: ...
대표기사 제목: ...
날짜: ...
언론사: ...
요약: ...
링크: ...

=== 주제 3 (언론사 N곳 보도) ===
(동일 형식)\
"""


def create_collect_economy_task(agent: Agent, generation_date: str) -> Task:
    logger.info("[Task] 경제 뉴스 수집 Task 생성")
    return Task(
        description=(
            f"오늘({generation_date}) 네이버 뉴스 API를 사용하여 한국에서 가장 화제인 경제 분야 주제 3개를 선정하라.\n\n"
            f"{_COLLECT_INSTRUCTIONS}\n\n"
            "검색 키워드 후보: '한국 경제', '코스피', '금리', '환율', '기업 실적', '무역수지'"
        ),
        expected_output=_COLLECT_OUTPUT,
        agent=agent,
        async_execution=True,  # Parallelization: 3개 분야 동시 수집
    )


def create_collect_society_task(agent: Agent, generation_date: str) -> Task:
    logger.info("[Task] 사회 뉴스 수집 Task 생성")
    return Task(
        description=(
            f"오늘({generation_date}) 네이버 뉴스 API를 사용하여 한국에서 가장 화제인 사회 분야 주제 3개를 선정하라.\n\n"
            f"{_COLLECT_INSTRUCTIONS}\n\n"
            "검색 키워드 후보: '한국 사회', '정치', '선거', '복지', '교육', '노동', '범죄'"
        ),
        expected_output=_COLLECT_OUTPUT,
        agent=agent,
        async_execution=True,  # Parallelization
    )


def create_collect_tech_task(agent: Agent, generation_date: str) -> Task:
    logger.info("[Task] 기술 뉴스 수집 Task 생성")
    return Task(
        description=(
            f"오늘({generation_date}) 네이버 뉴스 API를 사용하여 한국에서 가장 화제인 기술 분야 주제 3개를 선정하라.\n\n"
            f"{_COLLECT_INSTRUCTIONS}\n\n"
            "검색 키워드 후보: 'AI 인공지능', '반도체', '삼성 SK하이닉스', '스타트업', '빅테크'"
        ),
        expected_output=_COLLECT_OUTPUT,
        agent=agent,
        async_execution=True,  # Parallelization
    )


def create_keyword_extraction_task(
    agent: Agent,
    context_tasks: List[Task],
) -> Task:
    logger.info("[Task] 키워드 추출 Task 생성")
    return Task(
        description=(
            "이전 단계에서 수집된 경제/사회/기술 분야 뉴스 9건에서 핵심 키워드를 추출하라.\n\n"
            "추출 기준:\n"
            "- 각 뉴스 기사당 핵심 키워드 3-5개 추출\n"
            "- 분야별(경제/사회/기술)로 공통 키워드도 식별\n"
            "- 고유명사(기업명, 인물명, 정책명 등) 포함\n\n"
            "출력 형식: 분야별로 구분하여 키워드 목록을 JSON 형태로 정리."
        ),
        expected_output=(
            "분야별 키워드 목록 (JSON 형식):\n"
            "{\n"
            '  "경제": ["키워드1", "키워드2", ...],\n'
            '  "사회": ["키워드1", "키워드2", ...],\n'
            '  "기술": ["키워드1", "키워드2", ...],\n'
            '  "공통": ["키워드1", "키워드2", ...]\n'
            "}"
        ),
        agent=agent,
        context=context_tasks,
    )


def create_source_finding_task(
    agent: Agent,
    context_tasks: List[Task],
) -> Task:
    logger.info("[Task] 언론사 탐색 Task 생성")
    return Task(
        description=(
            "수집된 뉴스와 키워드를 활용하여, 각 분야(경제/사회/기술)에서 "
            "여러 언론사가 동시에 보도했을 특정 뉴스 사건 1건을 선정하고, "
            "그 사건에 대해 서로 다른 시각으로 보도한 언론사 2곳의 기사를 찾아라.\n\n"
            "【필수 제약】 두 기사는 반드시 동일한 하나의 사건/발표/사고를 다루어야 한다.\n"
            "테마나 주제가 같더라도 서로 다른 사건을 다루는 기사 쌍은 사용 금지.\n\n"
            "검색 3단계:\n"
            "1단계 - 사건 선정: 수집된 뉴스 중 여러 언론사가 동시에 보도했을 가능성이 높은 "
            "구체적 사건을 1개 선정 (예: '지방선거 투표용지 부족', 'OO 기업 실적 발표', 'OO 정책 발표')\n"
            "2단계 - 동시 보도 검색: 그 사건의 핵심 키워드로 네이버 뉴스 검색 "
            "(예: '투표용지 부족 지방선거' 또는 '삼성 2분기 실적')\n"
            "3단계 - 언론사 선택: 검색 결과에서 동일 사건을 다루는 서로 다른 논조의 언론사 2곳 기사 선택\n\n"
            "동일 사건 검증: 두 기사의 제목과 날짜를 비교하여 같은 사건인지 확인하라.\n"
            "다른 사건이면 2단계부터 다시 시작하여 더 구체적인 키워드로 재검색하라.\n\n"
            "언론사 선별 기준:\n"
            "- 서로 다른 논조 (예: 진보vs보수, 경제지vs종합지)\n"
            "- 대형 언론사 우선 (조선일보, 한겨레, 경향신문, 중앙일보, 매일경제, 한국경제 등)"
        ),
        expected_output=(
            "분야별 언론사 비교 데이터:\n"
            "각 분야당:\n"
            "- 선정된 구체적 사건 제목 (같은 사건임을 확인한 근거 1문장 포함)\n"
            "- 언론사A: 이름, 기사 제목, 주요 논점, 링크\n"
            "- 언론사B: 이름, 기사 제목, 주요 논점, 링크\n"
            "- 동일 사건 여부: '예 — 두 기사 모두 [사건명]을 다룸'"
        ),
        agent=agent,
        context=context_tasks,
    )


def create_analysis_task(
    agent: Agent,
    context_tasks: List[Task],
) -> Task:
    logger.info("[Task] 비교 분석 Task 생성")
    return Task(
        description=(
            "언론사 탐색 결과를 바탕으로 각 분야(경제/사회/기술)별 두 언론사의 보도를 심층 비교 분석하라.\n\n"
            "【사전 검증 — 분석 시작 전 필수】\n"
            "두 기사가 날짜·제목·내용 기준으로 동일한 특정 사건을 다루는지 확인하라.\n"
            "동일 사건이 아니라면 해당 분야의 언론사 비교를 건너뛰고 "
            "'동일 사건 기사 쌍 없음'으로 표기하라. 억지로 다른 사건을 비교하지 않는다.\n\n"
            "동일 사건 확인 후 다음 3개 항목만 분석하라. 【각 항목 3문장 이내로 간결하게 작성】\n"
            "1. 프레이밍 차이: 같은 사건을 어떤 관점에서 보도하는가\n"
            "2. 강조점 차이: 어떤 측면을 부각하고 어떤 측면을 축소하는가\n"
            "3. 종합 평가: 두 보도의 차이가 갖는 사회적 함의"
        ),
        expected_output=(
            "분야별 비교 분석 결과 (경제/사회/기술 각각):\n"
            "- 이슈 개요 (1문장)\n"
            "- 언론사A vs 언론사B 프레이밍 차이 (3문장 이내)\n"
            "- 강조점 차이 (3문장 이내)\n"
            "- 종합 평가 (3문장 이내)"
        ),
        agent=agent,
        context=context_tasks,
    )


def create_summarize_task(
    agent: Agent,
    context_tasks: List[Task],
    reviewer_feedback: Optional[str] = None,
) -> Task:
    logger.info("[Task] 요약 리포트 Task 생성")

    feedback_section = ""
    if reviewer_feedback:
        feedback_section = (
            f"\n\n[검토관 피드백 - 반드시 반영할 것]\n{reviewer_feedback}\n"
            "위 피드백을 모두 반영하여 개선된 요약 리포트를 작성하라."
        )

    return Task(
        description=(
            "모든 수집·분석 결과를 종합하여 구조화된 뉴스 분석 요약 리포트를 작성하라.\n\n"
            "리포트 구성:\n"
            "1. 오늘의 주요 뉴스 개요 (전체 한 단락)\n"
            "2. 경제 분야: 주요 뉴스 3건 요약 + 언론사 비교 분석 요약\n"
            "3. 사회 분야: 주요 뉴스 3건 요약 + 언론사 비교 분석 요약\n"
            "4. 기술 분야: 주요 뉴스 3건 요약 + 언론사 비교 분석 요약\n"
            "5. 종합 인사이트: 오늘의 핵심 트렌드와 주목할 점\n\n"
            "요구사항:\n"
            "- 각 분야 키워드 태그 포함\n"
            "- 언론사 간 시각 차이를 중립적으로 서술\n"
            "- 한국어로 작성, 전문적이되 일반인도 이해 가능한 수준\n"
            "- 【분량 기준 엄수】 뉴스 요약 기사당 2문장, 섹션 개요 2문장, 비교 분석 요약 3문장 이내"
            + feedback_section
        ),
        expected_output=(
            "완성된 뉴스 분석 요약 리포트 (마크다운 형식):\n"
            "# 오늘의 뉴스 분석 리포트\n"
            "## 개요\n## 경제\n## 사회\n## 기술\n## 종합 인사이트\n"
            "각 섹션에 키워드 태그 및 언론사 비교 포함."
        ),
        agent=agent,
        context=context_tasks,
    )


def create_review_task(
    agent: Agent,
    context_tasks: List[Task],
) -> Task:
    logger.info("[Task] 품질 검토 Task 생성")
    return Task(
        description=(
            "SummarizerAgent가 작성한 요약 리포트를 다음 기준으로 품질을 검토하라.\n\n"
            "평가 기준 (각 10점):\n"
            "1. 완성도: 경제/사회/기술 3개 분야가 모두 커버되었는가\n"
            "2. 정확성: 수집된 뉴스 내용을 정확히 반영하였는가\n"
            "3. 균형성: 두 언론사의 시각을 균형 있게 제시하였는가\n"
            "4. 가독성: 구조화되어 읽기 쉬운가\n"
            "5. 인사이트: 의미 있는 분석과 종합 인사이트가 포함되었는가\n\n"
            "판정 기준:\n"
            "- 총점 40점 이상: APPROVED\n"
            "- 총점 40점 미만: REVISION_NEEDED\n\n"
            "출력 형식:\n"
            "판정: APPROVED 또는 REVISION_NEEDED\n"
            "총점: X/50\n"
            "항목별 점수: 완성도(X), 정확성(X), 균형성(X), 가독성(X), 인사이트(X)\n"
            "피드백: [구체적인 개선사항 또는 칭찬]"
        ),
        expected_output=(
            "품질 검토 결과:\n"
            "- 판정: APPROVED 또는 REVISION_NEEDED\n"
            "- 총점 및 항목별 점수\n"
            "- 구체적인 피드백 (REVISION_NEEDED 시 개선 요구사항 상세 기술)"
        ),
        agent=agent,
        context=context_tasks,
    )


def create_report_generation_task(
    agent: Agent,
    context_tasks: List[Task],
    generation_date: str,
) -> Task:
    logger.info("[Task] 리포트 데이터 구조화 Task 생성")
    return Task(
        description=(
            "요약 리포트와 검토 결과를 바탕으로 뉴스 분석 데이터를 아래 JSON 스키마에 맞게 구조화하라.\n"
            "HTML은 생성하지 않는다. 순수 JSON만 반환한다.\n\n"
            f"리포트 생성 일시: {generation_date}\n\n"
            "반환 스키마 (반드시 이 구조를 지킬 것):\n"
            "{\n"
            '  "overview": "오늘의 뉴스 전체 개요 (2-3문장)",\n'
            '  "economy": {\n'
            '    "topics": [\n'
            '      {\n'
            '        "topic": "주제를 한 문장으로 설명",\n'
            '        "outlet_count": 6,\n'
            '        "title": "대표기사 제목", "date": "날짜", "publisher": "언론사",\n'
            '        "summary": "2-3문장 요약", "originallink": "원문URL", "link": "네이버URL"\n'
            '      },\n'
            '      ... (3건, outlet_count 내림차순)\n'
            '    ],\n'
            '    "keywords": ["키워드1", "키워드2", "키워드3"],\n'
            '    "comparison": {\n'
            '      "issue": "비교 이슈 제목 (topics[0].topic과 동일한 가장 화제인 주제)",\n'
            '      "source_a": {"name": "언론사명", "title": "기사 제목", "link": "기사원문URL", "perspective": "관점 요약"},\n'
            '      "source_b": {"name": "언론사명", "title": "기사 제목", "link": "기사원문URL", "perspective": "관점 요약"},\n'
            '      "analysis": "두 언론사 비교 분석 (3-4문장)"\n'
            '    }\n'
            '  },\n'
            '  "society": { /* economy와 동일한 구조 */ },\n'
            '  "tech": { /* economy와 동일한 구조 */ },\n'
            '  "insights": "종합 인사이트 (3-5문장)"\n'
            "}\n\n"
            "주의사항:\n"
            "- 모든 분야(economy, society, tech)를 빠짐없이 채울 것\n"
            "- topics 배열은 반드시 3건, outlet_count 내림차순 정렬\n"
            "- comparison.issue는 topics[0](가장 화제인 주제)와 동일한 주제여야 함\n"
            "- originallink/link 필드에는 이전 단계 결과의 '링크:' URL을 그대로 복사할 것\n"
            "- URL은 절대 생략하거나 임의로 만들지 말 것\n"
            "- 마크다운 코드블록(```) 없이 JSON만 출력\n"
            "- 한국어로 작성"
        ),
        expected_output=(
            "```json 없이 순수 JSON 텍스트만 출력.\n"
            "overview, economy, society, tech, insights 키를 모두 포함한 유효한 JSON."
        ),
        agent=agent,
        context=context_tasks,
    )
