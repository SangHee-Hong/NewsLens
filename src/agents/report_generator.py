import os
import logging
from crewai import Agent, LLM

logger = logging.getLogger(__name__)


def create_report_generator_agent() -> Agent:
    logger.info("[ReportGeneratorAgent] Agent 생성 시작")

    llm = LLM(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        max_tokens=10000,
    )

    agent = Agent(
        role="뉴스 분석 데이터 구조화 전문가",
        goal=(
            "요약 리포트와 검토 피드백을 바탕으로 뉴스 분석 결과를 "
            "정확하고 완전한 JSON 형태로 구조화하여 반환한다. "
            "HTML 생성은 하지 않으며 순수 데이터만 출력한다."
        ),
        backstory=(
            "데이터 엔지니어링 전문가로, 복잡한 뉴스 분석 결과를 "
            "구조화된 JSON 데이터로 변환하는 데 특화되어 있다. "
            "모든 필드를 빠짐없이 채우고, 반드시 유효한 JSON만 반환한다."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    logger.info("[ReportGeneratorAgent] Agent 생성 완료")
    return agent
