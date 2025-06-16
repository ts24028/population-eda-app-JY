import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")

        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded).replace('-', 0)
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        import matplotlib.font_manager as fm
        plt.rcParams['font.family'] = 'Malgun Gothic'  # 또는 'NanumGothic', 'AppleGothic'
        plt.rcParams['axes.unicode_minus'] = False
        
        tabs = st.tabs([
            "0. 목적 & 절차",
            "1. 데이터 구조 & 통계",
            "2. 결측치 & 중복 체크",
            "3. 연도별 추이",
            "4. 지역별 변화량",
            "5. 증감률 Top 100",
            "6. 누적 시각화",
            "7. 이상치 제거",
            "8. 로그 변환",
            "9. 사용자 정의 시각화",
            "10. 기타 참고사항",
            "11. 개발자 노트"
        ])

        # 0. 목적
        with tabs[0]:
            st.header("📌 목적 & 분석 절차")
            st.markdown("""
            - 이 앱은 `population_trends.csv` 데이터를 기반으로 대한민국 인구의 시계열적, 지역적 분석을 수행합니다.
            - 분석 목표:
              - 연도별 전국 인구 추이 확인
              - 지역별 인구 변화량 및 증감률 비교
              - 2035년 인구 예측 및 시각화
              - 누적 시각화를 통한 전체 구조 파악
            """)

        # 1. 기초 통계
        with tabs[1]:
            st.header("📋 데이터 구조 및 요약 통계")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("기초 통계량 (`df.describe()`)")
            st.dataframe(df.describe())

            st.subheader("샘플 데이터")
            st.dataframe(df.head())

        # 2. 결측치 & 중복
        with tabs[2]:
            st.header("🧼 품질 체크")

            st.subheader("결측값 개수")
            missing = df.isnull().sum()
            if missing.sum() == 0:
                st.success("✅ 결측값이 없습니다.")
            else:
                fig, ax = plt.subplots()
                missing[missing > 0].plot(kind='bar', ax=ax)
                ax.set_ylabel("결측값 개수")
                ax.set_title("Missing Values")
                plt.xticks(rotation=45)
                st.pyplot(fig)

            st.subheader("중복 행 개수")
            duplicates = df.duplicated().sum()
            st.write(f"🔁 중복 행: {duplicates}개")

        # 3. 연도별 인구 추이 및 예측
        with tabs[3]:
            st.header("📈 연도별 전체 인구 추이")
            nat = df[df['지역'] == '전국'].sort_values('연도')
            fig, ax = plt.subplots()
            ax.plot(nat['연도'], nat['인구'], marker='o', label='Population')

            recent = nat.tail(3)
            delta = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            last_year = nat['연도'].max()
            last_pop = nat[nat['연도'] == last_year]['인구'].values[0]
            pred_year = 2035
            pred_pop = int(last_pop + (pred_year - last_year) * delta)
            ax.scatter(pred_year, pred_pop, color='red')
            ax.text(pred_year, pred_pop, f"{pred_pop:,}", color='red')
            ax.set_title("Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)

        # 4. 지역별 변화량
        with tabs[4]:
            st.header("📊 최근 5년 지역별 인구 변화량")
            recent = df[df['연도'] >= df['연도'].max() - 4]
            pivot = recent.pivot(index='연도', columns='지역', values='인구')
            diff_abs = pivot.iloc[-1] - pivot.iloc[0]
            diff_pct = ((pivot.iloc[-1] - pivot.iloc[0]) / pivot.iloc[0]) * 100
            diff_abs = diff_abs.drop('전국', errors='ignore').sort_values(ascending=False)

            fig1, ax1 = plt.subplots(figsize=(10, 6))
            sns.barplot(x=diff_abs.values / 1000, y=diff_abs.index, ax=ax1)
            for i, v in enumerate(diff_abs.values / 1000):
                ax1.text(v, i, f"{v:.1f}", va='center')
            ax1.set_title("Population Change (K)")
            ax1.set_xlabel("Population (thousands)")
            st.pyplot(fig1)

            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sns.barplot(x=diff_pct.loc[diff_abs.index].values, y=diff_pct.loc[diff_abs.index].index, ax=ax2)
            for i, v in enumerate(diff_pct.loc[diff_abs.index].values):
                ax2.text(v, i, f"{v:.1f}%", va='center')
            ax2.set_title("Population Change Rate (%)")
            ax2.set_xlabel("Change (%)")
            st.pyplot(fig2)

        # 5. 증감률 상위
        with tabs[5]:
            st.header("📈 연도별 인구 증감 Top 100")
            df_ = df[df['지역'] != '전국'].copy()
            df_.sort_values(['지역', '연도'], inplace=True)
            df_['증감'] = df_.groupby('지역')['인구'].diff()
            top100 = df_.sort_values(by='증감', ascending=False).head(100)

            top100['증감(천명)'] = (top100['증감'] / 1000).round(1)
            top100['인구'] = top100['인구'].apply(lambda x: f"{x:,}")
            top100['증감'] = top100['증감'].apply(lambda x: f"{x:,.0f}")

            def highlight(val):
                try:
                    num = float(val.replace(',', ''))
                    if num > 0:
                        return 'background-color: lightblue'
                    elif num < 0:
                        return 'background-color: lightcoral'
                except:
                    return ''
                return ''

            styled = top100[['연도', '지역', '인구', '증감']].style.applymap(highlight, subset=['증감'])
            st.dataframe(styled)

        # 6. 누적 시각화
        with tabs[6]:
            st.header("📊 누적 영역 시각화 (연도 x 지역)")
            pivot = df[df['지역'] != '전국'].pivot_table(index='연도', columns='지역', values='인구', aggfunc='sum')
            fig, ax = plt.subplots(figsize=(12, 6))
            pivot.plot.area(ax=ax, colormap='tab20')
            ax.set_title("Population by Region Over Time")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0), fontsize='small')
            st.pyplot(fig)

        # 7. 이상치 제거
        with tabs[7]:
            st.header("🚫 이상치 제거 (인구 기준)")
            mean_pop = df['인구'].mean()
            std_pop = df['인구'].std()
            upper = mean_pop + 3 * std_pop
            filtered = df[df['인구'] <= upper]
            st.write(f"Before: {df.shape[0]} rows → After: {filtered.shape[0]} rows")

        # 8. 로그 변환
        with tabs[8]:
            st.header("🔄 로그 변환 (인구)")
            df['log_pop'] = np.log1p(df['인구'])
            fig, ax = plt.subplots(1, 2, figsize=(12, 4))
            sns.histplot(df['인구'], kde=True, ax=ax[0])
            ax[0].set_title("Original Population")
            sns.histplot(df['log_pop'], kde=True, ax=ax[1])
            ax[1].set_title("Log(Population+1)")
            st.pyplot(fig)

        # 9. 사용자 정의 시각화
        with tabs[9]:
            st.header("🎨 사용자 정의 시각화")
            region = st.selectbox("지역 선택", sorted(df['지역'].unique()))
            fig, ax = plt.subplots()
            subset = df[df['지역'] == region]
            ax.plot(subset['연도'], subset['인구'], marker='o')
            ax.set_title(f"{region} 연도별 인구 추이")
            st.pyplot(fig)

        # 10. 기타 참고
        with tabs[10]:
            st.header("ℹ️ 참고 정보")
            st.markdown("""
            - 데이터 출처: 통계청 (예시)
            - 결측치 처리 방식: '-' → 0 대체 후 numeric 변환
            - 분석 단위: 연도별, 지역별
            """)

        # 11. 개발자 노트
        with tabs[11]:
            st.header("👨‍💻 개발자 노트")
            st.markdown("""
            - 작성자: ChatGPT
            - 목적: Streamlit을 활용한 실시간 인구 데이터 시각화
            - 확장 가능성: 예측 모델, 인터랙티브 필터, PDF 리포트 등
            """)
# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()