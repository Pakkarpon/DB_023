from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl


def _config() -> tuple[str, str, str, str]:
    cfg = st.secrets["neo4j"]
    return (
        cfg["uri"],
        cfg["username"],
        cfg["password"],
        cfg.get("database", "neo4j"),
    )


@st.cache_resource(show_spinner=False)
def get_driver():
    """Create one thread-safe Neo4j Driver for the Streamlit process."""
    uri, username, password, _ = _config()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def query(cypher: str, parameters: dict[str, Any] | None = None, *, write: bool = False) -> list[dict[str, Any]]:
    """Execute parameterized Cypher and return rows as dictionaries."""
    _, _, _, database = _config()
    records, _, _ = get_driver().execute_query(
        cypher,
        parameters_=parameters or {},
        database_=database,
        routing_=RoutingControl.WRITE if write else RoutingControl.READ,
    )
    return [record.data() for record in records]


def ping() -> bool:
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)


def create_schema() -> None:
    statements = [
        "CREATE CONSTRAINT consumer_id_unique IF NOT EXISTS FOR (c:Consumer) REQUIRE c.consumer_id IS UNIQUE",
        "CREATE CONSTRAINT snack_id_unique IF NOT EXISTS FOR (s:Snack) REQUIRE s.snack_id IS UNIQUE",
        "CREATE CONSTRAINT brand_id_unique IF NOT EXISTS FOR (b:Brand) REQUIRE b.brand_id IS UNIQUE",
        "CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
    ]
    for stmt in statements:
        query(stmt, write=True)


