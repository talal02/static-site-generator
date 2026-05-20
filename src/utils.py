import re
from enum import Enum

from htmlnode import HTMLNode, LeafNode, ParentNode
from textnode import TextNode, TextType

class BlockType(Enum):
    PARAGRAPH = "p"
    HEADING = "h1"
    CODE = "pre"
    QUOTE = "blockquote"
    UNORDERED_LIST = "ul"
    ORDERED_LIST = "ol"


def text_node_to_html_node(text_node: TextNode):
  match text_node.text_type:
    case TextType.TEXT:
      return LeafNode(value=text_node.text)
    case TextType.BOLD:
      return LeafNode(tag="b", value=text_node.text)
    case TextType.ITALIC:
      return LeafNode(tag="i", value=text_node.text)
    case TextType.CODE:
      return LeafNode(tag="code", value=text_node.text)
    case TextType.LINK:
      return LeafNode(tag="a", value=text_node.text, props={"href": text_node.url})
    case TextType.IMAGE:
      return LeafNode(tag="img", props={"src": text_node.url, "alt": text_node.text})
    case _:
      raise ValueError(f"Unsupported TextType: {text_node.text_type}")


def split_nodes_delimiter(old_nodes, delimiter, text_type):
    new_nodes = []

    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue

        parts = node.text.split(delimiter)

        if len(parts) % 2 == 0:
            raise Exception(f"Invalid markdown syntax: unmatched {delimiter}")

        for i, part in enumerate(parts):
            if part == "":
                continue

            if i % 2 == 0:
                new_nodes.append(TextNode(part, TextType.TEXT))
            else:
                new_nodes.append(TextNode(part, text_type))

    return new_nodes
  
  
def extract_markdown_images(text):
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = re.findall(pattern, text)
    images = []
    for alt_text, url in matches:
        images.append((alt_text, url))
    return images


def extract_markdown_links(text):
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, text)
    links = []
    for link_text, url in matches:
        links.append((link_text, url))
    return links


def split_nodes_image(old_nodes):
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        text = node.text
        images = extract_markdown_images(text)
        if not images:
            new_nodes.append(node)
            continue
        for alt_text, url in images:
            sections = text.split(f"![{alt_text}]({url})", 1)
            if len(sections) != 2:
                raise Exception("Invalid markdown image syntax")
            if sections[0]:
                new_nodes.append(TextNode(sections[0], TextType.TEXT))
            new_nodes.append(TextNode(alt_text, TextType.IMAGE, url))
            text = sections[1]
        if text:
            new_nodes.append(TextNode(text, TextType.TEXT))
    return new_nodes


def split_nodes_link(old_nodes):
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        text = node.text
        links = extract_markdown_links(text)
        if not links:
            new_nodes.append(node)
            continue
        for link_text, url in links:
            sections = text.split(f"[{link_text}]({url})", 1)
            if len(sections) != 2:
                raise Exception("Invalid markdown link syntax")
            if sections[0]:
                new_nodes.append(TextNode(sections[0], TextType.TEXT))
            new_nodes.append(TextNode(link_text, TextType.LINK, url))
            text = sections[1]
        if text:
            new_nodes.append(TextNode(text, TextType.TEXT))
    return new_nodes


def text_to_textnodes(text):
    nodes = [TextNode(text, TextType.TEXT)]
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    return nodes


def markdown_to_blocks(markdown):
    raw_blocks = markdown.split("\n\n")

    blocks = []

    for block in raw_blocks:
        block = block.strip()

        if not block:
            continue

        lines = block.split("\n")
        cleaned_lines = [line.strip() for line in lines]

        blocks.append("\n".join(cleaned_lines))

    return blocks
  
def block_to_block_type(block):
    if block.startswith("# "):
        return BlockType.HEADING
    elif block.startswith(">"):
        return BlockType.QUOTE
    elif block.startswith("- "):
        return BlockType.UNORDERED_LIST
    elif re.match(r'^\d+\. ', block):
        return BlockType.ORDERED_LIST
    elif block.startswith("```") and block.endswith("```"):
        return BlockType.CODE
    else:
        return BlockType.PARAGRAPH
      

def markdown_to_html_node(markdown):
    blocks = markdown_to_blocks(markdown)
    children = []

    for block in blocks:
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", block)

        if heading_match:
            heading_level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            children.append(
                ParentNode(
                    tag=f"h{heading_level}",
                    children=[
                        text_node_to_html_node(tn)
                        for tn in text_to_textnodes(heading_text)
                    ],
                )
            )
            continue

        block_type = block_to_block_type(block)

        if block_type == BlockType.CODE:
            lines = block.split("\n")
            code_lines = lines[1:-1]
            cleaned_lines = [line.rstrip("\r") for line in code_lines]

            code_text = "\n".join(cleaned_lines) + "\n"

            code_node = ParentNode(
                tag="code",
                children=[
                    text_node_to_html_node(
                        TextNode(code_text, TextType.TEXT)
                    )
                ],
            )

            children.append(
                ParentNode(tag="pre", children=[code_node])
            )
            continue
        if block_type == BlockType.UNORDERED_LIST:
            list_items = []
            for line in block.split("\n"):
                item_text = line[2:].strip()
                list_items.append(
                    ParentNode(
                        tag="li",
                        children=[
                            text_node_to_html_node(tn)
                            for tn in text_to_textnodes(item_text)
                        ],
                    )
                )

            children.append(ParentNode(tag="ul", children=list_items))
            continue
        if block_type == BlockType.ORDERED_LIST:
            list_items = []
            for line in block.split("\n"):
                item_text = re.sub(r"^\d+\. ", "", line).strip()
                list_items.append(
                    ParentNode(
                        tag="li",
                        children=[
                            text_node_to_html_node(tn)
                            for tn in text_to_textnodes(item_text)
                        ],
                    )
                )

            children.append(ParentNode(tag="ol", children=list_items))
            continue
        if block_type == BlockType.QUOTE:
            quote_lines = [
                line.lstrip("> ").strip()
                for line in block.split("\n")
            ]
            quote_text = " ".join(line for line in quote_lines if line)
            children.append(
                ParentNode(
                    tag="blockquote",
                    children=[
                        text_node_to_html_node(tn)
                        for tn in text_to_textnodes(quote_text)
                    ],
                )
            )
            continue
        if block_type == BlockType.PARAGRAPH:
            block = " ".join(block.split())

        text_nodes = text_to_textnodes(block)

        html_children = [
            text_node_to_html_node(tn) for tn in text_nodes
        ]

        children.append(
            ParentNode(
                tag=block_type.value,
                children=html_children,
            )
        )

    return ParentNode("div", children)


def extract_title(markdown):
    for line in markdown.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("# ") and not stripped_line.startswith("##"):
            return stripped_line[1:].strip()

    raise Exception("No h1 header found in markdown")