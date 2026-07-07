import os
import ast
import sys

root = r"d:\GEO\backend"
targets = [
    "geo_core/schemas/business.py",
    "geo_core/services/scenario_service.py",
    "geo_core/services/strategy_service.py",
    "geo_core/services/diagnosis_service.py",
    "geo_core/services/content_service.py",
    "geo_core/services/publish_service.py",
    "geo_core/services/dashboard_service.py",
    "geo_core/api/v1/onboarding.py",
    "geo_core/api/v1/diagnosis.py",
    "geo_core/api/v1/strategy_pack.py",
    "geo_core/api/v1/content.py",
    "geo_core/api/v1/publish.py",
    "geo_core/api/v1/monitoring.py",
    "geo_core/api/v1/outcomes.py",
    "geo_core/api/v1/agent.py",
]

problems = []

for rel in targets:
    path = os.path.join(root, rel)
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    try:
        tree = ast.parse(src, filename=rel)
    except SyntaxError as e:
        problems.append(f"{rel}: syntax {e}")
        continue
    # check imports resolve-ish
    import_names = set()
    func_names = set()
    class_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                import_names.add(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                import_names.add(node.module)
        elif isinstance(node, ast.FunctionDef):
            func_names.add(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            func_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            class_names.add(node.name)
    print(f"  AST OK {rel:55s} classes={len(class_names)} funcs={len(func_names)} imports={len(import_names)}")

if problems:
    print("\nPROBLEMS:")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("\nAll targets pass AST parsing.")
