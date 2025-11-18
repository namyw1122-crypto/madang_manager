import streamlit as st
import duckdb
import pandas as pd
import time

# 1. DB 연결 (파일에 직접 연결)
# read_only=False로 해야 데이터 입력(INSERT)이 가능합니다.
con = duckdb.connect(database='madang.duckdb', read_only=False)

# 2. 도서 목록 가져오기
# DuckDB는 .df()를 쓰면 바로 pandas DataFrame으로 줍니다!
books_df = con.execute("select concat(bookid, ',', bookname) as book_info from Book").df()
books = books_df['book_info'].tolist()

# 3. 화면 구성
tab1, tab2, tab3 = st.tabs(["고객 조회", "주문 입력", "신규 가입"])

# --- [탭 1] 고객 조회 ---
with tab1:
    name = st.text_input("고객명 입력", key="search_name")
    custid = None 

    if name:
        # 고객 확인
        sql_customer = f"select custid, name, address, phone from Customer where name = '{name}'"
        customer_df = con.execute(sql_customer).df()

        if not customer_df.empty:
            custid = customer_df.iloc[0]['custid'] # pandas 방식으로 값 추출
            st.success(f"검색 성공: {name} (ID: {custid})")
            st.table(customer_df) # 깔끔하게 표로 보여주기

            # 주문 내역 조회
            sql_history = f'''
                select b.bookname, o.orderdate, o.saleprice 
                from Book b, Orders o 
                where o.bookid = b.bookid and o.custid = {custid}
            '''
            history_df = con.execute(sql_history).df()

    
            if not history_df.empty:
                st.dataframe(history_df, use_container_width=True) # 모바일 너비에 맞춤
            else:
                st.info("구매 내역이 없습니다.")
        else:
            st.warning("등록되지 않은 고객입니다.")

# --- [탭 2] 주문 입력 ---
with tab2:

    
    if custid is None:
        st.info("👉 [고객 조회] 탭에서 고객을 먼저 찾아주세요.")
    else:
        st.write(f"**{name}** 님의 주문을 입력합니다.")
        
        select_book = st.selectbox("구매 서적", books)
        price = st.number_input("판매 금액", min_value=0, step=1000)

        if st.button('거래 입력', type="primary"): # 강조 버튼
            if select_book:
                bookid = select_book.split(",")[0]
                dt = time.strftime('%Y-%m-%d', time.localtime())
                
                # 주문번호 생성 (NULL이면 1, 아니면 +1)
                res = con.execute("select COALESCE(max(orderid), 0) + 1 from Orders").fetchone()
                new_orderid = res[0]

                # INSERT 실행
                sql_insert = f"insert into Orders values ({new_orderid}, {custid}, {bookid}, {price}, '{dt}')"
                
                con.execute(sql_insert)
                
                st.success(f"✅ 주문 완료! (주문번호: {new_orderid})")
                time.sleep(1)
                st.rerun() # 화면 새로고침해서 바로 반영

# --- [탭 3] 신규 고객 등록 ---
with tab3:

    new_name = st.text_input("이름", key="new_n")
    new_addr = st.text_input("주소", key="new_a")
    new_phone = st.text_input("전화번호", key="new_p")

    if st.button("등록 하기"):
        if new_name:
            res = con.execute("select COALESCE(max(custid), 0) + 1 from Customer").fetchone()
            new_custid = res[0]
            
            sql_new = f"insert into Customer values ({new_custid}, '{new_name}', '{new_addr}', '{new_phone}')"
            con.execute(sql_new)
            
            st.success(f"🎉 {new_name}님 환영합니다! (ID: {new_custid})")
            time.sleep(1)
            st.rerun()
        else:
            st.error("이름은 필수입니다.")


