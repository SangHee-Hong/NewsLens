"""HTML 리포트 템플릿 — Python에서 조립, LLM은 데이터만 반환"""
from __future__ import annotations


# ── 섹션별 색상 ─────────────────────────────────────────────────────────────
SECTION_COLORS = {
    "economy": "#2563eb",   # 파랑
    "society": "#16a34a",   # 초록
    "tech":    "#7c3aed",   # 보라
}

SECTION_LABELS = {
    "economy": "경제",
    "society": "사회",
    "tech":    "기술",
}


# ── 부분 렌더러 ─────────────────────────────────────────────────────────────
def _keywords_html(keywords: list[str], color: str) -> str:
    tags = "".join(
        f'<span style="display:inline-block;background:{color}18;color:{color};'
        f'border:1px solid {color}44;border-radius:9999px;'
        f'padding:2px 12px;margin:3px 4px;font-size:0.78rem;">'
        f'{k}</span>'
        for k in keywords
    )
    return f'<div style="margin:10px 0 16px;">{tags}</div>'


def _topic_cards_html(topics: list[dict], color: str) -> str:
    cards = []
    for i, t in enumerate(topics):
        link = t.get("originallink") or t.get("link", "")
        link_html = (
            f'<a href="{link}" target="_blank" rel="noopener noreferrer" '
            f'style="display:inline-block;margin-top:10px;padding:4px 12px;'
            f'background:{color};color:#fff;font-size:0.76rem;font-weight:500;'
            f'border-radius:6px;text-decoration:none;letter-spacing:0.02em;">'
            f'원문 보기 ↗</a>'
            if link else ""
        )
        outlet_count = t.get("outlet_count", 0)
        is_hottest = (i == 0)
        badge_bg   = color if is_hottest else "#64748b"
        badge_icon = "🔥" if is_hottest else "📌"
        badge_text = (
            f'{badge_icon} 언론사 {outlet_count}곳 보도'
            if outlet_count
            else (f'{badge_icon} 가장 화제' if is_hottest else f'{badge_icon} 화제')
        )
        cards.append(
            f'<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;'
            f'padding:16px 18px;margin-bottom:12px;border-left:4px solid {color};">'
            # 주제명 + 화제성 배지
            f'<div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:8px;">'
            f'<div style="font-weight:700;font-size:0.97rem;color:#111827;flex:1;">'
            f'{t.get("topic", t.get("title", ""))}</div>'
            f'<span style="flex-shrink:0;background:{badge_bg};color:#fff;'
            f'font-size:0.72rem;font-weight:600;padding:3px 10px;border-radius:9999px;'
            f'white-space:nowrap;">{badge_text}</span>'
            f'</div>'
            # 대표기사 메타
            f'<div style="font-size:0.84rem;color:#374151;font-weight:500;margin-bottom:4px;">'
            f'{t.get("title", "")}</div>'
            f'<div style="font-size:0.76rem;color:#6b7280;margin-bottom:8px;">'
            f'{t.get("publisher", "")}  {t.get("date", "")}</div>'
            f'<div style="font-size:0.87rem;color:#374151;line-height:1.6;">'
            f'{t.get("summary", "")}</div>'
            f'{link_html}'
            f'</div>'
        )
    return "".join(cards)


def _source_link_html(link: str, color: str) -> str:
    if not link:
        return ""
    return (
        f'<a href="{link}" target="_blank" rel="noopener noreferrer" '
        f'style="display:inline-block;margin-top:8px;padding:3px 10px;'
        f'background:{color};color:#fff;font-size:0.74rem;font-weight:500;'
        f'border-radius:6px;text-decoration:none;letter-spacing:0.02em;">'
        f'원문 보기 ↗</a>'
    )