def seed_demo_data() -> None:
    """Idempotent sample dataset: safe to run more than once."""
    create_schema()

    consumers = [
        {"consumer_id": "C001", "name": "Aoy"},
        {"consumer_id": "C002", "name": "Bee"},
        {"consumer_id": "C003", "name": "Chai"},
        {"consumer_id": "C004", "name": "Dew"},
        {"consumer_id": "C005", "name": "Eve"},
        {"consumer_id": "C006", "name": "Fay"},
        {"consumer_id": "C007", "name": "Gao"},
        {"consumer_id": "C008", "name": "Hao"},
        {"consumer_id": "C009", "name": "Ivy"},
        {"consumer_id": "C010", "name": "Jia"},
    ]
    
    snacks = [
        {"snack_id": "SNA101", "title": "Chocolate", "image_url": "images/Chocolate.jpg"},
        {"snack_id": "SNA102", "title": "Chips", "image_url": "images/Chips.jpg"},
        {"snack_id": "SNA103", "title": "Cookies", "image_url": "images/Cookies.jpg"},
        {"snack_id": "SNA104", "title": "Gummy Bears", "image_url": "images/Gummy Bears.jpg"},
        {"snack_id": "SNA105", "title": "Pretzels", "image_url": "images/Pretzels.jpg"},
        {"snack_id": "SNA106", "title": "Candy", "image_url": "images/Candy.jpg"},
        {"snack_id": "SNA107", "title": "Popcorn", "image_url": "images/Popcorn.jpg"},
        {"snack_id": "SNA108", "title": "Crackers", "image_url": "images/Crackers.jpg"},
        {"snack_id": "SNA109", "title": "Fruit Bar", "image_url": "images/Fruit Bar.jpg"},
        {"snack_id": "SNA110", "title": "Nuts", "image_url": "images/Nuts.jpg"},
    ]
    
    brands = [
        {"brand_id": "BR01", "name": "SweetTooth Co."},
        {"brand_id": "BR02", "name": "Salty Bites"},
        {"brand_id": "BR03", "name": "Healthy Snacks Inc."},
    ]
    
    categories = ["Sweet", "Salty", "Healthy", "Chewy", "Crunchy"]

    query(
        """
        UNWIND $rows AS row
        MERGE (c:Consumer {consumer_id: row.consumer_id})
        SET c.name = row.name
        """,
        {"rows": consumers},
        write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MERGE (s:Snack {snack_id: row.snack_id})
        SET s.title = row.title, s.image_url = row.image_url
        """,
        {"rows": snacks},
        write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MERGE (b:Brand {brand_id: row.brand_id})
        SET b.name = row.name
        """,
        {"rows": brands},
        write=True,
    )
    query(
        "UNWIND $rows AS name MERGE (:Category {name:name})",
        {"rows": categories},
        write=True,
    )

    friendships = [
        ["C001", "C002"], ["C001", "C003"], ["C002", "C004"],
        ["C003", "C005"], ["C004", "C006"], ["C005", "C007"],
        ["C006", "C008"], ["C007", "C009"], ["C008", "C010"]
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (a:Consumer {consumer_id: row[0]}), (b:Consumer {consumer_id: row[1]})
        MERGE (a)-[:FRIEND_OF]->(b)
        """,
        {"rows": friendships},
        write=True,
    )

    purchases = [
        {"c": "C001", "s": "SNA101", "date": "2026-10-01", "rating": 5.0},
        {"c": "C001", "s": "SNA104", "date": "2026-10-02", "rating": 4.0},
        {"c": "C002", "s": "SNA102", "date": "2026-10-03", "rating": 4.5},
        {"c": "C003", "s": "SNA101", "date": "2026-10-04", "rating": 5.0},
        {"c": "C004", "s": "SNA105", "date": "2026-10-05", "rating": 3.5},
        {"c": "C005", "s": "SNA103", "date": "2026-10-06", "rating": 4.0},
        {"c": "C006", "s": "SNA107", "date": "2026-10-07", "rating": 5.0},
        {"c": "C007", "s": "SNA109", "date": "2026-10-08", "rating": 4.5},
        {"c": "C008", "s": "SNA110", "date": "2026-10-09", "rating": 4.0},
        {"c": "C009", "s": "SNA106", "date": "2026-10-10", "rating": 3.0},
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (c:Consumer {consumer_id: row.c}), (s:Snack {snack_id: row.s})
        MERGE (c)-[r:BOUGHT]->(s)
        SET r.purchase_date = date(row.date), r.rating = row.rating
        """,
        {"rows": purchases},
        write=True,
    )

    interests = [
        ["C001", "Sweet"], ["C002", "Salty"], ["C003", "Sweet"],
        ["C004", "Salty"], ["C005", "Sweet"], ["C006", "Crunchy"],
        ["C007", "Healthy"], ["C008", "Healthy"], ["C009", "Chewy"]
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (c:Consumer {consumer_id: row[0]}), (cat:Category {name: row[1]})
        MERGE (c)-[:INTERESTED_IN]->(cat)
        """,
        {"rows": interests},
        write=True,
    )

    snack_categories = [
        ["SNA101", "Sweet"], ["SNA102", "Salty"], ["SNA102", "Crunchy"],
        ["SNA103", "Sweet"], ["SNA104", "Sweet"], ["SNA104", "Chewy"],
        ["SNA105", "Salty"], ["SNA105", "Crunchy"], ["SNA106", "Sweet"],
        ["SNA106", "Chewy"], ["SNA107", "Salty"], ["SNA107", "Crunchy"],
        ["SNA108", "Salty"], ["SNA109", "Healthy"], ["SNA109", "Chewy"],
        ["SNA110", "Healthy"], ["SNA110", "Crunchy"]
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (s:Snack {snack_id: row[0]}), (cat:Category {name: row[1]})
        MERGE (s)-[:IN_CATEGORY]->(cat)
        """,
        {"rows": snack_categories},
        write=True,
    )

    produced = [
        ["BR01", "SNA101"], ["BR01", "SNA103"], ["BR01", "SNA104"], ["BR01", "SNA106"],
        ["BR02", "SNA102"], ["BR02", "SNA105"], ["BR02", "SNA107"], ["BR02", "SNA108"],
        ["BR03", "SNA109"], ["BR03", "SNA110"]
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (b:Brand {brand_id: row[0]}), (s:Snack {snack_id: row[1]})
        MERGE (b)-[:PRODUCED]->(s)
        """,
        {"rows": produced},
        write=True,
    )


def get_consumers() -> list[dict[str, Any]]:
    return query("MATCH (c:Consumer) RETURN c.consumer_id AS consumer_id, c.name AS name ORDER BY c.consumer_id")


def get_dashboard_metrics() -> dict[str, int]:
    rows = query(
        """
        MATCH (c:Consumer) WITH count(c) AS consumers
        MATCH (s:Snack) WITH consumers, count(s) AS snacks
        MATCH ()-[r:BOUGHT]->() WITH consumers, snacks, count(r) AS purchases
        MATCH ()-[f:FRIEND_OF]->()
        RETURN consumers, snacks, purchases, count(f) AS friendships
        """
    )
    return rows[0] if rows else {"consumers": 0, "snacks": 0, "purchases": 0, "friendships": 0}


def get_profile(consumer_id: str) -> dict[str, Any] | None:
    rows = query(
        """
        MATCH (c:Consumer {consumer_id:$consumer_id})
        OPTIONAL MATCH (c)-[:INTERESTED_IN]->(cat:Category)
        OPTIONAL MATCH (c)-[:BOUGHT]->(s:Snack)
        RETURN c.consumer_id AS consumer_id, c.name AS name,
               collect(DISTINCT cat.name) AS interests,
               collect(DISTINCT {snack_id:s.snack_id, title:s.title}) AS purchased
        """,
        {"consumer_id": consumer_id},
    )
    if not rows:
        return None
    row = rows[0]
    row["purchased"] = [x for x in row["purchased"] if x.get("snack_id")]
    return row


def recommend_snacks(consumer_id: str, limit: int = 8) -> list[dict[str, Any]]:
    """Explainable hybrid score: social + interests + popularity + ratings."""
    return query(
        """
        MATCH (u:Consumer {consumer_id:$consumer_id})
        MATCH (s:Snack)
        WHERE NOT (u)-[:BOUGHT]->(s)

        OPTIONAL MATCH (u)-[:FRIEND_OF]-(f:Consumer)-[:BOUGHT]->(s)
        WITH u, s, count(DISTINCT f) AS friend_count,
             [x IN collect(DISTINCT f.name) WHERE x IS NOT NULL][0..3] AS friend_names

        OPTIONAL MATCH (u)-[:INTERESTED_IN]->(c:Category)<-[:IN_CATEGORY]-(s)
        WITH s, friend_count, friend_names,
             count(DISTINCT c) AS interest_matches,
             [x IN collect(DISTINCT c.name) WHERE x IS NOT NULL] AS matched_categories

        OPTIONAL MATCH (:Consumer)-[br:BOUGHT]->(s)
        WITH s, friend_count, friend_names, interest_matches, matched_categories,
             count(br) AS popularity,
             avg(br.rating) AS avg_rating

        WITH s, friend_count, friend_names, interest_matches, matched_categories,
             popularity, coalesce(avg_rating, 0.0) AS avg_rating,
             (friend_count * 3.0) + (interest_matches * 2.0) +
             (popularity * 0.20) + (coalesce(avg_rating, 0.0) * 0.50) AS score
        WHERE friend_count > 0 OR interest_matches > 0 OR popularity > 0

        OPTIONAL MATCH (b:Brand)-[:PRODUCED]->(s)
        OPTIONAL MATCH (s)-[:IN_CATEGORY]->(allc:Category)
        RETURN s.snack_id AS snack_id, s.title AS title, s.image_url AS image_url,
               collect(DISTINCT b.name) AS brands,
               collect(DISTINCT allc.name) AS categories,
               friend_count, friend_names, interest_matches, matched_categories,
               popularity, round(avg_rating * 100) / 100.0 AS avg_rating,
               round(score * 100) / 100.0 AS score
        ORDER BY score DESC, s.title
        LIMIT $limit
        """,
        {"consumer_id": consumer_id, "limit": int(limit)},
    )


def search_snacks(keyword: str = "", category: str | None = None) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (s:Snack)
        OPTIONAL MATCH (b:Brand)-[:PRODUCED]->(s)
        OPTIONAL MATCH (s)-[:IN_CATEGORY]->(c:Category)
        WITH s, collect(DISTINCT b.name) AS brands, collect(DISTINCT c.name) AS categories
        WHERE ($keyword = '' OR toLower(s.title) CONTAINS toLower($keyword)
               OR any(x IN brands WHERE toLower(x) CONTAINS toLower($keyword)))
          AND ($category = '' OR $category IN categories)
        RETURN s.snack_id AS snack_id, s.title AS title, s.image_url AS image_url,
               brands, categories
        ORDER BY s.title
        """,
        {"keyword": keyword.strip(), "category": category or ""},
    )


