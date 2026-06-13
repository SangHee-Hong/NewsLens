import os
import logging
from crewai import Agent, LLM
from src.tools.naver_search import naver_news_search

logger = logging.getLogger(__name__)


def create_source_finder_agent() -> Agent:
    logger.info("[SourceFinderAgent] Agent 생성 시작")

    llm = LLM(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    agent = Agent(
        role="언론사 탐색 전문가",
        goal=(
            "추출된 키워드와 수집된 뉴스를 기반으로, 동일한 하나의 뉴스 사건에 대해 "
            "서로 다른 시각으로 보도한 언론사 2곳의 기사를 찾는다. "
            "테마가 같더라도 서로 다른 사건을 다루는 기사 쌍은 절대 사용하지 않는다. "
            "진보/보수, 경제지/종합지 등 상반된 논조의 언론사를 선별한다."
        ),
        backstory=(
            "한국 미디어 생태계 전문가로, 각 언론사의 논조와 편향성을 깊이 이해한다. "
            "핵심 원칙: 동일한 뉴스 사건을 두 언론사가 각각 어떻게 다르게 프레이밍하는지 비교해야 한다. "
            "서로 다른 사건을 비교하면 비교 분석이 무의미해진다는 것을 잘 알기에, "
            "반드시 같은 사건에 대한 기사 쌍만 선택한다."
        ),
        tools=[naver_news_search],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    logger.info("[SourceFinderAgent] Agent 생성 완료")
    return agent
