from __future__ import annotations

from datetime import date
import base64
import os

import pandas as pd
import streamlit as st

# สมมติว่ามีการแก้ไขชื่อฟังก์ชันในไฟล์ neo4j_service.py ให้สอดคล้องกับบริบทใหม่แล้ว
from neo4j_service import (
    get_dashboard_metrics,
    get_profile,
    get_consumers,
    graph_neighborhood,
    list_categories,
    ping,
    recommend_snacks,
    record_purchase,
    search_snacks,
    seed_demo_data,
)

st.set_page_config(
    page_title="GraphSnack Recommender",
    page_icon="🍿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
      .hero {
        padding: 1.4rem 1.6rem; border-radius: 22px;
        background: linear-gradient(120deg, #111827 0%, #1f2937 55%, #b45309 100%);
        color: white; margin-bottom: 1rem;
      }
      .hero h1 {margin:0; font-size:2.15rem;}
      .hero p {opacity:.88; margin:.35rem 0 0 0;}
      .snack-card {
        padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.25);
        border-radius: 16px; margin-bottom: .75rem; display: flex; align-items: flex-start;
      }
      .snack-image {
        width: 100px; height: auto; border-radius: 8px; margin-right: 15px; object-fit: cover;
      }
      .score-pill {
        display:inline-block; padding:.2rem .55rem; border-radius:999px;
        background:#b45309; color:white; font-size:.8rem; font-weight:700;
      }
      .muted {opacity:.72; font-size:.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def require_connection() -> None:
    try:
        if not ping():
            raise RuntimeError("Neo4j did not return a healthy response")
    except Exception as exc:
        st.error("ยังเชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
        st.code(
            '[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "neo4j"\npassword = "YOUR_PASSWORD"\ndatabase = "neo4j"',
            language="toml",
        )
        st.caption("ให้นำค่าด้านบนไปใส่ใน Streamlit Secrets และห้าม commit password ลง GitHub")
        st.exception(exc)
        st.stop()


def consumer_selector(key: str = "consumer") -> str:
    consumers = get_consumers()
    if not consumers:
        st.info("ยังไม่มีข้อมูลผู้บริโภค กรุณาไปหน้า Admin / Setup แล้วสร้างข้อมูลตัวอย่าง")
        st.stop()
    labels = {f"{x['consumer_id']} — {x['name']}": x["consumer_id"] for x in consumers}
    chosen = st.selectbox("เลือกผู้ใช้", list(labels), key=key)
    return labels[chosen]


def explain_reason(row: dict) -> str:
    parts = []
    if row.get("friend_count", 0):
        friends = ", ".join(row.get("friend_names") or [])
        parts.append(f"เพื่อน {row['friend_count']} คนเคยซื้อ" + (f" ({friends})" if friends else ""))
    if row.get("interest_matches", 0):
        cats = ", ".join(row.get("matched_categories") or [])
        parts.append(f"ตรงกับความสนใจ {row['interest_matches']} หมวด" + (f" ({cats})" if cats else ""))
    if row.get("popularity", 0):
        parts.append(f"ถูกซื้อแล้ว {row['popularity']} ครั้ง")
    if row.get("avg_rating", 0):
        parts.append(f"คะแนนเฉลี่ย {row['avg_rating']:.2f}/5")
    return " • ".join(parts) or "แนะนำจากข้อมูลพฤติกรรมโดยรวม"


require_connection()

with st.sidebar:
    profile_img = "images/Pakkarpon.jpg"
    if os.path.exists(profile_img):
        st.image(profile_img, use_container_width=True)
        
    st.markdown("## 🍿 GraphSnack")
    st.caption("Neo4j Aura + Streamlit")
    
    st.markdown("", unsafe_allow_html=True)
    
    page = st.radio(
        "เมนู",
        ["Dashboard", "Recommendations", "Snack Search", "Purchase / Rate", "Graph Explorer", "Admin / Setup"],
    )
    st.divider()
    st.caption("Graph Database Recommendation System")


st.markdown(
    """
    <div class="hero">
      <h1>🍿 GraphSnack Recommendation System</h1>
      <p>ระบบแนะนำขนมด้วย Graph Database ที่อธิบายเหตุผลของคำแนะนำได้พร้อมภาพประกอบ</p>
    </div>
    """,
    unsafe_allow_html=True,
)


if page == "Dashboard":
    st.subheader("ภาพรวมระบบ")
    m = get_dashboard_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Consumers", m.get("consumers", 0))
    c2.metric("Snacks", m.get("snacks", 0))
    c3.metric("Purchase relationships", m.get("purchases", 0))
    c4.metric("Friend relationships", m.get("friendships", 0))

    st.divider()
    consumer_id = consumer_selector("dash_consumer")
    profile = get_profile(consumer_id)
    
    if profile:
        left, right = st.columns([1, 2])
        with left:
            st.markdown(f"### {profile['name']}")
            st.write(f"**รหัส:** {profile['consumer_id']}")
            st.write("**ความสนใจ:** " + (", ".join(profile["interests"]) or "ยังไม่มี"))
        with right:
            st.markdown("### ประวัติการซื้อขนม")
            if profile.get("purchased"):
                st.dataframe(pd.DataFrame(profile["purchased"]), use_container_width=True, hide_index=True)
            else:
                st.info("ยังไม่มีประวัติการซื้อ")

elif page == "Recommendations":
    st.subheader("✨ ขนมที่แนะนำ")
    consumer_id = consumer_selector("rec_consumer")
    top_n = st.slider("จำนวนคำแนะนำ", 3, 12, 6)
    rows = recommend_snacks(consumer_id, top_n)

    st.caption("คะแนนตัวอย่าง = เพื่อน × 3 + หมวดความสนใจ × 2 + ความนิยม × 0.20 + rating เฉลี่ย × 0.50")
    if not rows:
        st.info("ยังไม่มีคำแนะนำสำหรับผู้ใช้นี้")
    
    for i, row in enumerate(rows, start=1):
        brands = ", ".join(row.get("brands") or []) or "ไม่ระบุแบรนด์"
        categories = ", ".join(row.get("categories") or []) or "ไม่ระบุหมวด"
        
        # จัดการอ่านไฟล์รูปภาพจากเครื่อง
        img_path = row.get("image_url", "")
        img_src = "https://via.placeholder.com/150?text=No+Image"
        
        if img_path and os.path.exists(img_path):
            with open(img_path, "rb") as img_file:
                b64_string = base64.b64encode(img_file.read()).decode()
                img_src = f"data:image/jpeg;base64,{b64_string}"
        
        st.markdown(
            f"""
            <div class="snack-card">
              <img src="{img_src}" class="snack-image" alt="{row['title']}">
              <div>
                  <span class="score-pill">#{i} · score {row['score']:.2f}</span>
                  <h3 style="margin:.55rem 0 .2rem 0">{row['title']}</h3>
                  <div class="muted">{row['snack_id']} · {brands} · {categories}</div>
                  <p style="margin-top:0.5rem;"><b>เหตุผล:</b> {explain_reason(row)}</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

elif page == "Snack Search":
    st.subheader("🔎 ค้นหาขนม")
    c1, c2 = st.columns([2, 1])
    keyword = c1.text_input("ชื่อขนมหรือแบรนด์", placeholder="เช่น Chocolate, Gummy Bears, Chips")
    categories = [""] + list_categories()
    category = c2.selectbox("หมวดหมู่", categories, format_func=lambda x: "ทุกหมวด" if x == "" else x)
    rows = search_snacks(keyword, category)
    st.write(f"พบ {len(rows)} รายการ")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Purchase / Rate":
    st.subheader("📝 บันทึกการซื้อและให้คะแนน")
    consumer_id = consumer_selector("purchase_consumer")
    snacks = search_snacks("", "")
    if not snacks:
        st.info("ยังไม่มีขนมในระบบ")
        st.stop()
    snack_labels = {f"{s['snack_id']} — {s['title']}": s["snack_id"] for s in snacks}
    selected = st.selectbox("ขนม", list(snack_labels))
    purchase_date = st.date_input("วันที่ซื้อ", value=date.today())
    use_rating = st.checkbox("ให้คะแนนพร้อมกัน")
    rating = st.slider("คะแนน", 1.0, 5.0, 4.0, 0.5, disabled=not use_rating)
    if st.button("บันทึก", type="primary", use_container_width=True):
        record_purchase(consumer_id, snack_labels[selected], purchase_date.isoformat(), rating if use_rating else None)
        st.success("บันทึกความสัมพันธ์ BOUGHT แล้ว")

elif page == "Graph Explorer":
    st.subheader("🕸️ Graph Explorer")
    consumer_id = consumer_selector("graph_consumer")
    rows = graph_neighborhood(consumer_id)
    if not rows:
        st.info("ยังไม่มี neighborhood graph")
    else:
        dot = ["digraph G {", 'rankdir="LR";', 'node [shape=box, style="rounded,filled", fillcolor="#f8fafc"];']
        seen_nodes = set()
        for r in rows:
            for nid, label, name in [
                (r["source_id"], r["source_label"], r["source_name"]),
                (r["target_id"], r["target_label"], r["target_name"]),
            ]:
                if nid not in seen_nodes:
                    safe_name = str(name).replace('"', "'")
                    dot.append(f'"{nid}" [label="{safe_name}\\n:{label}"];')
                    seen_nodes.add(nid)
            dot.append(f'"{r["source_id"]}" -> "{r["target_id"]}" [label="{r["relationship"]}"];')
        dot.append("}")
        st.graphviz_chart("\n".join(dot), use_container_width=True)
        with st.expander("ดูข้อมูล edge ที่ใช้วาดกราฟ"):
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Admin / Setup":
    st.subheader("⚙️ Setup ข้อมูลตัวอย่าง")
    st.warning("ปุ่มนี้ไม่ลบข้อมูลเดิม และใช้ MERGE จึงสามารถกดซ้ำได้")
    st.markdown(
        """
        **Graph schema ใหม่สำหรับระบบแนะนำขนม**
        - `(:Consumer)-[:FRIEND_OF]-(:Consumer)`
        - `(:Consumer)-[:BOUGHT {purchase_date, rating}]->(:Snack)`
        - `(:Consumer)-[:INTERESTED_IN]->(:Category)`
        - `(:Snack)-[:IN_CATEGORY]->(:Category)`
        - `(:Brand)-[:PRODUCED]->(:Snack)`
        """
    )
    if st.button("สร้าง Constraint + Demo Data", type="primary", use_container_width=True):
        with st.spinner("กำลังสร้างข้อมูล..."):
            seed_demo_data()
        st.success("สร้างข้อมูลตัวอย่างเรียบร้อยแล้ว")
        st.rerun()