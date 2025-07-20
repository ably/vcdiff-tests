#!/usr/bin/env python3
"""
Generator for general-positive VCDIFF tests.
Creates base files and their variants with ~25% modifications.
"""

import os
import json
import random
import string
import subprocess
from pathlib import Path

def generate_random_bytes(size):
    """Generate random bytes of specified size."""
    return bytes([random.randint(0, 255) for _ in range(size)])

def generate_random_json(target_size):
    """Generate random but valid JSON of approximately target_size bytes."""
    data = {}
    current_size = 0
    counter = 0
    
    # Add various JSON structures until we reach target size
    while current_size < target_size * 0.9:  # Leave some room for final structure
        key = f"key_{counter}"
        
        # Choose random data type
        choice = random.choice(['string', 'number', 'boolean', 'array', 'object'])
        
        if choice == 'string':
            length = min(50, target_size - current_size - 20)
            if length > 0:
                value = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))
                data[key] = value
        elif choice == 'number':
            data[key] = random.randint(0, 1000000)
        elif choice == 'boolean':
            data[key] = random.choice([True, False])
        elif choice == 'array':
            arr_size = random.randint(1, 10)
            data[key] = [random.randint(0, 100) for _ in range(arr_size)]
        elif choice == 'object':
            nested = {}
            for i in range(random.randint(1, 5)):
                nested[f"nested_{i}"] = ''.join(random.choices(string.ascii_letters, k=10))
            data[key] = nested
        
        current_size = len(json.dumps(data))
        counter += 1
        
        # Safety break
        if counter > 1000:
            break
    
    return json.dumps(data, indent=2)

def create_base_files():
    """Create all base files."""
    base_files = {}
    
    # Random byte files
    base_files['64_bytes_random'] = generate_random_bytes(64)
    base_files['1024_bytes_random'] = generate_random_bytes(1024)
    base_files['64k_bytes_random'] = generate_random_bytes(65536)
    
    # JSON files
    base_files['1k_json_random'] = generate_random_json(1024).encode('utf-8')
    base_files['64k_json_random'] = generate_random_json(65536).encode('utf-8')
    
    return base_files

def modify_binary_append(data):
    """Append ~25% random data."""
    append_size = len(data) // 4
    append_data = generate_random_bytes(append_size)
    return data + append_data

