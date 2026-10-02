# รวมการบ้าน — 664245023

Streamlit URL: https://22apezkshfcnklimdursax.streamlit.app/

รวมการบ้าน พร้อมไฟล์ประกอบโปรเจกต์ระบบแนะนำขนม (GraphSnack Recommendation System)

[Repository](https://github.com/)

| งาน | การบ้าน | ไฟล์/เว็บไซต์ | Colab |
| --- | --- | --- | --- |
| 01 | แบบฝึกหัด Graph Analysis (Neo4jDBOnline) | — | [เปิด Colab](https://colab.research.google.com/drive/1sAQqauHYCRtjK1jVGrsGJD0Wky-hiM8B?authuser=2&usp=drive_open) |
| 02 | ระบบแนะนำเบื้องต้น (DessertRecommender) | — | [เปิด Colab](https://colab.research.google.com/drive/1psVQlujQ0JD0iQekz-8qHTas4n-Dp3Vz?authuser=2&usp=drive_open) |
| 03 | Web Application ระบบแนะนำขนม (GraphSnack) | [เข้าสู่เว็บไซต์](https://22apezkshfcnklimdursax.streamlit.app/) | — | 
| 04 | ตอบคำถามแบบฝึกหัด  | [เปิด Canva](https://canva.link/nok1viq7c02b7vv) | — | 
| 05 | Slide Presentation (GraphSnack) | [เปิด Canva](https://canva.link/ybigmgpg3xsykij) | — |

---

# 🍿 GraphSnack Recommendation System (ระบบแนะนำขนม)

โปรเจกต์ระบบแนะนำขนมด้วย Graph Database 
พัฒนาด้วย **Streamlit + Neo4j Aura + Cypher** และออกแบบให้ deploy ผ่าน **GitHub → Streamlit Community Cloud** ได้โดยตรง

## 1. แนวคิดของระบบ

ระบบใช้ Property Graph ดังนี้

```text
(Consumer)-[:FRIEND_OF]-(Consumer)
(Consumer)-[:BOUGHT {purchase_date, rating}]->(Snack)
(Consumer)-[:INTERESTED_IN]->(Category)
(Snack)-[:IN_CATEGORY]->(Category)
(Brand)-[:PRODUCED]->(Snack)

จุดเด่นคือคำแนะนำอธิบายได้ (Explainable Recommendation) พร้อมแสดงภาพประกอบ ว่าขนมถูกแนะนำเพราะ
1. เพื่อนของผู้ใช้เคยซื้อ
2. หมวดหมู่ขนมตรงกับความสนใจ
3. ขนมได้รับความนิยม
4. ขนมมีคะแนนเฉลี่ยรีวิวดี

ตัวอย่างคะแนน Hybrid:

```text
score = friend_count*3
      + interest_matches*2
      + popularity*0.20
      + average_rating*0.50
```

สูตรนี้เป็น heuristic เพื่อการเรียนการสอน ไม่ใช่โมเดล ML ที่ผ่านการ optimize

## 2. โครงสร้างไฟล์

```text
graphsnack_recommender/
├── app.py                 
├── neo4j_service.py        
├── requirements.txt        
├── images/
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example
└── README.md 
```

## 3. สร้าง Neo4j Aura

1. สร้าง AuraDB instance
2. เก็บค่า Connection URI, username และ password
3. URI ของ Aura โดยทั่วไปอยู่ในรูป `neo4j+s://...databases.neo4j.io`
4. อย่านำ password ไปใส่ในไฟล์ที่ commit ขึ้น GitHub

## 4. รันในเครื่อง

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

คัดลอกไฟล์ตัวอย่าง secrets

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

จากนั้นใส่ credential จริง แล้วรัน

```bash
streamlit run app.py
```

## 5. ครั้งแรกที่เปิดระบบ

1. เข้าเมนู **Admin / Setup**
2. กด **สร้าง Constraint + Demo Data**
3. ระบบใช้ `MERGE` จึงกดซ้ำได้โดยไม่สร้าง node ซ้ำจาก key เดิม
4. จากนั้นทดลอง Dashboard, Recommendations, Search, Borrow/Rate และ Graph Explorer

## 6. Deploy GitHub → Streamlit Community Cloud

1. สร้าง GitHub repository ใหม่
2. push ไฟล์ทั้งหมดขึ้น GitHub **ยกเว้น `.streamlit/secrets.toml`**
3. เข้า Streamlit Community Cloud แล้วเลือก Create app
4. เลือก repository, branch และ entrypoint = `app.py`
5. ใน Advanced settings → Secrets ใส่

```toml
[neo4j]
uri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"
username = "neo4j"
password = "YOUR_PASSWORD"
database = "neo4j"
```

6. Deploy

## 7. ประเด็น Graph Database ที่นักศึกษาจะได้ฝึก

- Node, Label, Property
- Relationship และ Direction
- Constraint และ Unique Key
- `MATCH`, `MERGE`, `OPTIONAL MATCH`, `WITH`, `UNWIND`
- Graph traversal ผ่านเพื่อน → หนังสือ
- Aggregation เช่น `count`, `avg`, `collect`
- Recommendation จาก topology ของกราฟ
- Parameterized Cypher
- Python Driver และ connection pooling
- Streamlit UI
- Secrets และ cloud deployment

## 8. สิ่งที่ปรับปรุงจาก notebook ต้นแบบ

- ปรับบริบทเป็นระบบแนะนำขนม (Consumer / Snack)
- เพิ่มการแสดงผลรูปภาพขนมในหน้า Recommendations
- เพิ่มฟีเจอร์ Add Snack สำหรับการเพิ่มข้อมูลขนมและแบรนด์ลงฐานข้อมูล
- ใช้ MERGE ใน seed data เพื่อรองรับการรันซ้ำ
- เพิ่ม Unique Constraints
- แยก database layer (neo4j_service.py) ออกจาก UI (app.py)
