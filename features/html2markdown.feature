Feature: An HTML-to-Markdown converter

  Scenario Outline: Converting extended markdown to HTML
    Given I have a <file base name>,
    When I translate the HTML file to Markdown using antimarkdown
    Then the resulting Markdown should match the corresponding text in the Markdown file.
    
    Examples: Translations
      | file base name                     |
      | basic/amps-and-angle-encoding      |
      | basic/auto-links                   |
      | basic/angle-links-and-img          |
      | basic/blockquotes-with-code-blocks |
      | basic/codeblock-in-list            |

