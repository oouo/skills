# Java contracts

## Values and API contracts

- Prefer boolean bean fields such as `deleted` for new properties. Before renaming an existing
  `isDeleted` field, check generated accessors, framework bindings, and serialized names.
- Represent exact amounts with `BigDecimal` or the project's integer minor-unit model. Construct
  decimal constants from strings. `new BigDecimal(double)` captures the exact binary floating-point
  value. Use `BigDecimal.valueOf(double)` only when floating input is unavoidable. It cannot
  recover precision lost upstream.
- Use `compareTo() == 0` for numeric decimal equality. Keep `equals()` when scale is part of the
  contract, including existing map keys and set elements. Specify rounding for divisions that
  can yield a non-terminating decimal.
- Compare boxed values of the same numeric type with null-safe value equality. Normalize types
  explicitly for cross-type comparisons. An `Integer` and a `Long` cannot be equal via `equals()`.

```java
BigDecimal expectedAmount = new BigDecimal("0.10");
boolean sameAmount = expectedAmount.compareTo(actualAmount) == 0;
boolean sameOwner = Objects.equals(ownerId, requestedOwnerId);
```

- Keep enum metadata private and final, omit setters, and protect any mutable components.
- Handle expected nulls explicitly. Use empty collections for new APIs when the result means
  “no elements.” Preserve distinctions between absent, unknown, and empty in existing contracts.
- Use `Optional<T>` primarily for return values. Follow framework conventions for fields and
  parameters, and verify compatibility before changing a public signature.

## Collections

- Use `isEmpty()` for element absence. Handle a nullable collection according to its contract.
- Pre-size when an entry-count estimate is meaningful. The integer in `new HashMap<>(capacity)`
  sets the initial capacity. For an expected entry count, use `HashMap.newHashMap(expectedSize)`
  on JDK 19+ or a compatible helper or checked load-factor calculation on older targets.
- Iterate with `entrySet()` or `forEach((key, value) -> ...)` when both are needed. Use `keySet()`
  when only keys are needed. For typed arrays, use `toArray(new String[0])` or, on JDK 11+,
  `toArray(String[]::new)`.
- `Arrays.asList()` is an array-backed, fixed-size list. It supports `set()` but cannot grow or
  shrink. Copy into `new ArrayList<>(source)` when the caller needs a resizable, independent list.
- `subList()` is a backed view that supports the operations allowed by the backing list.
  Its semantics become undefined after a structural change to the backing list outside the view.
  Copy the view when the result needs independent ownership or lifetime.
- For repeated membership queries, weigh a separate `HashSet` against its construction and memory
  costs. Preserve required order, duplicates, and equality semantics in the original data.
  Keep `equals()` and `hashCode()` consistent and stable while elements are indexed.
- Choose ordinary constructors or factories over double-brace initialization. Check the required
  mutability and null support when choosing a factory.

## Text

- Use a local `StringBuilder` for repeated appends in a loop. Keep simple concatenation readable
  and base performance claims on the actual workload.
- `String.split()` takes a regex. Quote a literal delimiter and use a negative limit when
  trailing empty fields matter.

```java
String[] fields = "item|count|".split(Pattern.quote("|"), -1); // ["item", "count", ""]
```

## Concurrency

- Check workload, executor ownership, queue capacity, rejection, and shutdown. Reuse a
  framework-managed executor when its contract fits.
- Give custom platform-thread pools explicit limits, a bounded queue, a deliberate rejection
  policy, and recognizable thread names. Fixed pools may queue without bound. Cached pools may
  create unbounded numbers of threads.
- With virtual-thread executors (JDK 21+), bound access to scarce downstream resources directly,
  for example with a semaphore.
- Scope each `ThreadLocal` to its owner. On reusable threads, remove task-owned values in
  `finally`. For nested scopes, restore the outer value. Choose instance or static ownership
  according to the required lifetime.
- Before using parallel streams, check blocking, ordering, shared state, and context propagation.
  Verify how transaction and `ThreadLocal` state reach parallel workers if the work requires them.

## Language features

| Feature | First stable JDK | Check before use |
| --- | --- | --- |
| Switch expressions | 14 | A switch computes a value clearly. |
| Text blocks | 15 | Verify indentation and the trailing newline in the resulting string. |
| Records and `instanceof` patterns | 16 | Check value-carrier or type-test semantics. |
| Sealed classes and interfaces | 17 | The domain requires a closed set of direct subtypes. |
| Pattern matching for `switch` | 21 | Available only as a preview feature on JDK 17. |

- Cover all switch inputs. Omit a redundant `default` on an exhaustive enum switch and comment
  deliberate fall-through in colon-style switches.
- Records are shallowly immutable. Copy mutable components when ownership must be independent.
  Check framework construction and mutation requirements before converting a persistence entity
  or bean into a record.

## Resources and failures

- Close owned `AutoCloseable` resources with try-with-resources. Leave borrowed resources with
  their owner. For ordinary `Lock` instances, call `unlock()` in `finally` after acquiring the lock.
- Catch failures where the caller can recover, translate, or report them. Preserve causes and
  use broad catches only when required by the boundary's contract. Check catch ordering and
  exception contracts before removing a catch that only rethrows. Explain intentionally ignored
  exceptions where the contract permits them.
- Restore the interrupt flag if you catch `InterruptedException` without propagating it.
- Log a failure once at the responsible boundary using the project logger, the business action,
  key identifiers, and the exception object.

```java
log.error("Order processing failed, orderId={}", orderId, e);
```