def modify_binary_delete(data):
    """Delete ~25% of data at random offset."""
    if len(data) < 4:
        return data[:len(data)//2]  # Delete half if too small
    
    delete_size = len(data) // 4
    start_pos = random.randint(0, len(data) - delete_size)
    return data[:start_pos] + data[start_pos + delete_size:]

def modify_binary_insert(data):
    """Insert ~25% random data at random offset."""
    insert_size = len(data) // 4
    insert_pos = random.randint(0, len(data))
    insert_data = generate_random_bytes(insert_size)
    return data[:insert_pos] + insert_data + data[insert_pos:]

def modify_binary_modify(data):
    """Modify ~25% of data in-place."""
    modify_size = len(data) // 4
    start_pos = random.randint(0, len(data) - modify_size)
    new_data = generate_random_bytes(modify_size)
    return data[:start_pos] + new_data + data[start_pos + modify_size:]

def modify_json_append(json_str):
    """Append new JSON properties."""
    try:
        data = json.loads(json_str)
        original_size = len(json_str)
        target_addition = original_size // 4
        
        counter = len(data)
        while len(json.dumps(data, indent=2)) < original_size + target_addition * 0.8:
            new_key = f"appended_key_{counter}"
            data[new_key] = ''.join(random.choices(string.ascii_letters, k=20))
            counter += 1
            if counter > 50:  # Safety break
                break
        
        return json.dumps(data, indent=2).encode('utf-8')
    except:
        return json_str.encode('utf-8') if isinstance(json_str, str) else json_str

def modify_json_delete(json_str):
    """Delete ~25% of JSON properties."""
    try:
        data = json.loads(json_str)
        keys = list(data.keys())
        delete_count = max(1, len(keys) // 4)
        
        keys_to_delete = random.sample(keys, min(delete_count, len(keys)))
        for key in keys_to_delete:
            del data[key]
        
        return json.dumps(data, indent=2).encode('utf-8')
    except:
        return json_str.encode('utf-8') if isinstance(json_str, str) else json_str

def modify_json_insert(json_str):
    """Insert new JSON properties at various positions."""
    try:
        data = json.loads(json_str)
        original_size = len(json_str)
        target_addition = original_size // 4
        
        # Insert new properties
        counter = len(data)
        while len(json.dumps(data, indent=2)) < original_size + target_addition * 0.8:
            new_key = f"inserted_key_{counter}"
            data[new_key] = {
                'value': random.randint(0, 1000),
                'text': ''.join(random.choices(string.ascii_letters, k=15))
            }
            counter += 1
            if counter > 50:  # Safety break
                break
        
        return json.dumps(data, indent=2).encode('utf-8')
    except:
        return json_str.encode('utf-8') if isinstance(json_str, str) else json_str

def modify_json_modify(json_str):
    """Modify ~25% of JSON values while preserving structure."""
    try:
        data = json.loads(json_str)
        keys = list(data.keys())
        modify_count = max(1, len(keys) // 4)
        
        keys_to_modify = random.sample(keys, min(modify_count, len(keys)))
        for key in keys_to_modify:
            if isinstance(data[key], str):
                data[key] = ''.join(random.choices(string.ascii_letters, k=len(data[key])))
            elif isinstance(data[key], int):
                data[key] = random.randint(0, 1000000)
            elif isinstance(data[key], bool):
                data[key] = not data[key]
            elif isinstance(data[key], list):
                if data[key]:
                    data[key][0] = random.randint(0, 1000) if data[key] else []
        
        return json.dumps(data, indent=2).encode('utf-8')
    except:
        return json_str.encode('utf-8') if isinstance(json_str, str) else json_str

def create_test_case(base_name, base_data, variant_name, modified_data):
    """Create a test case directory with all required files."""
    test_name = f"{base_name}_{variant_name}"
    test_dir = Path("general-positive") / test_name
    test_dir.mkdir(exist_ok=True)
    
    # Write source and target files
    source_path = test_dir / "source"
    target_path = test_dir / "target"
    delta_path = test_dir / "delta.vcdiff"
    
    with open(source_path, "wb") as f:
        f.write(base_data)
    
    with open(target_path, "wb") as f:
        f.write(modified_data)
    
    # Generate delta using xdelta3
    try:
        subprocess.run([
            "xdelta3", "-A", "-S", "-s", str(source_path), str(target_path), str(delta_path)
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate delta for {test_name}: {e}")
        return False
    
    # Create metadata
    metadata = {
        "description": f"General positive test: {base_name} with {variant_name} modification",
        "source_description": f"Base file: {base_name}",
        "target_description": f"Modified with {variant_name} (~25% change)",
        "delta_description": f"VCDIFF delta for {variant_name} modification",
        "test_type": "general_positive",
        "base_file_type": "json" if "json" in base_name else "binary",
        "modification_type": variant_name,
        "base_size": len(base_data),
        "target_size": len(modified_data)
    }
    
    metadata_path = test_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return True

def main():
    """Generate all general-positive test cases."""
    random.seed(42)  # For reproducible results
    
    print("Generating base files...")
    base_files = create_base_files()
    
    modifications = {
        'append': {
            'binary': modify_binary_append,
            'json': modify_json_append
        },
        'delete': {
            'binary': modify_binary_delete, 
            'json': modify_json_delete
        },
        'insert': {
            'binary': modify_binary_insert,
            'json': modify_json_insert
        },
        'modify': {
            'binary': modify_binary_modify,
            'json': modify_json_modify
        }
    }
    
    test_count = 0
    failed_count = 0
    
    for base_name, base_data in base_files.items():
        is_json = 'json' in base_name
        file_type = 'json' if is_json else 'binary'
        
        print(f"Processing {base_name} ({len(base_data)} bytes)...")
        
        for variant_name, mod_funcs in modifications.items():
            mod_func = mod_funcs[file_type]
            
            if is_json:
                # Convert bytes to string for JSON processing
                json_str = base_data.decode('utf-8')
                modified_data = mod_func(json_str)
            else:
                modified_data = mod_func(base_data)
            
            print(f"  Creating {variant_name} variant...")
            if create_test_case(base_name, base_data, variant_name, modified_data):
                test_count += 1
            else:
                failed_count += 1
    
    print(f"\nGenerated {test_count} test cases successfully")
    if failed_count > 0:
        print(f"Failed to generate {failed_count} test cases")

if __name__ == "__main__":
    main()