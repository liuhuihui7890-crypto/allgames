
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
import mysql.connector
import os
import shutil
import uuid
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db_config = {
    "host": "localhost",
    "user": "test", 
    "password": "SA123",
    "database": "minigame_platform"
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
os.makedirs("static/avatars", exist_ok=True)

# --- Models ---
class UserAuth(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    password: Optional[str] = None
    # nickname: Optional[str] = None # Future use

class GameUpdate(BaseModel):
    game_key: str
    name: str
    description: str
    icon: str
    url: str

class ScoreSubmit(BaseModel):
    game_key: str
    user_id: int
    score: int

# --- Routes ---

@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.post("/api/register")
async def register(user: UserAuth):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM minigame_users WHERE username = %s", (user.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    hashed_password = pwd_context.hash(user.password)
    default_avatar = "/static/avatars/default.png"
    
    # is_admin defaults to 0
    insert_query = "INSERT INTO minigame_users (username, password_hash, avatar_url, is_admin) VALUES (%s, %s, %s, 0)"
    try:
        cursor.execute(insert_query, (user.username, hashed_password, default_avatar))
    except mysql.connector.Error:
        # Fallback if is_admin column doesn't exist yet (for smooth transition)
        insert_query_old = "INSERT INTO minigame_users (username, password_hash, avatar_url) VALUES (%s, %s, %s)"
        cursor.execute(insert_query_old, (user.username, hashed_password, default_avatar))

    conn.commit()
    user_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return {"id": user_id, "username": user.username, "avatar": default_avatar, "is_admin": 0}

@app.post("/api/login")
async def login(user: UserAuth):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM minigame_users WHERE username = %s", (user.username,))
    db_user = cursor.fetchone()
    if not db_user or not pwd_context.verify(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="信息错误")
    
    # Check is_admin column safely
    is_admin = db_user.get("is_admin", 0)
    
    return {"id": db_user["id"], "username": db_user["username"], "avatar": db_user["avatar_url"], "is_admin": is_admin}

@app.put("/api/user/{user_id}")
async def update_user(user_id: int, data: UserUpdate):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    if data.password:
        hashed = pwd_context.hash(data.password)
        cursor.execute("UPDATE minigame_users SET password_hash = %s WHERE id = %s", (hashed, user_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "更新成功"}

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
async def submit_score(score_data: ScoreSubmit):
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username FROM minigame_users WHERE id = %s", (score_data.user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        player_name = user['username']
        insert_query = "INSERT INTO minigame_scores (game_key, user_id, score, player_name) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, (score_data.game_key, score_data.user_id, score_data.score, player_name))
        conn.commit()
        return {"message": "分数提交成功"}
    except mysql.connector.Error as err:
        print(f"DB Error: {err}")
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.get("/api/scores/{game_key}")
async def get_leaderboard(game_key: str):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT u.username as player_name, u.avatar_url, MAX(s.score) as score 
        FROM minigame_scores s 
        JOIN minigame_users u ON s.user_id = u.id 
        WHERE s.game_key = %s 
        GROUP BY u.id, u.username, u.avatar_url
        ORDER BY score DESC LIMIT 10
    """
    cursor.execute(query, (game_key,))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return res

@app.get("/api/user/stats/{user_id}")
async def get_user_stats(user_id: int):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT s.game_key, g.name as game_name, MAX(s.score) as best_score
        FROM minigame_scores s
        JOIN minigame_list g ON s.game_key = g.game_key
        WHERE s.user_id = %s
        GROUP BY s.game_key, g.name
    """
    cursor.execute(query, (user_id,))
    stats = cursor.fetchall()
    cursor.close()
    conn.close()
    return stats

@app.post("/api/user/avatar")
async def upload_avatar(user_id: int = Form(...), file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只能上传图片文件")
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"{user_id}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = f"static/avatars/{filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    avatar_url = f"/{file_path}"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("UPDATE minigame_users SET avatar_url = %s WHERE id = %s", (avatar_url, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"avatar_url": avatar_url}

# --- Admin Routes ---

@app.get("/api/admin/users")
async def admin_get_users():
    # In real app, verify admin token here
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, avatar_url, is_admin FROM minigame_users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: int):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    # Delete scores first
    cursor.execute("DELETE FROM minigame_scores WHERE user_id = %s", (user_id,))
    # Delete user
    cursor.execute("DELETE FROM minigame_users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Deleted"}

@app.post("/api/admin/games")
async def admin_save_game(game: GameUpdate):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    query = """
        INSERT INTO minigame_list (game_key, name, description, icon, url)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name=VALUES(name), description=VALUES(description), icon=VALUES(icon), url=VALUES(url)
    """
    cursor.execute(query, (game.game_key, game.name, game.description, game.icon, game.url))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Saved"}

@app.delete("/api/admin/games/{game_key}")
async def admin_delete_game(game_key: str):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM minigame_scores WHERE game_key = %s", (game_key,))
    cursor.execute("DELETE FROM minigame_list WHERE game_key = %s", (game_key,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Deleted"}

app.mount("/static", StaticFiles(directory="static"), name="static")
