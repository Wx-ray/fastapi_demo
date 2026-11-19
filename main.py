# FastAPI 练手项目：users/news 资源的增删改查 + SQLite 持久化
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="练手")

DB_PATH = "app.db"


# ---------- 数据库连接与建表 ----------
def get_conn():
    # 每次请求新开一个连接；row_factory 让查询结果能按列名取值，如 row["姓名"]
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # 服务启动时执行：表不存在就建，空表就插入种子数据
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            姓名 TEXT,
            角色 TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            标题 TEXT,
            内容 TEXT,
            日期 TEXT
        )
    """)

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO users (姓名, 角色) VALUES (?, ?)",
            [("张三", "学生"), ("李四", "学生"), ("王五", "老师")]
        )

    cur.execute("SELECT COUNT(*) FROM news")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO news (标题, 内容, 日期) VALUES (?, ?, ?)",
            [
                ("FastAPI本地跑通", "三个GET接口已在127.0.0.1:8000启动", "2026/11/18"),
                ("远程AI开发岗待投递", "需准备可演示的小项目和GitHub仓库", "2026/11/18"),
                ("Git基础操作待练", "提交、推送、拉取等命令需要上手", "2026/11/18"),
            ]
        )

    conn.commit()
    conn.close()


init_db()


# ---------- 请求体模型 ----------
# 新增用户时，前端必须传过来的数据格式
class UserCreate(BaseModel):
    姓名: str
    角色: str = "学生"

# 修改用户时，字段都选填，传哪个改哪个，不传就保持原样
class UserUpdate(BaseModel):
    姓名: str | None = None
    角色: str | None = None

class NewsCreate(BaseModel):
    标题: str
    内容: str
    日期: str

class NewsUpdate(BaseModel):
    标题: str | None = None
    内容: str | None = None
    日期: str | None = None


# ---------- 基础演示接口 ----------
@app.get("/")
def home():
    return {"状态": "成功", "数据": "服务跑起来了", "框架": "FastAPI"}

@app.get("/hello/{name}")
def greet(name: str):
    return {"消息": f"你好，{name}，欢迎来面试"}

@app.get("/todo")
def todo():
    return {
        "任务": [
            {"id": 1, "内容": "学FastAPI", "完成": True},
            {"id": 2, "内容": "把项目传到GitHub", "完成": False},
            {"id": 3, "内容": "投那个远程AI开发岗", "完成": False}
        ]
    }


# ---------- 用户：增删改查 ----------
@app.get("/users")
def list_users():
    conn = get_conn()
    rows = conn.execute("SELECT id, 姓名, 角色 FROM users ORDER BY id").fetchall()
    conn.close()
    users = [{"id": r["id"], "姓名": r["姓名"], "角色": r["角色"]} for r in rows]
    return {"用户": users}

@app.post("/users")
def add_user(user: UserCreate):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO users (姓名, 角色) VALUES (?, ?)",
        (user.姓名, user.角色)
    )
    conn.commit()
    new_user = {"id": cur.lastrowid, "姓名": user.姓名, "角色": user.角色}
    conn.close()
    return {"消息": "新增成功", "用户": new_user}

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    conn = get_conn()
    row = conn.execute("SELECT id, 姓名, 角色 FROM users WHERE id=?", (user_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")

    data = {"姓名": row["姓名"], "角色": row["角色"]}
    if user.姓名 is not None:
        data["姓名"] = user.姓名
    if user.角色 is not None:
        data["角色"] = user.角色

    conn.execute(
        "UPDATE users SET 姓名=?, 角色=? WHERE id=?",
        (data["姓名"], data["角色"], user_id)
    )
    conn.commit()
    conn.close()
    return {"消息": "修改成功", "用户": {"id": user_id, **data}}

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_conn()
    cur = conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"消息": "删除成功", "id": user_id}


# ---------- 新闻：增删改查 ----------
@app.get("/news")
def list_news():
    conn = get_conn()
    rows = conn.execute("SELECT id, 标题, 内容, 日期 FROM news ORDER BY id").fetchall()
    conn.close()
    news = [
        {"id": r["id"], "标题": r["标题"], "内容": r["内容"], "日期": r["日期"]}
        for r in rows
    ]
    return {"新闻": news}

@app.post("/news")
def add_news(news_item: NewsCreate):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO news (标题, 内容, 日期) VALUES (?, ?, ?)",
        (news_item.标题, news_item.内容, news_item.日期)
    )
    conn.commit()
    new_news = {
        "id": cur.lastrowid,
        "标题": news_item.标题,
        "内容": news_item.内容,
        "日期": news_item.日期
    }
    conn.close()
    return {"消息": "新增成功", "新闻": new_news}

@app.put("/news/{news_id}")
def update_news(news_id: int, news_item: NewsUpdate):
    conn = get_conn()
    row = conn.execute(
        "SELECT id, 标题, 内容, 日期 FROM news WHERE id=?", (news_id,)
    ).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="新闻不存在")

    data = {"标题": row["标题"], "内容": row["内容"], "日期": row["日期"]}
    if news_item.标题 is not None:
        data["标题"] = news_item.标题
    if news_item.内容 is not None:
        data["内容"] = news_item.内容
    if news_item.日期 is not None:
        data["日期"] = news_item.日期

    conn.execute(
        "UPDATE news SET 标题=?, 内容=?, 日期=? WHERE id=?",
        (data["标题"], data["内容"], data["日期"], news_id)
    )
    conn.commit()
    conn.close()
    return {"消息": "修改成功", "新闻": {"id": news_id, **data}}

@app.delete("/news/{news_id}")
def delete_news(news_id: int):
    conn = get_conn()
    cur = conn.execute("DELETE FROM news WHERE id=?", (news_id,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="新闻不存在")
    return {"消息": "删除成功", "id": news_id}


# ---------- 演示页面 ----------
@app.get("/page", response_class=HTMLResponse)
def user_page():
    html = """
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="utf-8">
        <title>数据演示页</title>
        <style>
            body { font-family: sans-serif; margin: 40px; }
            table { border-collapse: collapse; width: 560px; margin-bottom: 30px; }
            th, td { border: 1px solid #999; padding: 8px 14px; }
            th { background: #f0f0f0; }
        </style>
    </head>
    <body>
        <h2>用户列表（来自 /users）</h2>
        <table>
            <thead><tr><th>ID</th><th>姓名</th><th>角色</th></tr></thead>
            <tbody id="user-tbody"></tbody>
        </table>

        <h2>新闻列表（来自 /news）</h2>
        <table>
            <thead><tr><th>ID</th><th>标题</th><th>内容</th><th>日期</th></tr></thead>
            <tbody id="news-tbody"></tbody>
        </table>

        <script>
            fetch('/users')
                .then(r => r.json())
                .then(data => {
                    const tbody = document.getElementById('user-tbody');
                    data['用户'].forEach(u => {
                        tbody.innerHTML += `<tr><td>${u.id}</td><td>${u['姓名']}</td><td>${u['角色']}</td></tr>`;
                    });
                });

            fetch('/news')
                .then(r => r.json())
                .then(data => {
                    const tbody = document.getElementById('news-tbody');
                    data['新闻'].forEach(n => {
                        tbody.innerHTML += `<tr><td>${n.id}</td><td>${n['标题']}</td><td>${n['内容']}</td><td>${n['日期']}</td></tr>`;
                    });
                });
        </script>
    </body>
    </html>
    """
    return html
