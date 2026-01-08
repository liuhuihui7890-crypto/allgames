
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
import mysql.connector
import os

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库配置
db_config = {
    "host": "localhost",
    "user": "test",  # 你的 MySQL 用户名
    "password": "SA123",  # 你的 MySQL 密码
    "database": "minigame_platform"
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 数据模型
class UserAuth(BaseModel):
    username: str
    password: str

class ScoreSubmit(BaseModel):
    game_key: str
    user_id: int
    score: int

# 路由
@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.post("/api/register")
async def register(user: UserAuth):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        hashed = pwd_context.hash(user.password)
        cursor.execute("INSERT INTO minigame_users (username, password_hash) VALUES (%s, %s)", (user.username, hashed))
        conn.commit()
        return {"message": "注册成功"}
    except:
        raise HTTPException(status_code=400, detail="用户名已存在")
    finally:
        cursor.close()
        conn.close()

@app.post("/api/login")
async def login(user: UserAuth):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM minigame_users WHERE username = %s", (user.username,))
    db_user = cursor.fetchone()
    if not db_user or not pwd_context.verify(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="信息错误")
    return {"id": db_user["id"], "username": db_user["username"], "avatar": db_user["avatar_url"]}

@app.get("/api/games")
async def get_games():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT game_key as id, name, description as `desc`, icon, url FROM minigame_list")
    games = cursor.fetchall()
    cursor.close()
    conn.close()
    return games

@app.post("/api/scores")
async def submit_score(data: ScoreSubmit):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO minigame_scores (game_key, user_id, score) VALUES (%s, %s, %s)",
                   (data.game_key, data.user_id, data.score))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/scores/{game_key}")
async def get_leaderboard(game_key: str):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT u.username as player_name, u.avatar_url, s.score 
        FROM minigame_scores s 
        JOIN minigame_users u ON s.user_id = u.id 
        WHERE s.game_key = %s ORDER BY s.score DESC LIMIT 10
    """
    cursor.execute(query, (game_key,))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return res

app.mount("/static", StaticFiles(directory="static"), name="static")



