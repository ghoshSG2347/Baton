import re
def language_for(path:str)->str|None:
    ext=path.rsplit(".",1)[-1].lower() if "." in path.rsplit("/",1)[-1] else ""
    return {"py":"python","js":"javascript","jsx":"javascript","ts":"typescript","tsx":"typescript","json":"json","md":"markdown","css":"css","html":"html","yaml":"yaml","yml":"yaml","toml":"toml"}.get(ext)
def extract_lines(text:str, pattern:str)->list[str]: return [line.strip() for line in text.splitlines() if re.search(pattern,line,re.I)]
def truncate(text:str, limit:int)->str: return text if len(text)<=limit else text[:limit]+"\n...[truncated]"
