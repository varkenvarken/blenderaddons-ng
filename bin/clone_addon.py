import sys
import os
import re

def to_snake_case(name):
    # Converts 'My New Addon' -> 'my_new_addon'
    name = name.strip()
    name = re.sub(r'[\s\-]+', '_', name)
    return name.lower()

def to_title_case(name):
    # Converts 'my new addon' -> 'My New Addon'
    return ' '.join(word.capitalize() for word in name.strip().split())

def main():
    if len(sys.argv) != 2:
        print("Usage: python clone_addon.py \"My New Addon\"")
        sys.exit(1)

    new_name = sys.argv[1]
    snake_name = to_snake_case(new_name)
    title_name = to_title_case(new_name)

    source = 'add_ons/example_simple.py'
    dest = f'add_ons/{snake_name}.py'

    if not os.path.exists(source):
        print(f"Source file {source} does not exist.")
        sys.exit(1)

    with open(source, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace all relevant names and identifiers
    # 1. UI/Menu: Move X -> Title Name
    content = re.sub(r"\bMove X\b", title_name, content)
    # 2. UI/Menu: move_x (lowercase) -> snake_name
    content = re.sub(r"\bmove_x\b", snake_name, content)
    # 3. Class names: OBJECT_OT_move_x -> OBJECT_OT_{snake_name}
    content = re.sub(r"\bOBJECT_OT_move_x\b", f"OBJECT_OT_{snake_name}", content)
    # 4. Operator idname: object.move_x -> object.{snake_name}
    content = re.sub(r"\bobject\.move_x\b", f"object.{snake_name}", content)
    # 5. OPERATOR_NAME variable
    content = re.sub(r'OPERATOR_NAME: str = OBJECT_OT_[a-zA-Z0-9_]+', f'OPERATOR_NAME: str = OBJECT_OT_{snake_name}', content)

    with open(dest, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Created {dest}")

if __name__ == '__main__':
    main()
  
