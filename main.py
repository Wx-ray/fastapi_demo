# FastAPI 练手项目：users/news 资源的增删改查接口 + 演示页面
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="练手")

# 内存里的用户数据（重启服务就清空，后面接数据库才会持久保存）
users = [
    {"id": 1, "姓名": "张三", "角色": "学生"},
    {"id": 2, "姓名": "李四", "角色": "学生"},
    {"id": 3, "姓名": "王五", "角色": "老师"},
]

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

# 内存里的新闻数据
news = [
    {"id": 1, "标题": "FastAPI本地跑通", "内容": "三个GET接口已在127.0.0.1:8000启动", "日期": "2026/11/18"},
    {"id": 2, "标题": "远程AI开发岗待投递", "内容": "需准备可演示的小项目和GitHub仓库", "日期": "2026/11/18"},
    {"id": 3, "标题": "Git基础操作待练", "内容": "提交、推送、拉取等命令需要上手", "日期": "2026/11/18"}
]

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

@app.get("/news")
def list_news():
    return {"新闻": news}
@app.get("/users")
def list_users():
    return {"用户": users}

@app.post("/users")
def add_user(user: UserCreate):
    new_id = max(u["id"] for u in users) + 1
    new_user = {"id": new_id, "姓名": user.姓名, "角色": user.角色}
    users.append(new_user)
    return {"消息": "新增成功", "用户": new_user}

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    for u in users:
        if u["id"] == user_id:
            if user.姓名 is not None:
                u["姓名"] = user.姓名
            if user.角色 is not None:
                u["角色"] = user.角色
            return {"消息": "修改成功", "用户": u}
    raise HTTPException(status_code=404, detail="用户不存在")

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    for u in users:
        if u["id"] == user_id:
            users.remove(u)
            return {"消息": "删除成功", "id": user_id}
    raise HTTPException(status_code=404, detail="用户不存在")
@app.post("/news")
def add_news(news_item: NewsCreate):
    new_id = max(u["id"] for u in news) + 1
    new_news = {
        "id": new_id,
        "标题": news_item.标题,
        "内容": news_item.内容,
        "日期": news_item.日期
    }
    news.append(new_news)
    return {"消息": "新增成功", "新闻": new_news}


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
