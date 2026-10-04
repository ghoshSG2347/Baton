import re
def analyze(contents):
 out=[]
 for path,text in contents.items():
  if re.search(r"handoff|TODO|FIXME",text,re.I): out.append({"path":path,"items":[x.strip() for x in text.splitlines() if re.search(r"handoff|TODO|FIXME",x,re.I)]})
 return out
