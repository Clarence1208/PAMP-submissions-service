# Sample Markdown Document

This is a comprehensive example of Markdown syntax demonstrating various features and formatting options.

## Table of Contents

- [Headers](#headers)
- [Text Formatting](#text-formatting)
- [Lists](#lists)
- [Links and Images](#links-and-images)
- [Code](#code)
- [Tables](#tables)
- [Blockquotes](#blockquotes)
- [Mathematical Expressions](#mathematical-expressions)

## Headers

# Header 1
## Header 2
### Header 3
#### Header 4
##### Header 5
###### Header 6

Alternative header syntax:

Header 1
========

Header 2
--------

## Text Formatting

**Bold text** or __bold text__

*Italic text* or _italic text_

***Bold and italic*** or ___bold and italic___

~~Strikethrough text~~

`Inline code`

Subscript: H~2~O

Superscript: x^2^

==Highlighted text==

> **Note:** Some extensions like highlights, subscript, and superscript may not be supported in all Markdown processors.

## Lists

### Unordered Lists

- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
    - Deeply nested item 2.2.1
- Item 3

Alternative syntax:

* Item A
* Item B
  + Nested item B.1
  + Nested item B.2

### Ordered Lists

1. First item
2. Second item
   1. Nested item 2.1
   2. Nested item 2.2
3. Third item

### Task Lists

- [x] Completed task
- [ ] Incomplete task
- [x] Another completed task
  - [x] Nested completed task
  - [ ] Nested incomplete task

## Links and Images

### Links

[Inline link](https://www.example.com)

[Link with title](https://www.example.com "Example Website")

[Reference link][ref-link]

[Another reference link][1]

<https://www.example.com>

<email@example.com>

### Images

![Alt text](https://via.placeholder.com/300x200 "Image Title")

![Reference image][image-ref]

## Code

### Inline Code

Use `console.log()` to output to the console in JavaScript.

### Code Blocks

```javascript
// JavaScript example
function greet(name) {
    return `Hello, ${name}!`;
}

const people = ['Alice', 'Bob', 'Charlie'];
people.forEach(person => {
    console.log(greet(person));
});
```

```python
# Python example
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Generate first 10 Fibonacci numbers
fib_numbers = [fibonacci(i) for i in range(10)]
print(fib_numbers)
```

```sql
-- SQL example
SELECT u.name, u.email, COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON u.id = p.author_id
WHERE u.active = true
GROUP BY u.id, u.name, u.email
ORDER BY post_count DESC
LIMIT 10;
```

## Tables

| Name    | Age | Occupation   | Location      |
|---------|-----|--------------|---------------|
| Alice   | 30  | Developer    | San Francisco |
| Bob     | 25  | Designer     | New York      |
| Charlie | 35  | Manager      | London        |

### Table with Alignment

| Left Aligned | Center Aligned | Right Aligned |
|:-------------|:--------------:|--------------:|
| Left         |     Center     |         Right |
| Text         |     Text       |          Text |

## Blockquotes

> This is a blockquote.
> 
> It can span multiple lines and paragraphs.

> **Nested blockquotes:**
> 
> > This is a nested blockquote.
> > 
> > > And this is even more nested.

## Horizontal Rules

---

***

___

## Mathematical Expressions

Inline math: $E = mc^2$

Block math:

$$
\sum_{i=1}^{n} x_i = x_1 + x_2 + \cdots + x_n
$$

$$
\int_{a}^{b} f(x) \, dx = F(b) - F(a)
$$

## HTML Elements

Markdown also supports <em>HTML elements</em> for additional formatting.

<details>
<summary>Click to expand</summary>

This content is hidden by default and can be expanded by clicking the summary.

</details>

<kbd>Ctrl</kbd> + <kbd>C</kbd> to copy

<mark>Highlighted text using HTML</mark>

## Footnotes

Here's a sentence with a footnote[^1].

This is another footnote[^note].

## Emojis

:smile: :heart: :rocket: :computer: :books:

## Escape Characters

Use backslashes to escape special characters:

\*Not italic\*

\`Not code\`

\[Not a link\]

## Line Breaks

To create a line break, end a line with two spaces  
or use a blank line.

This is a new paragraph.

---

## References

[ref-link]: https://www.example.com "Reference Link"
[1]: https://www.another-example.com
[image-ref]: https://via.placeholder.com/150x100 "Reference Image"

[^1]: This is the first footnote.
[^note]: This is another footnote with a custom identifier.

---

**Document created:** January 15, 2024  
**Last updated:** January 15, 2024  
**Author:** Sample Author  
**Version:** 1.0 