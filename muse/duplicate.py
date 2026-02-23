import os
import hashlib

# ANSI colors
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RED    = "\033[31m"
RESET  = "\033[0m"


class DuplicateChecker:
    def __init__(self, output_base):
        self.hash_db_file = os.path.join(output_base, ".muse_hashes.txt")

    # ── Hashing ──────────────────────────────────────────────────────────────

    def compute_file_hash(self, filepath: str, chunk_size: int = 8192) -> str | None:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            print(f"{RED}⚠️  Error computing hash: {e}{RESET}")
            return None

    # ── Database I/O ─────────────────────────────────────────────────────────

    def load_hash_database(self) -> dict:
        """
        Returns a dict of:
          { "hash:<sha256>": filepath, "id:<youtube_id>": filepath }
        """
        if not os.path.exists(self.hash_db_file):
            return {}

        db = {}
        try:
            with open(self.hash_db_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and ":" in line:
                        # format: "hash:<sha256>:<filepath>"  or  "id:<video_id>:<filepath>"
                        parts = line.split(":", 2)
                        if len(parts) == 3:
                            kind, key, filepath = parts
                            db[f"{kind}:{key}"] = filepath
        except Exception as e:
            print(f"{YELLOW}⚠️  Error loading hash database: {e}{RESET}")

        return db

    def _save_entry(self, kind: str, key: str, filepath: str):
        """Append a single entry to the database file."""
        try:
            os.makedirs(os.path.dirname(self.hash_db_file) or ".", exist_ok=True)
            with open(self.hash_db_file, "a") as f:
                f.write(f"{kind}:{key}:{filepath}\n")
        except Exception as e:
            print(f"{YELLOW}⚠️  Error saving to hash database: {e}{RESET}")

    def remove_entries(self, video_id: str, filepath: str):
        """Remove all entries matching this video ID or filepath from the database."""
        if not os.path.exists(self.hash_db_file):
            return
        try:
            with open(self.hash_db_file, "r") as f:
                lines = f.readlines()
            with open(self.hash_db_file, "w") as f:
                for line in lines:
                    # Keep lines that don't match this video ID or filepath
                    if f"id:{video_id}:" not in line and filepath not in line:
                        f.write(line)
        except Exception as e:
            print(f"{YELLOW}⚠️  Could not clean database: {e}{RESET}")        

    def save_hash_to_database(self, file_hash: str, filepath: str):
        self._save_entry("hash", file_hash, filepath)

    def save_id_to_database(self, video_id: str, filepath: str):
        self._save_entry("id", video_id, filepath)

    # ── Duplicate checks ─────────────────────────────────────────────────────

    def is_duplicate_by_id(self, video_id: str) -> tuple[bool, str | None]:
        """
        Check before downloading — fast, no file needed.
        Returns (True, existing_filepath) if already downloaded.
        """
        if not video_id:
            return False, None

        db = self.load_hash_database()
        key = f"id:{video_id}"

        if key in db:
            existing = db[key]
            if os.path.exists(existing):
                return True, existing
            # File was deleted — remove stale entry silently

        return False, None

    def is_duplicate(self, filepath: str) -> tuple[bool, str | None]:
        """
        Check after downloading — compares file content hash.
        Fallback for cases where we don't have a video ID.
        """
        file_hash = self.compute_file_hash(filepath)
        if not file_hash:
            return False, None

        db = self.load_hash_database()
        key = f"hash:{file_hash}"

        if key in db:
            existing = db[key]
            if os.path.exists(existing):
                return True, existing

        return False, None

    def register(self, video_id: str, file_hash: str, filepath: str):
        """Save both the video ID and file hash after a successful download."""
        if video_id:
            self.save_id_to_database(video_id, filepath)
        if file_hash:
            self.save_hash_to_database(file_hash, filepath)
