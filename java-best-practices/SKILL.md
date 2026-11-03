---
name: java-best-practices
description: >-
  Use when writing, modifying, refactoring, debugging, or reviewing Java source
  or tests, including tasks involving .java files even when Java is not named.
  Covers Google Java formatting, defensive coding, collections, concurrency,
  resource safety, and version-compatible language features.
  Skip non-Java and build-only tasks without Java code work.
---

# Java Best Practices

## Overview

Use the **Google Java Style Guide** and the **Alibaba Java Development Manual
(Taishan / Huangshan editions)** as the reference framework for style and defensive programming.
Use the linked Alibaba Cloud article as companion reading for practical examples.
Preserve project contracts and target-JDK compatibility while improving correctness and readability.

## When to Use

- Apply to Java implementation, refactoring, tests, code review, and source-level debugging.
  Infer the language from relevant files and code when the request omits it.
- Apply to concrete questions about Java value semantics, collections, or concurrency.
- Accept explicit invocation by skill name or the client's skill picker.
- Skip JavaScript/TypeScript work and documentation, dependency, or deployment tasks that do not
  involve Java source behavior. A Java repository alone is not a reason to activate this skill.

## Instructions

### 1. Establish the Project Baseline

- Read applicable repository instructions and nearby code before choosing a pattern.
- Check the target module's compiler release, source level, toolchain, and runtime requirements
  in its Maven or Gradle configuration. The installed JDK alone does not establish compatibility.
- Follow established framework, serialization, nullability, and public API contracts.
  Keep review-only tasks read-only and limit implementation changes to the requested behavior.
- Verify unfamiliar APIs against documentation for the project's actual version.
  Use modern features only when the configured release supports them; do not assume JDK 17+,
  raise the release level, or enable preview features merely to satisfy this skill.

### 2. Format and Structure the Code

- Run the repository's configured `google-java-format` task or its pinned formatter on changed
  Java code. Let the formatter choose wrapping instead of manually aligning every chain call.
- Use Google Style's 100-column limit, two-space block indentation, K&R braces, explicit imports,
  and braces around control-flow bodies. Follow the formatter's documented exceptions.
- Use conventional Java modifier order and uppercase `L` for long literals. Reserve
  `UPPER_SNAKE_CASE` for deeply immutable `static final` constants; keep mutable `static final`
  objects and loggers in `lowerCamelCase`.
- Keep overloads and constructors grouped logically. Add `@Override` where legal and qualify static
  members with their class rather than an instance. Keep type-use annotations with the annotated type.
- Document public/protected API contracts with Javadoc, including units, nullability, and
  boundaries. Reuse inherited documentation and omit redundant descriptions of obvious accessors.
- Handle invalid or exceptional cases with early returns or continues. Split independent business
  steps into action-named methods and give calculations meaningful intermediate names.
- Explain business rules, units, sentinel values, and non-obvious boundaries in comments using the
  project's comment language and English half-width punctuation.

### 3. Preserve Naming and Value Semantics

- Prefer boolean property names such as `deleted` for new bean fields. Check generated accessors
  and framework mappings before renaming existing `isDeleted` fields; serialized names are contracts.
- Represent exact decimal values with `BigDecimal` or an established integer minor-unit model.
  Construct decimal constants from strings, avoiding `new BigDecimal(double)` for decimal intent.
  Use `BigDecimal.valueOf(double)` only when a floating
  input is unavoidable; it cannot recover precision already lost in previous calculations.
- Use `compareTo() == 0` for numeric decimal equality. Retain `equals()` when scale is intentionally
  part of equality, including existing map-key or set semantics. Specify rounding for divisions
  that can produce non-terminating decimal results.
- Compare boxed numeric values with null-safe value equality, such as `Objects.equals(a, b)`,
  when both operands have the same intended wrapper type. Normalize types explicitly when comparing
  different numeric representations; `Integer` and `Long` do not become equal through `equals()`.
- Name business thresholds and sentinel values. Keep enum metadata private and final, without
  setters; protect mutable components from modification as well.
- Handle expected nulls explicitly instead of catching `NullPointerException` as normal control flow.

```java
BigDecimal expectedAmount = new BigDecimal("0.10");
boolean sameAmount = expectedAmount.compareTo(actualAmount) == 0;
boolean sameOwner = Objects.equals(ownerId, requestedOwnerId);
```

### 4. Use Collections According to Their Contracts

- Use `isEmpty()` for emptiness and handle nullable references according to the API contract.
- Pre-size collections when a meaningful size estimate is available. Distinguish `HashMap` bucket
  capacity from expected entry count. Use `HashMap.newHashMap(expectedSize)` only on JDK 19+;
  use an existing compatible helper or a checked load-factor calculation on older targets.
- Use `entrySet()` or `forEach((key, value) -> ...)` when both keys and values are needed.
  Use `keySet()` when only keys are needed.
- Convert collections to typed arrays with `toArray(new String[0])`, or an array constructor
  such as `toArray(String[]::new)` on JDK 11+. Choose based on compatibility and clarity.
- Treat `Arrays.asList()` as a fixed-size, array-backed list: `set()` is supported, structural
  changes are not. Copy into `new ArrayList<>(source)` when an independently resizable list is needed.
- Treat `subList()` as a backed view. Changes through the view are allowed when the backing list
  supports them; structural changes to the backing list outside the view make its semantics undefined.
  Copy the view when independent ownership or lifetime is required.
