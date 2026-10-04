from app.utils.token_budget import fit_context,estimate_tokens
def generate(analysis,max_bytes):
 lines=["# Baton Repository Context","",f"Stack: {', '.join(analysis.get('stack',{}).get('detected',[]))}","", "## File tree"]+[f"- {x.get('path')} ({x.get('type')})" for x in analysis.get("file_tree",[])]
 for k in ("routes","api_calls","environment_variables","handoffs","important_files"): lines += [f"\n## {k.replace('_',' ').title()}"]+[f"- {x}" for x in analysis.get(k,[])]
 text=fit_context("\n".join(lines),max_bytes); return {"markdown":text,"estimated_tokens":estimate_tokens(text)}
