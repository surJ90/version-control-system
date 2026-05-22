import hashlib
import os
import uuid
import zlib

class VersionControlSystem:
    """
    The main class implementation of the version control system.
    """
    def __init__(self, root_directory: str = '.git'):
        self.root_directory = root_directory
        self.objects_directory = os.path.join(self.root_directory, 'objects')
        self.chunk_size = 8192
        os.makedirs(self.objects_directory, exist_ok=True)

    def store_str_blob(self, str_data: str) -> str:
        data = str_data.encode('utf-8')
        compressed_data = zlib.compress(data)
        hash = hashlib.sha1(data).hexdigest()
        obj_path = os.path.join(self.objects_directory, hash)
        if not os.path.exists(obj_path):
            with open(obj_path, 'wb') as f:
                f.write(compressed_data)
        return hash
    
    def validate_str_blob(self, str_hash: str) -> bool:
        hash_path = os.path.join(self.objects_directory, str_hash)
        if not os.path.exists(hash_path):
            raise FileNotFoundError("Requested file is not present!")
        with open(hash_path, 'rb') as f:
            compressed_data = f.read()
        data = zlib.decompress(compressed_data)
        recalculated_hash = hashlib.sha1(data).hexdigest()

        return str_hash == recalculated_hash
    
    def retrieve_str_blob(self, str_hash: str) -> str:
        if self.validate_str_blob(str_hash):
            hash_path = os.path.join(self.objects_directory, str_hash)
            with open(hash_path, 'rb') as f:
                compressed_data = f.read()
            return zlib.decompress(compressed_data).decode('utf-8')
        return "File corrupted"

    def store_file_blob(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError("Mentioned file not found!")
        temp_file = os.path.join(self.objects_directory, f"tmp_{uuid.uuid4()}")

        hasher = hashlib.sha1()
        compressor = zlib.compressobj()

        try:
            with open(file_path, 'rb') as f_in, open(temp_file, 'wb') as f_out:
                while True:
                    data_chunk = f_in.read(self.chunk_size)
                    if not data_chunk:
                        break
                    hasher.update(data_chunk)
                    f_out.write(compressor.compress(data_chunk))
            with open(temp_file, 'ab') as f:
                f.write(compressor.flush())
            hash = hasher.hexdigest()
            obj_path = os.path.join(self.objects_directory, hash)
            if os.path.exists(obj_path):
                os.remove(temp_file)
            else:
                os.rename(temp_file, obj_path)
            return hash
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e
        
    def validate_file_blob(self, file_hash: str) -> bool:
        hash_path = os.path.join(self.objects_directory, file_hash)
        if not os.path.exists(hash_path):
            raise FileNotFoundError("Requested file not present.")
        decompressor = zlib.decompressobj()
        hasher = hashlib.sha1()
        with open(hash_path, 'rb') as f:
            while True:
                compressed_data_chunk = f.read(self.chunk_size)
                if not compressed_data_chunk:
                    break
                data = decompressor.decompress(compressed_data_chunk)
                hasher.update(data)
            hasher.update(decompressor.flush())
        return file_hash == hasher.hexdigest()
    
    def retrieve_file_blob(self, file_hash: str):
        decompressor = zlib.decompressobj()
        if self.validate_file_blob(file_hash):
            hash_path = os.path.join(self.objects_directory, file_hash)
            with open(hash_path, 'rb') as f:
                while True:
                    compressed_data = f.read(self.chunk_size)
                    if not compressed_data:
                        break
                    yield (decompressor.decompress(compressed_data))
                yield (decompressor.flush())
            
v = VersionControlSystem()
h1 = v.store_file_blob("test.txt")
print(f"File Hash: {h1}")
print(f"Validation Result: {v.validate_file_blob(h1)}")
for chunk in v.retrieve_file_blob(h1):
    print(chunk, end=" ")