- Consider a separate `HashSet` for repeated membership queries when construction and memory costs
  are justified. Preserve required order, duplicates, and equality semantics in the original data;
  ensure element `equals()` and `hashCode()` agree and remain stable while indexed.
- Initialize collections with ordinary constructors or compatible factories instead of double-brace
  anonymous subclasses. Preserve required mutability and null support when choosing a factory.

### 5. Handle Text Deliberately

- Use a local `StringBuilder` when repeatedly appending to an accumulated string in a loop.
  Keep simple concatenation readable; substantiate performance claims with the actual workload.
- Treat `String.split()` delimiters as regular expressions. Use `Pattern.quote()` for a literal
  delimiter, and a negative limit when trailing empty fields are significant.

```java
String row = "item|count|";
String[] fields = row.split(Pattern.quote("|"), -1);
```

The resulting fields are `"item"`, `"count"`, and `""`.

### 6. Bound Concurrency and Respect Ownership

- Inspect workload, executor ownership, queue capacity, rejection handling, and shutdown behavior.
  Reuse framework-managed executors when appropriate.
- For custom platform-thread pools, configure `ThreadPoolExecutor` with explicit limits, a bounded
  queue, an intentional rejection policy, and business-relevant thread names. Assess factory methods
  individually: fixed pools can queue without bound, while cached pools can grow threads without bound.
- Treat JDK 21+ virtual-thread executors separately. Bound access to scarce downstream resources
  with mechanisms such as semaphores; virtual threads do not remove resource limits.
- Scope `ThreadLocal` values to their owner. Remove task-owned values in `finally` on reusable
  threads; restore an outer value when nested scopes require it. Choose static or instance ownership
  deliberately rather than requiring every `ThreadLocal` to be static.
- Use parallel streams only after checking blocking behavior, ordering, shared state, and context
  propagation. Do not assume transaction or `ThreadLocal` state follows parallel work.

### 7. Adopt Compatible Language Features

| Feature | Stable baseline | Apply when |
| --- | --- | --- |
| Switch expressions | JDK 14 | A switch computes a value clearly. |
| Text blocks | JDK 15 | Multiline text benefits; verify indentation and trailing newline behavior. |
| Records and `instanceof` patterns | JDK 16 | A value carrier or type test fits existing contracts. |
| Sealed classes/interfaces | JDK 17 | A deliberately closed hierarchy models the domain. |
| Pattern matching for `switch` | JDK 21 | Type-pattern branches improve clarity; JDK 17 support is preview. |

- Cover all switch inputs; omit a redundant `default` when enum cases are already exhaustive.
  Comment deliberate fall-through in colon-style switches.
- Prefer records for suitable new value carriers after checking framework support. Records provide
  shallow immutability: defensively copy mutable components when immutable ownership is required.
  Keep persistence entities and models requiring mutable bean semantics in compatible class forms.
- Use empty collections for new APIs where "no elements" is the result. Preserve existing distinctions
  between absent, unknown, and empty values when they are part of the contract.
- Use `Optional<T>` primarily for return values that model absence. Keep fields and parameters in
  the project's established form, and verify framework support before changing a public signature.

### 8. Manage Resources and Report Failures

- Use try-with-resources for owned `AutoCloseable` resources. Keep borrowed resources open for their
  owner; ordinary `Lock` instances require `unlock()` in `finally` after successful acquisition.
- Catch exceptions at a boundary that can recover, translate, or report them. Use broad catches
  only when the boundary's contract requires them; preserve causes. Remove redundant catch-only-rethrow
  blocks only after checking catch ordering and exception contracts. Explain intentionally ignored
  exceptions when the contract permits ignoring them.
- Restore the interrupt flag when catching `InterruptedException` without propagating it.
- Log the failed business action and key identifiers with the exception object. Use the project's
  logging framework rather than `printStackTrace()` or message-only exception logging.

```java
try {
  processOrder(orderId);
} catch (OrderProcessingException e) {
  log.error("Order processing failed, orderId={}", orderId, e);
  throw e;
}
```

Log at the responsible boundary; avoid logging and rethrowing at every layer.

### 9. Verify and Deliver

- Run the relevant configured formatter, targeted compilation/tests, and applicable static checks
  for implementation changes. Derive commands from the repository; report checks that could not run.
- Recheck changed boundaries: nulls, numeric precision, collection ownership, concurrency, and
  framework compatibility where relevant to the task.
- For reviews, report concrete findings as **location -> failure condition and impact -> repair**.
  Separate enforceable style rules from correctness defects; avoid claiming a bug without a trigger.
- Summarize the change, observed verification results, and remaining limits in the user's language.

## References

Read [source notes](references/source-notes.md) when checking provenance or reconciling advice.
Use the relevant JDK documentation to settle API semantics and compatibility:

- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- [Alibaba Java Development Manual](https://github.com/alibaba/p3c), Taishan / Huangshan editions
  (《阿里巴巴 Java 开发手册（泰山版/黄山版）》)
- [Alibaba Cloud Java coding article][alibaba-article] (April 10, 2020), companion practical reading
- [Java 17 API](https://docs.oracle.com/en/java/javase/17/docs/api/index.html)
- [Java 21 language updates](https://docs.oracle.com/en/java/javase/21/language/java-language-changes.html)

[alibaba-article]: https://www.alibabacloud.com/blog/quickly-learn-how-you-can-improve-your-java-coding_596101
