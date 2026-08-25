---
source_hash: d0594ec094733ff9a9b13d38f4b41a9088a8fd35e54d762f918681da30ddbd29
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/blog/)
<!-- translation-notice:end -->

# 开发者博客

本节提供使用 `starlette-admin` 构建管理界面的高级模式与实用技巧。这些文章聚焦于真实场景中的实现，是对标准参考文档的进一步拓展。

## 发布新文章

Zensical 平台目前依赖于一个手动维护的博客内容静态索引。要发布新文章，请完成以下步骤：

1. **创建内容：**撰写你的文章，并将 Markdown 文件保存在 `blog/posts/` 目录中。
2. **更新索引：**在下方的**已发布文章**表格中添加一行，注明发布日期以及指向你文件的相对链接。
3. **更新配置：**在 `zensical.toml` 文件中注册新文章的路径。

## 已发布文章

| 日期 | 文章标题 |
| --- | --- |
| 2026-07-13 | [使用 starlette-admin 在 5 分钟内为 FastAPI 添加管理后台](posts/add-admin-panel-to-fastapi-in-5-minutes.md) |
| 2026-07-10 | [使用 FastAPI 与 starlette-admin 实现软删除和回收站视图](posts/soft-deletes-trash-view.md) |
