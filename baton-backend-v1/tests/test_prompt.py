from app.generators.prompt_generator import generate
def test_prompt(): assert "Fix the route" in generate("Fix the route")
