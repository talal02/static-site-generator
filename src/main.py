import os
import shutil
import sys

from utils import extract_title, markdown_to_html_node


def delete_contents(directory):
	if not os.path.exists(directory):
		return

	for item in os.listdir(directory):
		item_path = os.path.join(directory, item)

		if os.path.isfile(item_path):
			os.remove(item_path)
		else:
			shutil.rmtree(item_path)


def copy_directory(src, dst):
	if not os.path.exists(dst):
		os.makedirs(dst)

	for item in os.listdir(src):
		src_path = os.path.join(src, item)
		dst_path = os.path.join(dst, item)

		if os.path.isfile(src_path):
			print(f"Copying file: {src_path} -> {dst_path}")
			shutil.copy2(src_path, dst_path)
		else:
			print(f"Entering directory: {src_path}")
			copy_directory(src_path, dst_path)


def build_static():
	base_path = os.path.dirname(os.path.dirname(__file__))

	static_dir = os.path.join(base_path, "static")
	docs_dir = os.path.join(base_path, "docs")

	print("Cleaning docs directory...")
	delete_contents(docs_dir)

	print("Copying static → docs...")
	copy_directory(static_dir, docs_dir)


def generate_page(from_path, template_path, dest_path, basepath):
	print(f"Generating page from {from_path} to {dest_path} using {template_path}")

	with open(from_path, "r", encoding="utf-8") as markdown_file:
		markdown = markdown_file.read()

	with open(template_path, "r", encoding="utf-8") as template_file:
		template = template_file.read()

	content = markdown_to_html_node(markdown).to_html()
	title = extract_title(markdown)

	full_html = template.replace("{{ Title }}", title).replace("{{ Content }}", content)
	full_html = full_html.replace('href="/', f'href="{basepath}')
	full_html = full_html.replace('src="/', f'src="{basepath}')

	os.makedirs(os.path.dirname(dest_path), exist_ok=True)

	with open(dest_path, "w", encoding="utf-8") as output_file:
		output_file.write(full_html)


def generate_pages_recursive(dir_path_content, template_path, dest_dir_path, basepath):
	for entry in os.listdir(dir_path_content):
		content_path = os.path.join(dir_path_content, entry)
		dest_path = os.path.join(dest_dir_path, entry)

		if os.path.isdir(content_path):
			generate_pages_recursive(content_path, template_path, dest_path, basepath)
		elif entry.endswith(".md"):
			dest_path = os.path.splitext(dest_path)[0] + ".html"
			generate_page(content_path, template_path, dest_path, basepath)


def main():
	base_path = os.path.dirname(os.path.dirname(__file__))
	basepath = sys.argv[1] if len(sys.argv) > 1 else "/"

	build_static()
	generate_pages_recursive(
		os.path.join(base_path, "content"),
		os.path.join(base_path, "template.html"),
		os.path.join(base_path, "docs"),
		basepath,
	)


if __name__ == "__main__":
	main()
