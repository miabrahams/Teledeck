import os
import hashlib
import pathlib

def get_file_hash(file_path, chunk_size=1024 * 1024):
    """Compute SHA-256 hash of a file. If the file is larger than 1MB, only the first 1MB is hashed."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read the first 1MB or the whole file if it's smaller
        data = f.read(chunk_size)
        hash_sha256.update(data)
    return hash_sha256.hexdigest()

def handle_duplicates(file1, file2, file_hash):
    name1, ext1 = os.path.splitext(file1.name)
    name2, ext2 = os.path.splitext(file2.name)
    print(f"{name1} and {name2}")
    if name1[0:6] == "photo_" and name2[0:6] == "photo_":
        print("**************PHOTO***************")
        print(file1)
        os.unlink(file1)

    if name1 == (name2 + " (4)"):
        print("**************ONE***************")
        os.unlink(file1)
    elif name2 == name1 + " (4)":
        print("**************TWO***************")
        os.unlink(file2)



def find_duplicates(directory):
    """Find and print duplicates in the specified directory."""
    files_by_size = {}
    duplicates = []
    n = 0

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
    for size, same_size_files in files_by_size.items():
        if len(same_size_files) > 1:
            hashes = {}
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
