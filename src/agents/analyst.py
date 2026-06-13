import os
import logging
from crewai import Agent, LLM

logger = logging.getLogger(__name__)


def create_analyst_agent() -> Agent:
    logger.info("[AnalystAgent] Agent 생성 시작")

    llm = LLM(
        model="anthropic/claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=6000,
    )

    agent = Agent(
        role="뉴스 비교 분석 전문가",
        goal=(
            "서로 다른 언론사 2곳의 기사를 심층 비교 분석하여 "
            "각 언론사의 관점 차이, 강조점, 프레이밍 방식을 명확하게 파악하고 "
            "객관적인 비교 분석 결과를 제공한다."
        ),
        backstory=(
            "20년 경력의 미디어 비평 전문가이자 저널리즘 연구자로, "
            "한국 언론의 보도 패턴과 정치·경제적 편향성을 체계적으로 분석해왔다. "
            "같은 사건에 대한 다양한 보도 방식을 비교하여 "
            "독자들이 균형 잡힌 시각을 가질 수 있도록 돕는다."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    logger.info("[AnalystAgent] Agent 생성 완료")
    return agent
