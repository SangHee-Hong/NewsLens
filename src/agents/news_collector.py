import os
import logging
from crewai import Agent, LLM
from src.tools.naver_search import naver_news_search

logger = logging.getLogger(__name__)


def _make_collector(domain: str) -> Agent:
    llm = LLM(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    return Agent(
        role=f"한국 {domain} 뉴스 화제성 분석 전문가",
        goal=(
            f"네이버 뉴스 API를 활용하여 {domain} 분야에서 오늘 가장 많은 언론사가 "
            "동시에 보도한 화제성 높은 주제 3개를 선별한다. "
            "단순 최신순이 아닌 '여러 언론사의 동시 보도 수'를 화제성 기준으로 삼는다."
        ),
        backstory=(
            "10년 경력의 미디어 분석 전문가로, 한국 주요 언론사의 보도 패턴을 깊이 이해한다. "
            "여러 키워드로 폭넓게 검색한 뒤, 같은 사건을 보도한 언론사 수를 기준으로 "
            "화제성을 측정하고 가장 주목받는 주제를 선별하는 데 특화되어 있다."
        ),
        tools=[naver_news_search],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_economy_collector_agent() -> Agent:
    logger.info("[NewsCollectorAgent] 경제 수집 Agent 생성")
    return _make_collector("경제")


def create_society_collector_agent() -> Agent:
    logger.info("[NewsCollectorAgent] 사회 수집 Agent 생성")
    return _make_collector("사회")


def create_tech_collector_agent() -> Agent:
    logger.info("[NewsCollectorAgent] 기술 수집 Agent 생성")
    return _make_collector("기술")
