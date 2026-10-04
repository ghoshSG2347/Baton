from app.generators.prompt_generator import generate
def create(req): return {"prompt":generate(req.task,req.context,req.constraints)}
