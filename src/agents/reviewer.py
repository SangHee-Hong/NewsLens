import os
import logging
from crewai import Agent, LLM

logger = logging.getLogger(__name__)


def create_reviewer_agent() -> Agent:
    logger.info("[ReviewerAgent] Agent 생성 시작")

    # 독립적 평가를 위해 다른 회사(OpenAI) 모델 사용 — 객관성 확보
    llm = LLM(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    agent = Agent(
        role="뉴스 분석 리포트 품질 검토관",
        goal=(
            "SummarizerAgent가 작성한 요약 리포트의 품질을 독립적으로 평가하고, "
            "미흡한 부분을 구체적으로 지적하여 개선을 요청하거나 최종 승인한다. "
            "평가 기준: 완성도, 정확성, 균형성, 가독성, 분야별 커버리지."
        ),
        backstory=(
            "뉴스 미디어 품질 관리 전문가로, 다양한 언론사의 에디터로 근무한 경험을 바탕으로 "
            "뉴스 리포트의 품질을 객관적으로 평가한다. "
            "SummarizerAgent와 독립적인 판단 기준을 적용하여 편향 없는 품질 검토를 수행한다."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    logger.info("[ReviewerAgent] Agent 생성 완료")
    return agent
