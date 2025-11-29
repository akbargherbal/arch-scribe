## Cell 1 (code) [no output] [1]

```python
#
```

## Cell 2 (code) [no output] [2]

```python
import pandas as pd
import regex as re
import os
from pathlib import Path
import json
```

## Cell 3 (code) [no output] [3]

```python
with open('./PROMPT_TEMPLATE.md', encoding='utf-8') as f:
    prompt_template = f.read()
```

## Cell 4 (code) [no output] [4]

```python
list_docs = []
for root, dirs, files in os.walk('./DOCS/'):
    for file in files:
        if file.endswith('.md'):
            list_docs.append(os.path.join(root, file).replace(os.sep, '/'))

list_placeholders = re.findall(r'\[.*?_PLACEHOLDER.*?\]', prompt_template)
```

## Cell 5 (code) [7]

```python
# Automatically map placeholders to document paths with assertions
dict_docs_placeholders = {}

for placeholder in list_placeholders:
    # Skip CHAPTER_JSON_PLACEHOLDER (not a document)
    if 'CHAPTER_JSON' in placeholder:
        continue
    
    # Extract the filename from placeholder: [DOC_MASTER_SUMMARY_PLACEHOLDER] -> DOC_MASTER_SUMMARY
    filename = placeholder.strip('[]').replace('_PLACEHOLDER', '')
    
    # Search for matching file in list_docs
    matched = False
    for doc_path in list_docs:
        if filename in Path(doc_path).stem:
            dict_docs_placeholders[placeholder] = doc_path
            matched = True
            break
    
    # Assert that we found a match
    assert matched, f"No document found for placeholder: {placeholder} (looking for: {filename})"

# Assert we have exactly 7 document mappings (excluding CHAPTER_JSON_PLACEHOLDER)
assert len(dict_docs_placeholders) == 7, f"Expected 7 documents, found {len(dict_docs_placeholders)}"

# Assert all mapped files exist
for placeholder, doc_path in dict_docs_placeholders.items():
    assert os.path.exists(doc_path), f"File not found: {doc_path} for {placeholder}"

print("✓ All assertions passed!")
print(f"✓ Mapped {len(dict_docs_placeholders)} documents successfully")
dict_docs_placeholders
```

**Output (stream):**
```text
✓ All assertions passed!
✓ Mapped 7 documents successfully
```

**Result:**
```text
{'[DOC_MASTER_SUMMARY_PLACEHOLDER]': './DOCS/DOC_MASTER_SUMMARY_PLACEHOLDER.md',
 '[DOC_SESSION_7_PLACEHOLDER]': './DOCS/DOC_SESSION_7_PLACEHOLDER.md',
 '[DOC_SESSION_9_PLACEHOLDER]': './DOCS/DOC_SESSION_9_PLACEHOLDER.md',
 '[DOC_INCEPTION_PLACEHOLDER]': './DOCS/DOC_INCEPTION_PLACEHOLDER.md',
 '[DOC_SWOT_PLACEHOLDER]': './DOCS/DOC_SWOT_PLACEHOLDER.md',
 '[DOC_FEEDBACK_PLACEHOLDER]': './DOCS/DOC_FEEDBACK_PLACEHOLDER.md',
 '[DOC_GITLOG_PLACEHOLDER]': './DOCS/DOC_GITLOG_PLACEHOLDER.md'}
```

## Cell 6 (code) [no output] [ ]

```python
def create_prompt(part_json_data, prompt_template, dict_docs_placeholders):
    "Complete this function the way you see necessary - it takes a single part json and return the prompt for that part " 
    pass
```

