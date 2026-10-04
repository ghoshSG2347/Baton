from app.services.conflict_service import detect
def test_conflict(): assert detect([],{"a":["x"],"b":["x"]})["conflict_count"]==1
