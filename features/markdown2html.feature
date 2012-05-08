Feature: The results of the HTML-to-Markdown converter reverse back to HTML.

  @markdown
  Scenario Outline: Converting markdown to HTML
    Given I have a <file base name>,
    When I translate the Markdown file to HTML using markdown
    Then the resulting HTML should match the corresponding text in the Markdown file.
    
  Examples: Basic scenarios
    | file base name                        |
    | basic/amps-and-angle-encoding         |
    | basic/auto-links                      |
    | basic/angle-links-and-img             |
    | basic/blockquotes-with-code-blocks    |
    | basic/codeblock-in-list               |
    | basic/horizontal-rules                |
    | basic/inline-html-simple              |
    | basic/inline-html-advanced            |
    | basic/inline-html-comments            |
    | basic/links-inline                    |
    | basic/literal-quotes                  |
    | basic/markdown-documentation-basics   |
    | basic/markdown-syntax                 |
    | basic/nested-blockquotes              |
    | basic/ordered-and-unordered-list      |
    | basic/strong-and-em-together          |
    | basic/tabs                            |
    | basic/tidyness                        |
    | misc/adjacent-headers                 |
    | misc/amp-in-url                       |
    | misc/ampersand                        |
    | misc/arabic                           |
    | misc/autolinks_with_asterisks_russian |
    | misc/autolinks_with_asterisks         |
    | misc/backtick-escape                  |
    | misc/bidi                             |
    | misc/blank-block-quote                |
    | misc/blockquote-below-paragraph       |
    | misc/blockquote-hr                    |
    | misc/blockquote                       |
    | misc/bold_links                       |
    | misc/br                               |
    | misc/code-first-line                  |
    | misc/em_strong                        |
    | misc/em-around-links                  |
    | misc/email                            |
    | misc/escaped_links                    |
    | misc/headers                          |
    | misc/image_in_links                   |
    | misc/image-2                          |
    | misc/image                            |
    | misc/japanese                         |
    | misc/link-with-parenthesis            |
    | misc/lists                            |
    | misc/lists4                           |
    | misc/lists5                           |
    | misc/lists7                           |
    | misc/lists8                           |
    | misc/nested-lists                     |
    | misc/nested-patterns                  |
