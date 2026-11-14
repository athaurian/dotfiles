# prettier-math regression corpus

This directory contains the regression test suite for `prettier-math`, a
Prettier wrapper that prevents formatting changes inside math formulas.

## The Prettier bug

Starting in Prettier 3.9.9, the Markdown formatter parses inline math as regular
text ([issue #20199](https://github.com/prettier/prettier/issues/20199)). When a
paragraph contains multiple formulas with asterisks or underscores, Prettier
treats those characters as emphasis markers and rewrites them:

| Before                | After                 |
| --------------------- | --------------------- |
| `$x^*$ and $y^*$`     | `$x^_$ and $y^_$`     |
| `$x^{*}$ and $y^{*}$` | `$x^{_}$ and $y^{_}$` |
| `$x_*$ and $y_*$`     | `$x__$ and $y__$`     |

Prettier requires two markers to form an emphasis pair:

- **One formula in a paragraph:** A single `$x^*$` has only one asterisk and
  remains unchanged.
- **Two formulas in a paragraph:** Two formulas provide a pair of markers, which
  triggers the rewrite shown in the table above.

## How the wrapper works

1. Replaces each math formula with a placeholder before running Prettier.
2. Runs Prettier on the document.
3. Restores the original formulas.

## Test suite design

- **One construct per file:** Each Markdown file tests a single math construct
  so that a test failure points to one exact cause.
- **Full Markdown formatting:** Running Prettier on complete Markdown files
  verifies that surrounding paragraph formatting does not corrupt the restored
  formulas.
- **Span comparison:** The test runner extracts every formula before and after
  formatting and asserts that they match. Any file without a detected formula
  fails by default so that typos or empty files cannot pass silently.

## Supported syntax and limits

| Syntax       | Delimiter | Line breaks         | Wrapper behavior                                                                                         |
| ------------ | --------- | ------------------- | -------------------------------------------------------------------------------------------------------- |
| Inline math  | `$...$`   | Single line only    | Matches up to a line break. Formulas that cross a line break are ignored and remain exposed to Prettier. |
| Display math | `$$...$$` | Multiline supported | Matches across line breaks as a single block.                                                            |

## Intentional exceptions

Three test files contain no valid formulas. Because there are no formula spans
to compare, the test runner allowlists these files by name and asserts that the
entire file remains unchanged:

1. **Escaped dollars (`\$`):** Literal text that must stay literal.
2. **Unclosed inline math (`$`):** Invalid math that must not receive a closing
   `$`.
3. **Unclosed display math (`$$`):** Invalid math that must not receive a
   closing `$$`.
