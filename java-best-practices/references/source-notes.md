# Sources and Interpretation

Reviewed on 2026-11-03. Use these notes for attribution and source conflicts; apply the workflow
in `SKILL.md` for coding tasks.

## Source Scope

- **Google Java Style Guide:** use the living guide for style and declaration conventions.
  Relevant sections include [constant names][constants], [type-use annotations][annotations],
  [overloads][overloads], [switches][switches], [overrides][overrides], and [Javadoc][javadoc].
- **Alibaba Java Development Manual, Taishan / Huangshan editions
  (《阿里巴巴 Java 开发手册（泰山版/黄山版）》):** use this handbook family as the reference
  framework for defensive programming. Find the handbook in the [official P3C repository][handbook].
- **Alibaba Cloud, "Quickly Learn How You Can Improve Your Java Coding":** use the
  [supplied article][article], published on April 10, 2020, as companion practical reading.
  Attribute examples inspected there to the article; consult the relevant handbook edition
  before making edition-specific or full-compliance claims.
- **JDK documentation:** use version-specific API contracts and language specifications for
  correctness. Modern language and virtual-thread guidance are later supplements to the article.

## Interpretation Decisions

- The article's emptiness wording conflates null references with empty collections. The
  [Collection contract][collection] defines element absence and promises no universal O(1) cost.
  Its empty-return examples also show empty arrays/collections despite the misleading heading.
- [HashSet][hashset] conditions constant-time operations on hash dispersion and preserves no
  iteration order. Treat membership indexing as a workload-dependent choice.
- Retain parentheses that clarify grouping; [Google section 4.7][parentheses] supports them.
  Do not apply the article's parentheses-removal suggestion as a blanket rewrite.
- Check reflection, framework bindings, and API compatibility before adopting the article's
  unused-member cleanup suggestions. Keep that cleanup within the requested scope.
- The text-splitting guidance also uses the [String contract][string] and [Pattern API][pattern]
  for literal delimiters and trailing-empty-field handling.

[constants]: https://google.github.io/styleguide/javaguide.html#s5.2.4-constant-names
[annotations]: https://google.github.io/styleguide/javaguide.html#s4.8.5.1-type-use-annotation-style
[overloads]: https://google.github.io/styleguide/javaguide.html#s3.4.2.1-overloads-never-split
[switches]: https://google.github.io/styleguide/javaguide.html#s4.8.4-switch
[overrides]: https://google.github.io/styleguide/javaguide.html#s6.1-override-annotation
[javadoc]: https://google.github.io/styleguide/javaguide.html#s7.3-javadoc-where-required
[parentheses]: https://google.github.io/styleguide/javaguide.html#s4.7-grouping-parentheses
[collection]: https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Collection.html
[hashset]: https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/HashSet.html
[string]: https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/String.html
[pattern]: https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/regex/Pattern.html
[handbook]: https://github.com/alibaba/p3c
[article]: https://www.alibabacloud.com/blog/quickly-learn-how-you-can-improve-your-java-coding_596101
