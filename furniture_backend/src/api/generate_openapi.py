import json
import os

from src.api.main import app

# Generate and write the OpenAPI schema to interfaces/openapi.json
def main() -> None:
    schema = app.openapi()
    output_dir = "interfaces"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "openapi.json")
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"Wrote OpenAPI schema to {output_path}")


if __name__ == "__main__":
    main()
