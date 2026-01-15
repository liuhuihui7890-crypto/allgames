
import mysql.connector
import sys

# 数据库配置 - 请确保这与您 main.py 中的配置一致
db_config = {
    "host": "localhost",
    "user": "test", 
    "password": "SA123",
    "database": "minigame_platform"
}

def fix_system():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("Connected to database...")

        # 1. 尝试添加 is_admin 字段
        try:
            print("Checking/Adding 'is_admin' column...")
            cursor.execute("ALTER TABLE minigame_users ADD COLUMN is_admin TINYINT(1) DEFAULT 0")
            print("  - Added 'is_admin' column.")
        except mysql.connector.Error as err:
            if err.errno == 1060: # Duplicate column name
                print("  - 'is_admin' column already exists.")
            else:
                print(f"  - Warning: {err}")

        # 2. 插入新游戏
        games = [
            {"k": "raiden", "n": "雷电战机", "d": "太空射击，躲避弹幕击败敌人。", "i": "🚀", "u": "/static/games/raiden/index.html"},
            {"k": "poker", "n": "21点扑克", "d": "运气与策略的较量。", "i": "🃏", "u": "/static/games/poker/index.html"},
            {"k": "gomoku", "n": "五子棋", "d": "黑白对弈，五子连珠者胜。", "i": "⚫", "u": "/static/games/gomoku/index.html"},
            {"k": "mole", "n": "打地鼠", "d": "拼手速，看见地鼠就敲！", "i": "🐹", "u": "/static/games/mole/index.html"},
            {"k": "maze", "n": "迷宫挑战", "d": "寻找出口，逃离迷宫。", "i": "🗺️", "u": "/static/games/maze/index.html"},
            {"k": "tank", "n": "坦克大战", "d": "保卫基地，消灭敌方坦克。", "i": "🛡️", "u": "/static/games/tank/index.html"}
        ]
        
        print("Inserting/Updating new games...")
        query = "INSERT INTO minigame_list (game_key, name, description, icon, url) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE name=VALUES(name), description=VALUES(description), icon=VALUES(icon), url=VALUES(url)"
        for g in games:
            cursor.execute(query, (g['k'], g['n'], g['d'], g['i'], g['u']))
        print("  - Games updated.")

        # 3. 提权用户
        # 您可以在这里修改为您具体的用户名，例如 "admin"
        # 如果不知道用户名，下面的语句会将所有用户都设为管理员
        print("Promoting users to Admin...")
        cursor.execute("UPDATE minigame_users SET is_admin = 1")
        print(f"  - {cursor.rowcount} users promoted to admin.")

        conn.commit()
        print("\nSUCCESS! Database updated.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    fix_system()
