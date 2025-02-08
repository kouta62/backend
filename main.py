from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import mysql.connector

app = FastAPI()

# CORS設定（フロントエンドとバックエンドの通信を許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可（開発用）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MySQL の接続設定
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",  # MySQLのパスワードを設定している場合は入力
    "database": "pos_db"
}

# 商品データモデル
class Product(BaseModel):
    code: str

# 購入データのリクエストモデル
class PurchaseItem(BaseModel):
    code: str
    name: str
    price: int

class PurchaseRequest(BaseModel):
    items: List[PurchaseItem]

# MySQL から商品を検索する API
@app.get("/products/{code}")
def get_product(code: str):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products WHERE code = %s", (code,))
    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if not product:
        return {"error": "商品が見つかりません"}

    return product

# 購入データを MySQL に保存する API
@app.post("/purchase")
def purchase_items(request: PurchaseRequest):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 合計金額の計算
    total_price = sum(item.price for item in request.items)

    # 取引データを保存
    cursor.execute("INSERT INTO transactions (total_price) VALUES (%s)", (total_price,))
    conn.commit()
    transaction_id = cursor.lastrowid

    # 取引明細を保存
    for item in request.items:
        cursor.execute(
            "INSERT INTO transaction_items (transaction_id, product_code, product_name, product_price) VALUES (%s, %s, %s, %s)",
            (transaction_id, item.code, item.name, item.price)
        )
    
    conn.commit()
    cursor.close()
    conn.close()

    return {"status": "success", "total_price": total_price}

# 購入履歴を取得する API
@app.get("/transactions")
def get_transactions():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # すべての取引データを取得
    cursor.execute("SELECT * FROM transactions ORDER BY created_at DESC")
    transactions = cursor.fetchall()

    cursor.close()
    conn.close()

    return transactions
