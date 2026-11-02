"""Допоміжні засоби для заповнення шаблонів документів DOCX."""

from __future__ import annotations

import html
import re
import zipfile
from pathlib import Path
from typing import Mapping
from xml.sax.saxutils import escape


_TEXT_NODE_RE = re.compile(r"(<w:t\b[^>]*>)(.*?)(</w:t>)", re.DOTALL)
_PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def _replace_placeholders(xml: str, replacements: Mapping[str, str]) -> str:
	"""Замінює плейсхолдери, навіть якщо Word розділив їх між вузлами w:t."""
	nodes = list(_TEXT_NODE_RE.finditer(xml))
	if not nodes:
		return xml

	texts = [html.unescape(match.group(2)) for match in nodes]
	document_text = "".join(texts)
	matches = list(_PLACEHOLDER_RE.finditer(document_text))
	if not matches:
		return xml

	offsets = []
	offset = 0
	for text in texts:
		offsets.append((offset, offset + len(text)))
		offset += len(text)

	for match in reversed(matches):
		replacement = str(replacements.get(match.group(1), match.group(0)))
		start_node = next(i for i, (_, end) in enumerate(offsets) if match.start() < end)
		end_node = next(i for i, (start, end) in enumerate(offsets) if match.end() <= end and match.end() > start)
		start_offset = match.start() - offsets[start_node][0]
		end_offset = match.end() - offsets[end_node][0]
		if start_node == end_node:
			texts[start_node] = texts[start_node][:start_offset] + replacement + texts[start_node][end_offset:]
		else:
			texts[start_node] = texts[start_node][:start_offset] + replacement
			for node_index in range(start_node + 1, end_node):
				texts[node_index] = ""
			texts[end_node] = texts[end_node][end_offset:]

	result = []
	last_end = 0
	for match, text in zip(nodes, texts):
		result.append(xml[last_end:match.start()])
		result.append(match.group(1) + escape(text) + match.group(3))
		last_end = match.end()
	result.append(xml[last_end:])
	return "".join(result)


def _replace_leader_role(xml: str, role: str) -> str:
	"""Замінює фіксовану назву посади керівника у блоці підписів."""
	role_genitive = {"Директор": "директора", "Декан": "декана"}.get(role, role.lower())
	xml = re.sub(
		r"(<w:t\b[^>]*>)(.*?)(Декан)(.*?</w:t>)",
		rf"\1\2{escape(role)}\4",
		xml,
		flags=re.DOTALL,
	)
	return re.sub(
		r"(<w:t\b[^>]*>)(.*?)(декана)(.*?</w:t>)",
		rf"\1\2{escape(role_genitive)}\4",
		xml,
		flags=re.DOTALL,
	)


def fill_docx_template(
	template_path: str | Path,
	output_path: str | Path,
	replacements: Mapping[str, str],
) -> Path:
	"""Створює заповнений DOCX-документ і повертає шлях до нього."""
	template = Path(template_path)
	output = Path(output_path)
	if template.suffix.lower() != ".docx":
		raise ValueError("Автоматичне заповнення підтримує лише файли .docx")
	if not template.is_file():
		raise FileNotFoundError(f"Шаблон не знайдено: {template}")

	with zipfile.ZipFile(template, "r") as source, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
		for item in source.infolist():
			data = source.read(item.filename)
			if item.filename.startswith("word/") and item.filename.endswith(".xml"):
				xml = _replace_placeholders(data.decode("utf-8"), replacements)
				xml = _replace_leader_role(xml, str(replacements.get("FACULTY_HEAD_ROLE", "Декан")))
				data = xml.encode("utf-8")
			target.writestr(item, data)
	return output
