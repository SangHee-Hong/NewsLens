import os
import logging
from crewai import Agent, LLM

logger = logging.getLogger(__name__)


def create_keyword_extractor_agent() -> Agent:
    logger.info("[KeywordExtractorAgent] Agent 생성 시작")

    llm = LLM(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    agent = Agent(
        role="뉴스 키워드 추출 전문가",
        goal=(
            "수집된 뉴스 기사에서 각 분야별 핵심 키워드를 정확하게 추출하여 "
            "후속 분석에 활용 가능한 구조화된 키워드 목록을 제공한다."
        ),
        backstory=(
            "자연어처리 및 텍스트 마이닝 전문가로, 뉴스 기사의 핵심 주제와 "
            "트렌드를 반영하는 키워드를 선별하는 데 탁월한 능력을 갖추고 있다. "
            "한국어 뉴스의 문맥과 용어를 정확히 이해하여 의미 있는 키워드를 도출한다."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    logger.info("[KeywordExtractorAgent] Agent 생성 완료")
    return agent
