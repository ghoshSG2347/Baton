from app.utils.text_utils import language_for
def analyze(files):
 names={x["path"] for x in files}; stack=[]
 if any(p.endswith((".tsx",".jsx")) for p in names): stack.append("React")
 if any(p.endswith(".ts") for p in names): stack.append("TypeScript")
 if any(p.endswith(".py") for p in names): stack.append("Python")
 if any(p.endswith("requirements.txt") for p in names): stack.append("Python dependencies")
 if any(p.endswith("package.json") for p in names): stack.append("Node.js")
 return {"detected":stack,"languages":sorted({language_for(p) for p in names if language_for(p)})}
