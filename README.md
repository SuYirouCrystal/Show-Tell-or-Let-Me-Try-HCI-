# Show, Tell, or Let Me Try

这是一个基于 Flask 的 HCI 实验后端骨架。它实现了完整实验流程，前端只保留最小可用页面，方便前端同学之后替换 UI。

## 项目目标

这个项目用于比较三种 AI explanation modality 对用户理解、信任校准、认知负担和任务表现的影响。

三种条件是：

1. `show`：视觉解释
2. `tell`：文字解释
3. `try`：交互式解释

用户进入实验后，后端会随机分配一种条件。整个 session 中，用户只会看到这一种解释方式。

## 如何运行

建议使用 Python 3.10 或以上版本。

```bash
cd hci_explanation_backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

然后打开：

```text
http://127.0.0.1:5000
```

## 本地测试指定条件

这些链接只用于开发测试，不要发给真实 participant。

```text
http://127.0.0.1:5000/start?condition=show
http://127.0.0.1:5000/start?condition=tell
http://127.0.0.1:5000/start?condition=try
```

真实实验请使用首页的 Start Study 按钮，让系统随机分组。

## 项目结构

```text
hci_explanation_backend/
  app.py
  config.py
  requirements.txt
  requirements-analysis.txt
  backend/
    __init__.py
    routes.py
    experiment.py
    storage.py
  data/
    tasks.json
    participants.csv
    responses.csv
    surveys.csv
  templates/
    base.html
    welcome.html
    task.html
    survey.html
    done.html
    error.html
  static/
    css/style.css
    js/task.js
  scripts/
    analyze_results.py
```


## 可选数据分析脚本

收完数据后，如果想运行简单统计分析，可以再安装分析依赖：

```bash
pip install -r requirements-analysis.txt
python scripts/analyze_results.py
```

输出会保存在：

```text
analysis_output/
```

## 后端已经实现的功能

### 1. 随机分组

用户开始实验时，后端会随机分配：

```text
show / tell / try
```

代码位置：

```text
backend/experiment.py
```

### 2. 任务读取

所有实验任务都放在：

```text
data/tasks.json
```

每个任务包含：

```text
任务场景
产品选项
AI recommendation
正确答案
AI 是否正确
三种解释条件需要的数据
```

### 3. 实验流程控制

流程是：

```text
/              welcome page
/start         创建 participant session，随机分组
/task/1        第 1 题
/task/2        第 2 题
...
/task/6        第 6 题
/survey        结束问卷
/done          完成页面
```

### 4. 答题数据保存

每道题提交后，后端会写入：

```text
data/responses.csv
```

字段包括：

```text
participant_id
condition
task_id
selected_option
correct_answer
is_correct
ai_recommendation
ai_is_correct
user_thinks_ai_correct
error_detection_correct
confidence_rating
client_decision_ms
server_decision_ms
```

### 5. 问卷数据保存

最终问卷写入：

```text
data/surveys.csv
```

字段包括：

```text
perceived_understanding
trust
mental_demand
effort
frustration
engagement
feedback
```

### 6. 交互式解释 API

`try` 条件中的 sliders 会调用这个接口：

```text
POST /api/tasks/<task_id>/simulate
```

请求格式：

```json
{
  "weights": {
    "price": 30,
    "battery_life": 50,
    "weight": 20
  }
}
```

返回格式：

```json
{
  "recommendation": "A",
  "recommendation_name": "NovaBook Air",
  "scores": []
}
```

这个接口不是一个真实机器学习模型。它是一个 deterministic weighted scoring simulation，用来支持 HCI 实验中的交互式解释。

## 数据导出

本地运行时可以访问：

```text
/admin/export/responses
/admin/export/surveys
/admin/export/participants
```

注意：这些 route 没有身份验证。部署到公网前要删除或加密码。

## 前端说明

前端页面只是骨架，主要目的是让后端流程可以跑通。

前端同学之后可以替换：

```text
templates/*.html
static/css/style.css
static/js/task.js
```

只要保留表单字段名，就不需要改后端。

关键表单字段名：

```text
selected_option
user_thinks_ai_correct
confidence_rating
client_decision_ms
perceived_understanding
trust
mental_demand
effort
frustration
engagement
feedback
```

## 后续可以加的功能

1. 更漂亮的前端页面
2. 平衡随机分组，保证三组人数接近
3. 防止重复提交
4. 管理员登录
5. 数据分析 dashboard
6. 部署到 Render、Railway 或 Columbia server
