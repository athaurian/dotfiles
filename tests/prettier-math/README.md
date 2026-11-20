# prettier-math regression corpus

This directory contains the regression test suite for `prettier-math`, a
Prettier wrapper that prevents formatting changes inside math formulas.

## The Prettier bug

| Property          | Value                                                                       |
| :---------------- | :-------------------------------------------------------------------------- |
| Affected release  | Starting in 3.9.9                                                           |
| Upstream report   | [issue #20199](https://github.com/prettier/prettier/issues/20199)           |

The Markdown formatter parses inline math as regular text. When a paragraph
contains multiple formulas with asterisks or underscores, Prettier treats those
characters as emphasis markers and rewrites them:

| Before                | After                 |
| --------------------- | --------------------- |
| `$x^*$ and $y^*$`     | `$x^_$ and $y^_$`     |
| `$x^{*}$ and $y^{*}$` | `$x^{_}$ and $y^{_}$` |
| `$x_*$ and $y_*$`     | `$x__$ and $y__$`     |

Prettier requires two markers to form an emphasis pair:

- **One emphasis marker in a paragraph:** A paragraph containing `$x^*$` has
  only one asterisk. No pair can be formed, and the formula remains unchanged.
- **Two or more markers in a paragraph:** Prettier pairs the markers across the
  paragraph, whether they occur in one formula or in several, and applies the
  rewrite shown in the table above.

## Wrapper operation

The wrapper protects formulas in three steps:

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

Three corpus files contain no closed math span. Because there are no formula
spans to compare, the runner allowlists them by name and asserts that each file
remains unchanged:

| File                     | Construct                                             |
| :----------------------- | :---------------------------------------------------- |
| `29-escaped-dollar.md`   | Escaped dollars: literal text that must stay literal   |
| `33-unclosed.md`         | Unclosed inline math: no closing `$` should be added  |
| `43-display-unclosed.md` | Unclosed display math: no closing `$$` should be added |
