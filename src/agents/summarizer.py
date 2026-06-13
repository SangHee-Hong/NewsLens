import os
import logging
from crewai import Agent, LLM

logger = logging.getLogger(__name__)


def create_summarizer_agent() -> Agent:
    logger.info("[SummarizerAgent] Agent 생성 시작")

    llm = LLM(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        max_tokens=4000,
    )

    agent = Agent(
        role="뉴스 분석 리포트 요약 전문가",
        goal=(
            "수집·분석된 전체 뉴스 데이터를 종합하여 경제/사회/기술 분야별로 "
            "구조화된 요약 리포트를 작성한다. "
            "핵심 트렌드, 주요 이슈, 언론사 간 시각 차이를 명확히 정리한다."
        ),
        backstory=(
            "뉴스 에디터 및 데이터 저널리즘 전문가로, 방대한 뉴스 데이터를 "
            "핵심만 추려 독자가 이해하기 쉬운 구조화된 리포트로 변환하는 데 뛰어나다. "
            "복잡한 정보를 명확하고 간결하게 전달하는 능력을 갖추고 있다."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    logger.info("[SummarizerAgent] Agent 생성 완료")
    return agent
