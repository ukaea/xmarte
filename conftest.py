# conftest.py
import sys
import os
from pathlib import Path
import pdb
import shutil

top_dir = os.path.abspath(os.path.dirname(__file__))

# Setup our environment
user_path = os.path.join(os.path.abspath(str(Path.home())), r".xmarte/")
if os.path.exists(user_path):
    shutil.rmtree(user_path)
if not os.path.exists(user_path):
    os.mkdir(user_path)
db_path = os.path.join(os.path.abspath(str(Path.home())), r".xmarte/", 'typedb')
if not os.path.exists(db_path):
    os.mkdir(db_path)

db_test_files = os.path.join(top_dir, 'test', 'files','type_db')
for item in os.listdir(db_test_files):
    src_path = os.path.join(db_test_files, item)
    dst_path = os.path.join(db_path, item)
    if not os.path.exists(dst_path):
        if os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)