import os
import time
import logging
import requests
from urllib.parse import urlparse
from crewai.tools import tool

logger = logging.getLogger(__name__)

# ── 메이저 언론사 도메인 매핑 ─────────────────────────────────────────────────
MAJOR_PUBLISHERS: dict[str, str] = {
    "chosun.com":      "조선일보",
    "joongang.co.kr":  "중앙일보",
    "joins.com":       "중앙일보",
    "donga.com":       "동아일보",
    "hani.co.kr":      "한겨레",
    "khan.co.kr":      "경향신문",
    "yna.co.kr":       "연합뉴스",
    "ytn.co.kr":       "YTN",
    "imbc.com":        "MBC",
    "mbc.co.kr":       "MBC",
    "kbs.co.kr":       "KBS",
    "sbs.co.kr":       "SBS",
    "mk.co.kr":        "매일경제",
    "hankyung.com":    "한국경제",
    "etnews.com":      "전자신문",
    "zdnet.co.kr":     "ZDNet",
    "bloter.net":      "블로터",
    "newsis.com":      "뉴시스",
    "news1.kr":        "뉴스1",
}


def _get_publisher(original_link: str, naver_link: str) -> tuple[str, str]:
    """
    originallink 우선, 없으면 link로 도메인 확인 후 언론사명 반환.
    Returns: (사용할_링크, 언론사명)
    """
    for url in (original_link, naver_link):
        if not url:
            continue
        try:
            domain = urlparse(url).netloc.lower().removeprefix("www.")
        except Exception:
            continue
        for key, name in MAJOR_PUBLISHERS.items():
            if key in domain:
                # originallink 우선 반환
                best_link = original_link if original_link else naver_link
                return best_link, name
    best_link = original_link if original_link else naver_link
    return best_link, ""


def _clean(text: str) -> str:
    return text.replace("<b>", "").replace("</b>", "").strip()


def _filter_items(items: list[dict], count: int = 10) -> list[dict]:
    """메이저 언론사 기사를 앞으로, 나머지는 뒤에 배치 후 count개 반환."""
    major, others = [], []
    for item in items:
        orig = item.get("originallink", "")
        nav  = item.get("link", "")
        _, publisher = _get_publisher(orig, nav)
        item["_publisher"] = publisher
        item["_link"] = orig if orig else nav
        if publisher:
            major.append(item)
        else:
            others.append(item)

    selected = (major + others)[:count]
    logger.info(
        f"[NaverSearch] 메이저 {len(major)}건 / 기타 {len(others)}건 → "
        f"상위 {len(selected)}건 선택"
    )
    return selected


@tool("Naver_News_Search")
def naver_news_search(query: str) -> str:
    """
    네이버 뉴스 API를 사용하여 한국 최신 뉴스를 검색합니다.
    메이저 언론사(조선일보, 중앙일보, 한겨레, 연합뉴스 등) 기사를 우선 반환합니다.
    query: 검색할 키워드 (한국어 또는 영어)
    """
    client_id     = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        logger.error("[NaverSearch] NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경변수가 없습니다.")
        return "네이버 API 인증 정보가 설정되지 않았습니다."

    url     = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id":     client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query":   query,
        "display": 20,   # 주제 클러스터링을 위해 충분히 가져옴
        "sort":    "date",
    }

    logger.info(f"[NaverSearch] 검색 쿼리: '{query}'")

    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data  = response.json()
            items = data.get("items", [])
            logger.info(f"[NaverSearch] '{query}' API 응답 건수: {len(items)}")

            if not items:
                return f"'{query}'에 대한 검색 결과가 없습니다."

            selected = _filter_items(items, count=3)

            results = []
            for i, item in enumerate(selected, 1):
                title       = _clean(item.get("title", ""))
                description = _clean(item.get("description", ""))
                pub_date    = item.get("pubDate", "")
                publisher   = item["_publisher"] or "알 수 없음"
                link        = item["_link"]

                results.append(
                    f"[{i}] 제목: {title}\n"
                    f"    언론사: {publisher}\n"
                    f"    날짜: {pub_date}\n"
                    f"    요약: {description}\n"
                    f"    링크: {link}"
                )

            return "\n\n".join(results)

        except requests.HTTPError as e:
            logger.warning(f"[NaverSearch] HTTP 오류 (시도 {attempt + 1}/3): {e}")
        except requests.ConnectionError as e:
            logger.warning(f"[NaverSearch] 연결 오류 (시도 {attempt + 1}/3): {e}")
        except requests.Timeout:
            logger.warning(f"[NaverSearch] 타임아웃 (시도 {attempt + 1}/3)")
        except Exception as e:
            logger.warning(f"[NaverSearch] 예상치 못한 오류 (시도 {attempt + 1}/3): {e}")

        if attempt < 2:
            logger.info("[NaverSearch] 2초 후 재시도...")
            time.sleep(2)

    logger.error(f"[NaverSearch] 3회 재시도 후 최종 실패 - 쿼리: '{query}'")
    return f"'{query}' 뉴스 검색에 실패했습니다 (3회 재시도 초과). 해당 분야는 스킵됩니다."
