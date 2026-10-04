import re
def analyze(contents):
 return {"types":sorted({x for t in contents.values() for x in re.findall(r"(?:interface|type)\s+([A-Za-z0-9_]+)",t)}),"mock_data":[p for p,t in contents.items() if re.search(r"mock|fixture|fake",p,re.I) or re.search(r"mockData|dummyData",t,re.I)]}
