
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
import mysql.connector
import os
import shutil
import uuid

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

# 确保头像目录存在
os.makedirs("static/avatars", exist_ok=True)

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
    cursor.execute("SELECT id FROM minigame_users WHERE username = %s", (user.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    hashed_password = pwd_context.hash(user.password)
    default_avatar = "/static/avatars/default.png"
    
    insert_query = "INSERT INTO minigame_users (username, password_hash, avatar_url) VALUES (%s, %s, %s)"
    cursor.execute(insert_query, (user.username, hashed_password, default_avatar))
    conn.commit()
    user_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return {"id": user_id, "username": user.username, "avatar": default_avatar}

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

        insert_query = """
            INSERT INTO minigame_scores (game_key, user_id, score, player_name) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (score_data.game_key, score_data.user_id, score_data.score, player_name))
        conn.commit()
        
        return {"message": "分数提交成功"}
    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        raise HTTPException(status_code=500, detail=f"提交积分失败: {err}")
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

# --- 个人中心相关接口 ---

@app.get("/api/user/stats/{user_id}")
async def get_user_stats(user_id: int):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    # 获取用户所有游戏的最高分
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
    # 验证文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只能上传图片文件")
    
    # 生成文件名
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"{user_id}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = f"static/avatars/{filename}"
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 更新数据库
    avatar_url = f"/{file_path}"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("UPDATE minigame_users SET avatar_url = %s WHERE id = %s", (avatar_url, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"avatar_url": avatar_url}

app.mount("/static", StaticFiles(directory="static"), name="static")
