# make-photo-album-zine

一个自包含的手帐风照片相册 Skill。上传照片后，它会按色调和视觉氛围分类，自动完成页面规划、背景构建、照片排版、页面渲染与 PDF 装订。

## 设计原则

- 人像和含人物照片默认保持原图，不重绘、不美化、不换背景、不生成式修改。
- 只允许景物和物品照片提供配色、背景元素、贴纸或可选风格化版本。
- 默认每页 3–4 张照片，完整保留画面比例，不裁切、不拉伸、不互相重叠。
- 每页背景从照片主色、辅助色和可辨认的非人物元素中提取，使用 2–4 层低干扰装饰。
- 贴纸只来源于景物或物品，放在照片边缘和页面留白区，不遮挡人物与重要内容。
- 不调用或依赖其他照片风格 Skill。

## 输出

- 整册相册 PDF
- 每页独立 PNG
- 页面分组与照片使用清单
- 满足素材条件时生成透明贴纸 PNG

## 使用方式

将仓库作为 Skill 安装到支持 `SKILL.md` 的环境，然后上传照片并输入：

```text
使用 $make-photo-album-zine 生成整册相册，按照片色调分类，每页 3–4 张，人像保持原图。
```

如果要求所有照片完全不处理，可明确输入：

```text
所有照片仅排版，不处理照片内容。
```

## 工作流程

1. 识别人像、混合场景、景物和物品。
2. 提取每张照片的确定性色板。
3. 按主色调、明暗和视觉连续性分组。
4. 生成每页 3–4 张照片的非重叠版面计划。
5. 使用照片来源色和非人物元素构建手帐背景与贴纸。
6. 将原始照片确定性合成到页面。
7. 校验照片完整性、页面数量和人物保护规则。
8. 输出页面 PNG，并按顺序装订为 PDF。

## 目录

```text
SKILL.md
agents/openai.yaml
assets/icon.svg
references/album-blueprint.md
references/scrapbook-design-system.md
scripts/extract_palette.py
scripts/validate_album_plan.py
scripts/compose_album_pages.py
scripts/assemble_album.py
```

## 运行依赖

- Python 3.10+
- Pillow
- pypdf，用于额外核对 PDF 页数
- Poppler，用于最终 PDF 页面渲染与视觉检查

安装 Python 依赖：

```bash
python3 -m pip install -r requirements.txt
```

## 本地校验

```bash
python3 scripts/extract_palette.py --self-test
python3 scripts/validate_album_plan.py --self-test
python3 scripts/compose_album_pages.py --self-test
python3 scripts/assemble_album.py --self-test
```

当前版本已经过 19 张混合照片前向测试：共生成 5 页，页面照片数为 `4+4+4+4+3`，所有含人物照片均保持原始内容。
