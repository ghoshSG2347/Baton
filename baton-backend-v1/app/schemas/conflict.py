from pydantic import BaseModel
class ConflictRequest(BaseModel): files: list[str] = []; branches: dict[str,list[str]] = {}
