import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# 환경변수 로드 (.env 우선)
load_dotenv(override=True)  # 시스템 환경변수보다 .env 우선

# ── 디렉터리 준비 ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ── 로거 설정 ──────────────────────────────────────────────────────────────────
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> logging.Logger:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # 파일 핸들러
    file_handler = logging.FileHandler(LOGS_DIR / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 외부 라이브러리 로그 수준 조정
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)

    return logging.getLogger("main")


def validate_env() -> bool:
    required = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        print(f"[ERROR] 필수 환경변수가 설정되지 않았습니다: {', '.join(missing)}")
        print("  .env.example을 참고하여 .env 파일을 생성하세요.")
        return False
    return True


def save_html_report(html_content: str) -> None:
    output_path = OUTPUT_DIR / "report.html"
    try:
        output_path.write_text(html_content, encoding="utf-8")
        resolved = output_path.resolve()
        print(f"\n[완료] HTML 리포트가 저장되었습니다: {resolved}")
        os.startfile(str(resolved))
        print("[완료] 브라우저에서 리포트를 열었습니다.")
    except OSError as e:
        print(f"[경고] HTML 파일 저장 실패: {e}")
        print("[Fallback] HTML 내용을 콘솔에 출력합니다:\n")
        print(html_content)


def main():
    logger = setup_logging()

    logger.info("=" * 60)
    logger.info("뉴스 분석 멀티에이전트 시스템 (CrewAI) 시작")
    logger.info("=" * 60)

    if not validate_env():
        sys.exit(1)

    try:
        from src.crew import NewsAnalysisCrew

        crew = NewsAnalysisCrew()
        html_report = crew.run()

        if html_report and html_report.strip():
            save_html_report(html_report)
        else:
            logger.error("HTML 리포트 생성 결과가 비어 있습니다.")

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"[ERROR] 파이프라인 실행 중 오류 발생: {e}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("뉴스 분석 멀티에이전트 시스템 종료")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
