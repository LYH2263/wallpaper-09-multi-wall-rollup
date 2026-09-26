# 18-wallpaper（墙纸卷数）

Wallpaper — 幅宽分幅 + 花高匹配损耗后的卷数向上取整

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4700 |
| API | http://localhost:9700 |

## 主链

周长层高+花匹配 → 卷数 → 展开示意

## 合并订卷

`POST /api/estimate/batch`：`{wall_ids:[...], roll_id, save, note}` 一次请求多面墙 + 同一卷材，
各墙按现有算法出 drops/rolls，回包分墙明细与合计；空列表或 dirty 墙/卷报 422 且不增行。
`save=true` 只落一条 run（分墙明细快照存于 result_json，之后改墙不重算）；`save=false` 为试算不落库。
单墙测算仍在 `POST /api/estimate`，合并汇总逻辑独立在 `app/modules/order_batch/`。

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