def list_categories() -> list[str]:
    return [row["name"] for row in query("MATCH (c:Category) RETURN c.name AS name ORDER BY c.name")]


def record_purchase(consumer_id: str, snack_id: str, purchase_date: str, rating: float | None = None) -> None:
    query(
        """
        MATCH (c:Consumer {consumer_id:$consumer_id}), (s:Snack {snack_id:$snack_id})
        MERGE (c)-[r:BOUGHT]->(s)
        SET r.purchase_date = date($purchase_date)
        FOREACH (_ IN CASE WHEN $rating IS NULL THEN [] ELSE [1] END | SET r.rating = $rating)
        """,
        {"consumer_id": consumer_id, "snack_id": snack_id, "purchase_date": purchase_date, "rating": rating},
        write=True,
    )


def graph_neighborhood(consumer_id: str, limit: int = 40) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:Consumer {consumer_id:$consumer_id})
        OPTIONAL MATCH p=(u)-[:FRIEND_OF|BOUGHT|INTERESTED_IN*1..2]-(x)
        WITH u, collect(p)[0..$limit] AS paths
        UNWIND paths AS p
        UNWIND relationships(p) AS r
        WITH DISTINCT startNode(r) AS src, r, endNode(r) AS tgt
        RETURN elementId(src) AS source_id, labels(src)[0] AS source_label,
               coalesce(src.name, src.title, src.consumer_id, src.snack_id) AS source_name,
               type(r) AS relationship,
               elementId(tgt) AS target_id, labels(tgt)[0] AS target_label,
               coalesce(tgt.name, tgt.title, tgt.consumer_id, tgt.snack_id) AS target_name
        LIMIT $limit
        """,
        {"consumer_id": consumer_id, "limit": int(limit)},
    )
def add_new_snack(snack_id: str, title: str, image_url: str, brand_name: str, categories: list[str]) -> None:
    # 1. สร้างโหนด Snack ใหม่ 
    query(
        "MERGE (s:Snack {snack_id: $snack_id}) SET s.title = $title, s.image_url = $image_url",
        {"snack_id": snack_id, "title": title, "image_url": image_url},
        write=True
    )
    
    # 2. เชื่อมความสัมพันธ์กับ Brand (ถ้ามีการกรอกชื่อแบรนด์)
    if brand_name.strip():
        query(
            """
            MATCH (s:Snack {snack_id: $snack_id})
            MERGE (b:Brand {name: $brand_name})
            ON CREATE SET b.brand_id = 'BR_' + $snack_id
            MERGE (b)-[:PRODUCED]->(s)
            """,
            {"snack_id": snack_id, "brand_name": brand_name.strip()},
            write=True
        )
        
    # 3. เชื่อมความสัมพันธ์กับ Categories
    if categories:
        query(
            """
            MATCH (s:Snack {snack_id: $snack_id})
            UNWIND $categories AS cat_name
            MERGE (c:Category {name: cat_name})
            MERGE (s)-[:IN_CATEGORY]->(c)
            """,
            {"snack_id": snack_id, "categories": categories},
            write=True
        )
