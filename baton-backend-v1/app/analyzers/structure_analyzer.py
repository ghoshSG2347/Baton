def analyze(files):
 return {"file_tree":files,"important_files":[x["path"] for x in files if x["path"].split("/")[-1] in {"package.json","requirements.txt","pyproject.toml","README.md","main.py","App.tsx","App.jsx"}]}
