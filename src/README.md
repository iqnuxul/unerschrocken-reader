# 精读页源文件

- `template.html`：精读页模板（明文，句子数据已清空）
- `build.py`：把一章的数据套进模板，生成明文页面
- `data/money-kapitel*.js`：小狗钱钱各章数据

## 数据格式

```js
const PAGE_TITLES = { 25: "四点钟的约定", ... };   // 每页的中文小标题
const data = [
[页码, "德语原句", "中文翻译", [["词条", "释义"], ...], "<b>语法点</b>：讲解"],
...
];
```

## 新增一章

```bash
python3 src/build.py src/data/money-kapitel3.js /tmp/money3.html "第 3 章 · Daryl, der Junge, der viel Geld verdient" money3
npx staticrypt@3.5.4 /tmp/money3.html -p money --short --remember false -d .   # 生成加密的 money3.html
```

然后在 `money-index.html` 里把第 3 章那行从 `<div class="ch off">…待更新…</div>` 改成 `<a class="ch" href="money3.html">…开始读 →</a>`。
