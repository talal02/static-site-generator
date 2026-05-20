import unittest
from textnode import TextNode, TextType
from utils import text_node_to_html_node, split_nodes_delimiter, extract_markdown_images, split_nodes_image, text_to_textnodes, markdown_to_blocks, block_to_block_type, BlockType, markdown_to_html_node, extract_title

class TestUtils(unittest.TestCase):
    def test_text(self):
      node = TextNode("This is a text node", TextType.TEXT)
      html_node = text_node_to_html_node(node)
      self.assertEqual(html_node.tag, None)
      self.assertEqual(html_node.value, "This is a text node")
      
    def test_split_nodes_delimiter(self):
      nodes = [
        TextNode("This is text with a **bolded phrase** in the middle", TextType.TEXT)
      ]
      new_nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
      self.assertEqual(len(new_nodes), 3)
      self.assertEqual(new_nodes[0].text, "This is text with a ")
      self.assertEqual(new_nodes[0].text_type, TextType.TEXT)
      self.assertEqual(new_nodes[1].text, "bolded phrase")
      self.assertEqual(new_nodes[1].text_type, TextType.BOLD)
      self.assertEqual(new_nodes[2].text, " in the middle")
      self.assertEqual(new_nodes[2].text_type, TextType.TEXT)
            
    def test_extract_markdown_images(self):
        matches = extract_markdown_images(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png)"
        )
        self.assertListEqual([("image", "https://i.imgur.com/zjjcJKZ.png")], matches)  

    def test_split_images(self):
        node = TextNode(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png) and another ![second image](https://i.imgur.com/3elNhQu.png)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("This is text with an ", TextType.TEXT),
                TextNode("image", TextType.IMAGE, "https://i.imgur.com/zjjcJKZ.png"),
                TextNode(" and another ", TextType.TEXT),
                TextNode(
                    "second image", TextType.IMAGE, "https://i.imgur.com/3elNhQu.png"
                ),
            ],
            new_nodes,
        )
        
    def test_text_to_textnodes(self):
      text = "This is **text** with an _italic_ word and a `code block` and an ![obi wan image](https://i.imgur.com/fJRm4Vk.jpeg) and a [link](https://boot.dev)"
      expected_nodes = [
          TextNode("This is ", TextType.TEXT),
          TextNode("text", TextType.BOLD),
          TextNode(" with an ", TextType.TEXT),
          TextNode("italic", TextType.ITALIC),
          TextNode(" word and a ", TextType.TEXT),
          TextNode("code block", TextType.CODE),
          TextNode(" and an ", TextType.TEXT),
          TextNode("obi wan image", TextType.IMAGE, "https://i.imgur.com/fJRm4Vk.jpeg"),
          TextNode(" and a ", TextType.TEXT),
          TextNode("link", TextType.LINK, "https://boot.dev"),
      ]
      actual_nodes = text_to_textnodes(text)
      self.assertEqual(expected_nodes, actual_nodes)
      
      
    def test_markdown_to_blocks(self):
        md = """
          This is **bolded** paragraph

          This is another paragraph with _italic_ text and `code` here
          This is the same paragraph on a new line

          - This is a list
          - with items
        """
        blocks = markdown_to_blocks(md)
        self.assertEqual(
            blocks,
            [
                "This is **bolded** paragraph",
                "This is another paragraph with _italic_ text and `code` here\nThis is the same paragraph on a new line",
                "- This is a list\n- with items",
            ],
        )
        
    def test_block_to_block_type(self):
        self.assertEqual(block_to_block_type("This is a paragraph"), BlockType.PARAGRAPH)
        self.assertEqual(block_to_block_type("# This is a heading"), BlockType.HEADING)
        self.assertEqual(block_to_block_type("```\nThis is code\n```"), BlockType.CODE)
        self.assertEqual(block_to_block_type("> This is a quote"), BlockType.QUOTE)
        self.assertEqual(block_to_block_type("- Item 1\n- Item 2"), BlockType.UNORDERED_LIST)
        self.assertEqual(block_to_block_type("1. Item 1\n2. Item 2"), BlockType.ORDERED_LIST)
        
    def test_paragraphs(self):
        md = """
          This is **bolded** paragraph
          text in a p
          tag here

          This is another paragraph with _italic_ text and `code` here

        """

        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><p>This is <b>bolded</b> paragraph text in a p tag here</p><p>This is another paragraph with <i>italic</i> text and <code>code</code> here</p></div>",
        )

    def test_codeblock(self):
        md = """
          ```
          This is text that _should_ remain
          the **same** even with inline stuff
          ```
        """

        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><pre><code>This is text that _should_ remain\nthe **same** even with inline stuff\n</code></pre></div>",
        )

    def test_quote_and_lists(self):
        md = """
          > A quote line
          > another quote line

          - first item
          - second item

          1. alpha
          2. beta
        """

        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><blockquote>A quote line another quote line</blockquote><ul><li>first item</li><li>second item</li></ul><ol><li>alpha</li><li>beta</li></ol></div>",
        )

    def test_extract_title(self):
        self.assertEqual(extract_title("# Hello"), "Hello")
        self.assertEqual(extract_title("  #   Hello World  \n\nParagraph"), "Hello World")

    def test_extract_title_missing(self):
        with self.assertRaises(Exception):
            extract_title("## No title here\nJust text")