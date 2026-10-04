from app.generators.context_generator import generate
def test_context(): assert "Baton Repository Context" in generate({"stack":{"detected":[]},"file_tree":[]},1000)["markdown"]
