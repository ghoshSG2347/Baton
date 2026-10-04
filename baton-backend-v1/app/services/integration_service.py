def compare(frontend,backend):
 fr=set(frontend.get("routes",[])); br=set(backend.get("routes",[])); return {"frontend_routes":sorted(fr),"backend_routes":sorted(br),"unmatched_frontend_routes":sorted(fr-br),"unmatched_backend_routes":sorted(br-fr),"compatible":fr==br}
