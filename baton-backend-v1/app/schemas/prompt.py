from pydantic import BaseModel
class PromptRequest(BaseModel): task: str; context: str = ""; constraints: list[str] = []
