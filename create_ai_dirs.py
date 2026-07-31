import os

base_dir = "/home/vicky/Documents/investai/AI"
dirs = [
    "agents/clusters",
    "services",
    "training",
    "prediction",
    "rag",
    "learning",
    "models"
]

for d in dirs:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)
    
# Create __init__.py files
init_dirs = [
    "",
    "agents",
    "agents/clusters",
    "services",
    "training",
    "prediction",
    "rag",
    "learning"
]
for d in init_dirs:
    with open(os.path.join(base_dir, d, "__init__.py"), "w") as f:
        pass
        
with open(os.path.join(base_dir, "models", ".gitkeep"), "w") as f:
    pass

print("Directories created.")
