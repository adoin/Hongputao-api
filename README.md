# 红葡萄 API 包

红葡萄 Windows 和 Android 的来源规则包。程序启动先使用内置或上次验证通过的规则。有已登录 GitHub CLI 的 Windows 客户端读取 Release，其余客户端读取 [GitHub Pages 静态更新入口](https://adoin.github.io/Hongputao-api/feed.json)，避免匿名 API 的限流。两条入口都包含包摘要。

| 规则 | 可更新内容 |
|---|---|
| `search` | 官网页面的搜索路径、关键词和分页参数、结果及分页字段 |
| `recommendations` | 详情路径、剧集 ID 参数、相关剧集所在字段 |
| `playback` | 客户端内置取流来源的尝试顺序 |

包只包含数据。客户端固定允许的来源域名、请求方式、解析能力和包大小。不接受脚本、原生库、任意请求头、文件路径或外部跳转。新增签名算法、原生依赖或不兼容的响应结构需要更新客户端。包内不得放访客资料、签名值、Cookie、播放地址或密钥。

修改 `hongputao-api.json` 后，运行 `python3 scripts/validate.py`。测试搜索分页、推荐和实际播放，再提交并推送与包内版本一致的 `vMAJOR.MINOR.PATCH` Tag。Actions 校验并发布 `hongputao-api.json`。回退时用更高版本重新发布已验证的旧规则内容。

规则按 GPL-3.0-only 提供，见 `LICENSE`。

### EdgeOne 主源与 VPS 备用源

在仓库 Actions 中配置 `EDGEONE_PROJECT`、`EDGEONE_SITE`，将 Pages API Token 存入 Secret `EDGEONE_API_TOKEN`。Tag 出包后会自动把静态文件部署到 EdgeOne。客户端构建参数 `HONGPUTAO_API_FEED` 绑定 EdgeOne 项目的公开 `feed.json`。

VPS 使用独立 HTTPS 静态目录。运行 `python3 scripts/sync_vps.py /srv/hongputao-api/feed.json` 可以把已发布的规则拉到本地并原子更新，适合配置成服务器定时任务。客户端构建参数 `HONGPUTAO_API_FALLBACK_FEED` 绑定 VPS 上的 `feed.json`。客户端按主源、备用源尝试，配置其中任一项后不会再查 GitHub。VPS 单独从发布附件同步，不依赖 EdgeOne。
