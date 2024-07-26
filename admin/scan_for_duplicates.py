import os
import hashlib
import pathlib
import re
from os import DirEntry
from typing import List, Dict, Optional



def get_file_hash(file_path: DirEntry[str], chunk_size: int=2 * 1024 * 1024):
    """Compute SHA-256 hash of a file. If the file is larger than 2MB, only the first 2MB is hashed."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read the first 1MB or the whole file if it's smaller
        data = f.read(chunk_size)
        hash_sha256.update(data)
    return hash_sha256.hexdigest()

def handle_duplicates(file1: DirEntry[str], file2: DirEntry[str], file_hash: str):
    name1, _ = os.path.splitext(file1.name)
    name2, _ = os.path.splitext(file2.name)
    print(f"{name1} and {name2}")
    if name1[0:6] == "photo_" and name2[0:6] == "photo_":
        print("**************PHOTO***************")
        print(file1)
        os.unlink(file1)

    name_to_del = delete_lower_number_extension(name1, name2) or delete_lower_number_extension(name2, name1)
    if name_to_del == name1:
        print(f"Deleting {name1}")
        os.unlink(file1)
    elif name_to_del == name2:
        print(f"Deleting {name2}")
        os.unlink(file2)



def delete_lower_number_extension(name1: str, name2: str) -> Optional[str]:
    # Try to match documents like '1abq2325b083aW.mp4' '1abq2325b083aW (2).mp4'
    name_re = re.compile(r"^(.+) \(([0-9]+)\)$")
    match1 = re.match(name_re, name1)
    if not match1:
        return None
    else:
        basename = match1.group(1)
        if name2 == basename:
            # name2 has no number at the end
            return name1
        match2 = re.match(name_re, name2)
        if not match2:
            return None
        if match2.group(1) == basename:
            if int(match1.group(2)) > int(match2.group(2)):
                return name2
            else:
                return name1




def find_duplicates(directory: str):
    """Find and print duplicates in the specified directory."""
    files_by_size: Dict[int, List[DirEntry[str]]] = {}
    duplicates: List[str] = []
    n = 0


    raise NotImplementedError("Implement better handling of favorites please!")
    # Group files by their size
    for item in os.scandir(directory):
        if not item.is_file():
            continue
        n += 1
        try:
            file_size = os.path.getsize(item)
            if file_size in files_by_size:
                files_by_size[file_size].append(item)
            else:
                files_by_size[file_size] = [item]
        except OSError as e:
            print(f"Error accessing {item}: {e}")

    # Compare files with the same size using SHA-256
    d = 0
    for _, same_size_files in files_by_size.items():
        if len(same_size_files) > 1:
            hashes: Dict[str, DirEntry[str]] = {}
            for file in same_size_files:
                try:
                    file_hash = get_file_hash(file)
                    if file_hash in hashes:
                        d += 1
                        handle_duplicates(file, hashes[file_hash], file_hash)
                        break
                    else:
                        hashes[file_hash] = file
                except OSError as e:
                    print(f"Error hashing {file}: {e}")

    # Print duplicates
    print(f"Scanned {n} files.")
    print(f"{d} duplicates found.")

# Example usage
directory_path = '/home/abrahams/apps/TG-Collector/static/media'
find_duplicates(directory_path)
