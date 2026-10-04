import re
def analyze(contents):
 routes=[]; api_calls=[]; env=[]
 for path,text in contents.items():
  routes += [f"{path}: {x.strip()}" for x in re.findall(r"(?:app|router)\.(?:get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)",text,re.I)]
  api_calls += [f"{path}: {x}" for x in re.findall(r"(?:fetch|axios\.(?:get|post|put|patch|delete))\s*\(\s*['\"]([^'\"]+)",text,re.I)]
  env += re.findall(r"(?:process\.env\.([A-Z0-9_]+)|os\.environ(?:_get)?\(\s*['\"]([A-Z0-9_]+))",text)
 return {"routes":routes,"api_calls":api_calls,"environment_variables":sorted({a or b for a,b in env})}
