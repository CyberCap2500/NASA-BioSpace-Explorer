import os
import ast
from typing import List

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DOWNLOAD_PY = os.path.join(PROJECT_ROOT, 'download.py')
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'pmc_urls.txt')


def extract_article_links(py_path: str) -> List[str]:
    with open(py_path, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source, filename=py_path)
    urls: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'article_links':
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                urls.append(elt.value.strip())
    return urls


def main() -> None:
    urls = extract_article_links(DOWNLOAD_PY)
    if not urls:
        print('No URLs found in download.py article_links.')
        return
    # Deduplicate preserving order
    seen = set()
    unique_urls: List[str] = []
    for u in urls:
        if u and u not in seen:
            unique_urls.append(u)
            seen.add(u)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for u in unique_urls:
            f.write(u + '\n')
    print(f'Wrote {len(unique_urls)} URLs to {OUTPUT_FILE}')


if __name__ == '__main__':
    main()


