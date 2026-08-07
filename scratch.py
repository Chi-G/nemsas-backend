import yaml
with open('.github/workflows/deploy.yml', 'r') as f:
    try:
        yaml.safe_load(f)
        print("YAML is valid!")
    except Exception as e:
        print(f"YAML ERROR: {e}")
