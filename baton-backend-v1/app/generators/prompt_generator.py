def generate(task,context="",constraints=None):
 constraints=constraints or []; extra="\n".join(f"- {x}" for x in constraints)
 return f"You are working on the Baton repository.\n\nTask:\n{task}\n\nConstraints:\n{extra}\n\nRepository context:\n{context}"
