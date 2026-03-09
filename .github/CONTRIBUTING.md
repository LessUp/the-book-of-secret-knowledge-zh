# 贡献指南

> _然而，一个真正的社区只有在其成员以有意义的方式互动时才存在，这种互动加深了他们对彼此的理解并促进了学习。_

如果你想支持这个项目，对如何改进这个工具有一个有趣的想法，或者你发现了一些错误——请 fork 本项目，添加你的修复，然后将你的分支的 pull request 提交到 **master 分支**。

## 使用问题跟踪器

[问题跟踪器](https://github.com/trimstray/the-book-of-secret-knowledge/issues) 是报告错误、功能请求和提交 pull request 的首选渠道，但请遵守以下限制：

*   请**不要**使用问题跟踪器来请求个人支持（请使用 [Stack Overflow](https://stackoverflow.com) 或 IRC）。
*   请**不要**在问题中进行无端攻击或引战。请保持讨论的重点，并尊重他人的意见。

## 关于中文翻译项目的贡献

本仓库是 `the-book-of-secret-knowledge` 的中文翻译版本。我们欢迎并感谢所有针对翻译内容（例如：修正错别字、改进译文流畅度、统一术语等）的贡献。

如果您希望对翻译做出贡献，请直接向本仓库提交 Pull Request。

对于原始内容的补充、修正或技术性的贡献（例如，添加新的工具链接、修复失效链接等），我们建议您向[英文原项目](https://github.com/trimstray/the-book-of-secret-knowledge)提交。这将确保所有语言版本都能从您的贡献中受益。

## 如何查找失效链接？

您可以使用以下脚本来帮助查找 `README.md` 中的失效链接。这对于维护项目质量非常有帮助。

```bash
git clone https://github.com/trimstray/the-book-of-secret-knowledge-zh && cd the-book-of-secret-knowledge-zh

for i in $(sed -n 's/.*href="\([^"]*\).*/\1/p' README.md | grep -v "^#") ; do

  _rcode=$(curl -s -o /dev/null -w "%{http_code}" "$i")

  if [[ "$_rcode" != "2"* ]] ; then echo " -> $i - $_rcode" ; fi

done
```

结果示例：

```bash
 -> https://ghostproject.fr/ - 503
 -> http://www.mmnt.net/ - 302
 -> https://search.weleakinfo.com/ - 503
 [...]
``` 