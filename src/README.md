# 图书馆源文件

```
src/
├── site.py          生成器：书架、目录页、章节精读页
├── template.html    精读页模板（句子数据已清空）
└── books/
    └── <书的文件夹>/
        ├── book.json             书的信息
        └── kapitel1.js …         各章数据（也可命名为 money_ch1_data.js）
```

推到 `main` 后，GitHub Actions（「发布图书馆」）会自动：
生成并加密改动过的章节 → 在目录页点亮章节 → 更新书架首页 → 提交。

## 加一章

把数据文件放进对应书的文件夹，文件名 `kapitel5.js` 或 `money_ch5_data.js`（数字是章节号），推送即可。

数据格式：

```js
// Ein Hund namens Money — Kapitel 5: Moneys früherer Besitzer (S. 63–72)
const PAGE_TITLES = { 63: "这一页的中文小标题", ... };
const data = [
[页码, "德语原句", "中文翻译", [["词条", "释义"], ...], "<b>语法点</b>：讲解"],
...
];
```

## 加一本书

新建文件夹 `src/books/<英文短名>/`，放 `book.json`：

```json
{
  "month": "2027-03",
  "zh": "毛毛",
  "title": "Momo",
  "author": "Michael Ende",
  "tag": "奇幻小说",
  "note": "书架卡片上的一句话简介",
  "color": "#c26a1b",
  "cover": "img/momo.png",
  "prefix": "momo",
  "password_secret": "BOOK_PASSWORD",
  "speak_word": "Momo",
  "chapters": [
    {"de": "Kapitel 1 德语标题", "zh": "中文标题", "page": 7}
  ]
}
```

- `month` 决定书架上的年份和月份；`cover` 可省略，会自动用 `color` 做纯色封面。
- `prefix` 决定页面文件名：目录 `momo-index.html`，章节 `momo1.html`、`momo2.html`…
- `chapters` 可以先写空列表 `[]`，有数据的章节会自动出现在目录里。
- `password_secret` 是密码的 Secret 名。在仓库 **Settings → Secrets and variables → Actions** 里添加同名 Secret。
  现有：`MONEY_PASSWORD`（小狗钱钱）；其他书默认用 `BOOK_PASSWORD`。

## 本地运行

```bash
python3 src/site.py pages                                   # 只更新书架和目录页
MONEY_PASSWORD=... python3 src/site.py build src/books/money/kapitel3.js
```
