# Developer Blog

This section provides advanced patterns and practical techniques for building admin interfaces with `starlette-admin`. These articles focus on real-world implementations that expand upon the standard reference documentation.

## Publishing a New Post

The Zensical platform currently relies on a manually maintained static index for blog content. To publish a new article, complete the following steps:

1. **Create the content:** Write your post and save the Markdown file within the `blog/posts/` directory.
2. **Update the index:** Add a new row to the **Published Articles** table below, including the publication date and a relative link to your file.
3. **Update the configuration:** Register the new post path in the `zensical.toml` file.

## Published Articles

| Date | Article Title |
| --- | --- |
| 2026-07-13 | [Add an Admin Panel to FastAPI in 5 Minutes with starlette-admin](posts/add-admin-panel-to-fastapi-in-5-minutes.md) |
| 2026-07-10 | [Soft Deletes and a Trash View with FastAPI & starlette-admin](posts/soft-deletes-trash-view.md) |
