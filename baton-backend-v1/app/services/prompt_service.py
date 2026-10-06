from app.generators.prompt_generator import generate
def create(req): return {"prompt": 'Provenance: USER_PROVIDED. This manual prompt is not verified repository evidence.\n\n' + generate(req.task,req.context,req.constraints,repository=req.repository)}
