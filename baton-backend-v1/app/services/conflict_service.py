def detect(files,branches):
 owners={}; conflicts=[]
 for branch,paths in branches.items():
  for p in paths: owners.setdefault(p,[]).append(branch)
 for path,bs in owners.items():
  if len(bs)>1: conflicts.append({"path":path,"branches":bs,"reason":"shared file changed by multiple branches"})
 return {"conflicts":conflicts,"conflict_count":len(conflicts)}
