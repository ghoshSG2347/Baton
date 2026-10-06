def detect(files,branches):
 owners={}; conflicts=[]
 for branch,paths in branches.items():
  for p in set(paths): owners.setdefault(p,[]).append(branch)
 for path,bs in owners.items():
  if len(bs)>1: conflicts.append({"path":path,"branches":bs,"reason":"File present in multiple branch inventories; changes and merge conflicts have not been established."})
 return {"conflicts":conflicts,"conflict_count":len(conflicts)}
