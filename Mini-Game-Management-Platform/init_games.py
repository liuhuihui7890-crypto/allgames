
import mysql.connector

db_config = {
    "host": "localhost",
    "user": "test", 
    "password": "SA123",
    "database": "minigame_platform"
}

games = [
    {
        "game_key": "tetris",
        "name": "俄罗斯方块",
        "description": "经典益智游戏，消除方块获得高分！",
        "icon": "🧱",
        "url": "/static/games/tetris/index.html"
    },
    {
        "game_key": "pong",
        "name": "乒乓球",
        "description": "向经典致敬，简单的双人对战体验。",
        "icon": "🏓",
        "url": "/static/games/pong/index.html"
    },
    {
        "game_key": "breakout",
        "name": "打砖块",
        "description": "控制挡板，击碎所有砖块！",
        "icon": "🔨",
        "url": "/static/games/breakout/index.html"
    },
    {
        "game_key": "2048",
        "name": "2048",
        "description": "合并数字，挑战2048！",
        "icon": "🔢",
        "url": "/static/games/2048/index.html"
    },
    {
        "game_key": "flappy",
        "name": "像素鸟",
        "description": "虐心神作，看看你能飞多远。",
        "icon": "🐦",
        "url": "/static/games/flappy/index.html"
    }
]

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    insert_query = """
        INSERT INTO minigame_list (game_key, name, description, icon, url)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name=VALUES(name), description=VALUES(description), icon=VALUES(icon), url=VALUES(url)
    """
    
    for game in games:
        cursor.execute(insert_query, (game['game_key'], game['name'], game['description'], game['icon'], game['url']))
        print(f"Added/Updated game: {game['name']}")
        
    conn.commit()
    print("All games initialized successfully!")
    
except mysql.connector.Error as err:
    print(f"Error: {err}")
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()
