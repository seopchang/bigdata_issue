import streamlit as st
import google.generativeai as genai
import feedparser
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# 1. 웹사이트 기본 설정
st.set_page_config(page_title="AI 뉴스 & 논문 분석기", page_icon="🤖", layout="wide")
st.title("🤖 최신 뉴스 & 논문 트렌드 분석기")
st.write("관련 분야의 최신 뉴스와 논문을 수집하고 AI가 핵심 주제와 키워드를 정리해 줍니다. (제목 클릭 시 원문 이동)")

# 2. 사이드바: API 키 및 검색 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Google AI Studio API Key", type="password")
    st.markdown("---")
    search_query = st.text_input("검색어 입력", "XAI 인공지능") 
    search_button = st.button("데이터 수집 및 AI 분석 시작")

# 3. 데이터 수집 함수 (뉴스 & 논문) - 링크 포함 버전
def get_news(keyword, limit=15):
    """구글 뉴스 RSS에서 제목과 링크를 가져옵니다."""
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={safe_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    news_data = []
    for entry in feed.entries[:limit]:
        # 제목을 클릭하면 링크로 이동하도록 마크다운 형식으로 저장
        news_data.append(f"- [뉴스] [{entry.title}]({entry.link})")
    return "\n".join(news_data)

def get_papers(keyword, limit=15):
    """arXiv API에서 논문 제목과 링크를 가져옵니다."""
    safe_keyword = urllib.parse.quote(keyword)
    url = f"http://export.arxiv.org/api/query?search_query=all:{safe_keyword}&start=0&max_results={limit}&sortBy=submittedDate&sortOrder=descending"
    try:
        response = urllib.request.urlopen(url).read()
        root = ET.fromstring(response)
        papers_data = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip().replace('\n', ' ')
            link = entry.find('{http://www.w3.org/2005/Atom}id').text.strip()
            # 제목을 클릭하면 링크로 이동하도록 마크다운 형식으로 저장
            papers_data.append(f"- [논문] [{title}]({link})")
        return "\n".join(papers_data)
    except Exception as e:
        return "- 논문 데이터를 불러오는 데 실패했습니다."

# 4. 메인 실행 로직
if search_button:
    if not api_key:
        st.error("👈 왼쪽 사이드바에 Google AI API Key를 먼저 입력해 주세요!")
    elif not search_query:
        st.warning("검색어를 입력해 주세요.")
    else:
        with st.spinner('데이터를 수집하고 상세 리포트를 작성 중입니다...'):
            try:
                # API 키 설정
                genai.configure(api_key=api_key)
                
                # AI 모델 자동 탐색
                valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(valid_models[0])

                # 데이터 수집 (15개씩)
                news_text = get_news(search_query, limit=15)
                papers_text = get_papers(search_query, limit=15)
                combined_text = f"### 수집된 뉴스 목록\n{news_text}\n\n### 수집된 논문 목록\n{papers_text}"

                # AI 프롬프트 (설명 길이를 100자 내외로 강조)
                prompt = f"""
                다음은 '{search_query}'와 관련된 최신 뉴스와 논문 제목들입니다.
                이 데이터를 바탕으로 보고서 형식의 상세 분석 리포트를 작성해 주세요.
                
                1. 전체적인 최신 동향 요약 (전문적이고 체계적인 4문장 내외)
                2. 핵심 주제 10가지 (각 주제별로 중요성과 핵심 내용을 포함하여 '100자 내외'로 상세히 설명해 주세요.)
                3. 눈여겨볼 중요 키워드 10개 (해시태그 형태, 예: #머신러닝)
                
                데이터:
                {combined_text}
                """

                # AI 분석 요청
                response = model.generate_content(prompt)

                # 결과 출력
                st.success("분석이 완료되었습니다!")
                
                tab1, tab2 = st.tabs(["💡 AI 트렌드 분석 리포트", "📚 수집 데이터 원문 링크"])
                
                with tab1:
                    st.markdown(response.text)
                
                with tab2:
                    st.info("제목을 클릭하면 해당 뉴스나 논문 페이지로 이동합니다.")
                    st.markdown(combined_text)

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
