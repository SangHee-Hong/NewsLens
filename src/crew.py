import json
import logging
import os
import re
from datetime import datetime
from crewai import Crew, Process

from src.agents.news_collector import (
    create_economy_collector_agent,
    create_society_collector_agent,
    create_tech_collector_agent,
)
from src.agents.keyword_extractor import create_keyword_extractor_agent
from src.agents.source_finder import create_source_finder_agent
from src.agents.analyst import create_analyst_agent
from src.agents.summarizer import create_summarizer_agent
from src.agents.reviewer import create_reviewer_agent
from src.agents.report_generator import create_report_generator_agent
from src.report_template import render_html

from src.tasks.tasks import (
    create_collect_economy_task,
    create_collect_society_task,
    create_collect_tech_task,
    create_keyword_extraction_task,
    create_source_finding_task,
    create_analysis_task,
    create_summarize_task,
    create_review_task,
    create_report_generation_task,
)

logger = logging.getLogger(__name__)

REFLECTION_MAX_ITERATIONS = 2


class NewsAnalysisCrew:
    def __init__(self):
        logger.info("[Crew] NewsAnalysisCrew 초기화 시작")
        self._init_agents()
        logger.info("[Crew] NewsAnalysisCrew 초기화 완료")

    def _init_agents(self):
        # async_execution=True 병렬 실행 시 executor 충돌 방지 — 분야별 독립 인스턴스
        self.economy_collector = create_economy_collector_agent()
        self.society_collector = create_society_collector_agent()
        self.tech_collector = create_tech_collector_agent()
        self.keyword_extractor = create_keyword_extractor_agent()
        self.source_finder = create_source_finder_agent()
        self.analyst = create_analyst_agent()
        self.summarizer = create_summarizer_agent()
        self.reviewer = create_reviewer_agent()
        self.report_generator = create_report_generator_agent()

    # ── Phase 1: 뉴스 수집 + 키워드 + 언론사 탐색 + 분석 ──────────────────────
    def _run_phase1(self, generation_date: str) -> tuple:
        """Parallelization + Prompt Chaining으로 데이터 수집 및 분석 실행."""
        logger.info("[Crew] Phase 1 시작 — 뉴스 수집(병렬) → 키워드 → 탐색 → 분석")

        # 분야별 독립 인스턴스를 1:1 매핑 — 동일 executor 동시 호출 방지
        collect_eco = create_collect_economy_task(self.economy_collector, generation_date)
        collect_soc = create_collect_society_task(self.society_collector, generation_date)
        collect_tech = create_collect_tech_task(self.tech_collector, generation_date)

        keyword_task = create_keyword_extraction_task(
            self.keyword_extractor,
            context_tasks=[collect_eco, collect_soc, collect_tech],
        )
        source_task = create_source_finding_task(
            self.source_finder,
            context_tasks=[keyword_task, collect_eco, collect_soc, collect_tech],
        )
        analysis_task = create_analysis_task(
            self.analyst,
            context_tasks=[collect_eco, collect_soc, collect_tech, source_task],
        )

        crew = Crew(
            agents=[
                self.economy_collector,
                self.society_collector,
                self.tech_collector,
                self.keyword_extractor,
                self.source_finder,
                self.analyst,
            ],
            tasks=[
                collect_eco,
                collect_soc,
                collect_tech,
                keyword_task,
                source_task,
                analysis_task,
            ],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()
        logger.info("[Crew] Phase 1 완료")

        # 이후 phase에서 context로 활용할 task 반환 (source_task 포함 — 링크 보존)
        return analysis_task, keyword_task, collect_eco, collect_soc, collect_tech, source_task

    # ── Phase 2: 요약 + 검토 (Reflection 루프) ─────────────────────────────────
    def _run_phase2_with_reflection(self, phase1_tasks: tuple) -> tuple:
        """Reflection 패턴: ReviewerAgent 피드백으로 최대 3회 재작성."""
        analysis_task, keyword_task, collect_eco, collect_soc, collect_tech, source_task = phase1_tasks

        reviewer_feedback: str | None = None
        summarize_task = None
        review_task = None

        for iteration in range(1, REFLECTION_MAX_ITERATIONS + 1):
            logger.info(f"[Crew] Phase 2 — Reflection 반복 {iteration}/{REFLECTION_MAX_ITERATIONS}")

            summarize_task = create_summarize_task(
                self.summarizer,
                context_tasks=[analysis_task, keyword_task, source_task, collect_eco, collect_soc, collect_tech],
                reviewer_feedback=reviewer_feedback,
            )
            review_task = create_review_task(
                self.reviewer,
                context_tasks=[summarize_task],
            )

            crew = Crew(
                agents=[self.summarizer, self.reviewer],
                tasks=[summarize_task, review_task],
                process=Process.sequential,
                verbose=True,
            )
            crew.kickoff()

            review_output = str(review_task.output.raw if review_task.output else "")
            logger.info(f"[Crew] Reviewer 판정 결과 (반복 {iteration}):\n{review_output[:300]}")

            if "REVISION_NEEDED" not in review_output:
                logger.info(f"[Crew] Phase 2 — APPROVED (반복 {iteration}회 만에 승인)")
                break

            reviewer_feedback = review_output
            logger.info(f"[Crew] Phase 2 — REVISION_NEEDED, 피드백 반영하여 재작성 예정")

            if iteration == REFLECTION_MAX_ITERATIONS:
                logger.warning("[Crew] Phase 2 — 최대 반복 횟수 도달, 마지막 결과로 진행")

        return summarize_task, review_task, source_task

    # ── Phase 3: 데이터 구조화 → Python에서 HTML 조립 ──────────────────────────
    def _run_phase3(
        self,
        summarize_task,
        review_task,
        source_task,
        generation_date: str,
    ) -> str:
        """LLM은 JSON 데이터만 반환, HTML 조립은 Python 템플릿으로 처리."""
        logger.info("[Crew] Phase 3 시작 — 리포트 데이터 구조화")

        report_task = create_report_generation_task(
            self.report_generator,
            context_tasks=[summarize_task, review_task, source_task],
            generation_date=generation_date,
        )

        crew = Crew(
            agents=[self.report_generator],
            tasks=[report_task],
            process=Process.sequential,
            verbose=True,
        )
        crew.kickoff()

        raw = str(report_task.output.raw if report_task.output else "{}")
        data = self._parse_json_output(raw)

        # 검토 결과 추출
        review_raw = str(review_task.output.raw if review_task.output else "")
        review_score, review_verdict = self._extract_review_meta(review_raw)

        html = render_html(data, generation_date, review_score, review_verdict)
        logger.info("[Crew] Phase 3 완료 — Python 템플릿으로 HTML 조립 완료")
        return html

    def _parse_json_output(self, raw: str) -> dict:
        """LLM 출력에서 JSON 추출 — 마크다운 코드블록 제거 후 파싱."""
        # ```json ... ``` 또는 ``` ... ``` 블록 제거
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # 중괄호 블록만 추출 재시도
            match = re.search(r"\{[\s\S]+\}", cleaned)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        logger.warning("[Crew] JSON 파싱 실패 — 빈 데이터로 대체")
        return {}

    def _extract_review_meta(self, review_raw: str) -> tuple[str, str]:
        """Reviewer 출력에서 총점과 판정 추출."""
        verdict = "APPROVED" if "APPROVED" in review_raw else "REVISION_NEEDED"
        score_match = re.search(r"(\d+)\s*/\s*50", review_raw)
        score = f"{score_match.group(1)}/50" if score_match else ""
        return score, verdict

    # ── 공개 진입점 ────────────────────────────────────────────────────────────
    def run(self) -> str:
        """전체 파이프라인 실행 후 HTML 리포트 문자열 반환."""
        generation_date = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
        logger.info(f"[Crew] 전체 파이프라인 시작 — 생성 시각: {generation_date}")

        phase1_tasks = self._run_phase1(generation_date)
        summarize_task, review_task, source_task = self._run_phase2_with_reflection(phase1_tasks)
        html_report = self._run_phase3(summarize_task, review_task, source_task, generation_date)

        logger.info("[Crew] 전체 파이프라인 완료")
        return html_report