def _comparison_html(comp: dict, color: str) -> str:
    if not comp:
        return ""
    sa = comp.get("source_a", {})
    sb = comp.get("source_b", {})
    sa_link = _source_link_html(sa.get("link", ""), color)
    sb_link = _source_link_html(sb.get("link", ""), "#475569")
    return (
        f'<div style="margin-top:20px;">'
        f'<div style="font-weight:600;font-size:0.92rem;color:#374151;margin-bottom:10px;">'
        f'📰 언론사 비교: {comp.get("issue", "")}</div>'
        f'<table style="width:100%;border-collapse:collapse;font-size:0.88rem;">'
        f'<thead><tr>'
        f'<th style="width:50%;padding:10px 14px;background:{color};color:#fff;'
        f'border-radius:8px 0 0 0;text-align:left;">{sa.get("name", "언론사 A")}</th>'
        f'<th style="width:50%;padding:10px 14px;background:#475569;color:#fff;'
        f'border-radius:0 8px 0 0;text-align:left;">{sb.get("name", "언론사 B")}</th>'
        f'</tr></thead>'
        f'<tbody>'
        f'<tr>'
        f'<td style="padding:12px 14px;border:1px solid #e5e7eb;vertical-align:top;">'
        f'<strong style="color:{color};">{sa.get("title", "")}</strong>'
        f'<p style="margin:6px 0 0;color:#374151;line-height:1.6;">{sa.get("perspective", "")}</p>'
        f'{sa_link}'
        f'</td>'
        f'<td style="padding:12px 14px;border:1px solid #e5e7eb;vertical-align:top;">'
        f'<strong style="color:#475569;">{sb.get("title", "")}</strong>'
        f'<p style="margin:6px 0 0;color:#374151;line-height:1.6;">{sb.get("perspective", "")}</p>'
        f'{sb_link}'
        f'</td>'
        f'</tr>'
        f'<tr><td colspan="2" style="padding:12px 14px;border:1px solid #e5e7eb;'
        f'background:#f8fafc;color:#374151;line-height:1.7;">'
        f'<strong>📊 비교 분석</strong><br>{comp.get("analysis", "")}'
        f'</td></tr>'
        f'</tbody></table></div>'
    )


def _section_html(key: str, section_data: dict) -> str:
    color = SECTION_COLORS[key]
    label = SECTION_LABELS[key]
    topics = section_data.get("topics", [])
    keywords = section_data.get("keywords", [])
    comparison = section_data.get("comparison", {})

    return (
        f'<div style="margin-bottom:40px;">'
        f'<h2 style="font-size:1.25rem;font-weight:700;color:{color};'
        f'border-bottom:2px solid {color};padding-bottom:8px;margin-bottom:16px;">'
        f'{label} 화제 뉴스</h2>'
        f'{_keywords_html(keywords, color)}'
        f'{_topic_cards_html(topics, color)}'
        f'{_comparison_html(comparison, color)}'
        f'</div>'
    )


# ── 최종 HTML 렌더러 ─────────────────────────────────────────────────────────
def render_html(data: dict, generated_at: str, review_score: str = "", review_verdict: str = "") -> str:
    economy_html = _section_html("economy", data.get("economy", {}))
    society_html = _section_html("society", data.get("society", {}))
    tech_html    = _section_html("tech",    data.get("tech",    {}))
    overview     = data.get("overview", "")
    insights     = data.get("insights", "")

    verdict_color = "#16a34a" if "APPROVED" in review_verdict else "#dc2626"
    verdict_label = "✅ APPROVED" if "APPROVED" in review_verdict else "🔄 REVISION"
    score_badge = (
        f'<span style="background:{verdict_color};color:#fff;padding:4px 14px;'
        f'border-radius:9999px;font-size:0.82rem;font-weight:600;">'
        f'{verdict_label} {review_score}</span>'
        if review_score else ""
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>한국 뉴스 분석 리포트</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{
    font-family: 'Noto Sans KR', sans-serif;
    background: #f1f5f9;
    color: #1e293b;
    margin: 0; padding: 0;
  }}
  .header {{
    background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
    color: #fff;
    padding: 36px 40px 28px;
  }}
  .header h1 {{ margin: 0 0 6px; font-size: 1.7rem; font-weight: 700; }}
  .header .meta {{ font-size: 0.85rem; color: #94a3b8; }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 60px; }}
  .card {{
    background: #fff;
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 28px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  }}
  .overview-text {{
    font-size: 0.95rem;
    line-height: 1.8;
    color: #374151;
  }}
  .insights-text {{
    font-size: 0.95rem;
    line-height: 1.8;
    color: #374151;
    white-space: pre-line;
  }}
  h3.card-title {{
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0 0 14px;
  }}
</style>
</head>
<body>

<div class="header">
  <h1>🗞 한국 뉴스 분석 리포트</h1>
  <div class="meta">생성 시각: {generated_at} &nbsp;|&nbsp; CrewAI 멀티에이전트 시스템 {score_badge}</div>
</div>

<div class="container">

  <div class="card">
    <h3 class="card-title">📌 오늘의 뉴스 개요</h3>
    <div class="overview-text">{overview}</div>
  </div>

  <div class="card">{economy_html}</div>
  <div class="card">{society_html}</div>
  <div class="card">{tech_html}</div>

  <div class="card">
    <h3 class="card-title">💡 종합 인사이트</h3>
    <div class="insights-text">{insights}</div>
  </div>

</div>
</body>
</html>"""
