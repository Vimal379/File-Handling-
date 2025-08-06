import os
import shutil
import streamlit as st
from datetime import datetime
from pathlib import Path

# Set page config
st.set_page_config(
    page_title="File Operations Dashboard",
    page_icon="📂",
    layout="wide"
)

# Initialize session state
if 'current_dir' not in st.session_state:
    st.session_state.current_dir = os.getcwd()

# Sidebar navigation
def sidebar_nav():
    st.sidebar.title("Navigation")
    operation = st.sidebar.radio(
        "Select Operation",
        ["Browse Files", "Create Directory", "Create File", 
         "Copy/Move Files", "Delete Files", "File Info", "Search Files"]
    )
    return operation

# Helper functions
def get_dir_contents(path):
    """Get directory contents with metadata"""
    try:
        with os.scandir(path) as entries:
            dirs = []
            files = []
            for entry in entries:
                stat = entry.stat()
                item = {
                    'name': entry.name,
                    'path': entry.path,
                    'is_dir': entry.is_dir(),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'created': datetime.fromtimestamp(stat.st_ctime)
                }
                if entry.is_dir():
                    dirs.append(item)
                else:
                    files.append(item)
            return dirs + files  # Directories first
    except OSError as e:
        st.error(f"Error accessing directory: {e}")
        return []

def human_readable_size(size):
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

# UI Components
def browse_files():
    st.header("File Browser")
    
    # Breadcrumb navigation
    path_parts = Path(st.session_state.current_dir).parts
    breadcrumb = st.container()
    with breadcrumb:
        cols = st.columns(len(path_parts) + 1)
        for i, part in enumerate(path_parts):
            if cols[i].button(part, key=f"breadcrumb_{i}"):
                st.session_state.current_dir = os.path.join(*path_parts[:i+1])
                st.rerun()
    
    # Current directory info
    st.write(f"Current directory: `{st.session_state.current_dir}`")
    
    # Directory contents table
    contents = get_dir_contents(st.session_state.current_dir)
    
    if contents:
        st.subheader("Directory Contents")
        for item in contents:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            with col1:
                icon = "📁" if item['is_dir'] else "📄"
                if st.button(f"{icon} {item['name']}"):
                    if item['is_dir']:
                        st.session_state.current_dir = item['path']
                        st.rerun()
                    else:
                        st.session_state.selected_file = item['path']
            
            with col2:
                st.text(human_readable_size(item['size']))
            with col3:
                st.text(item['modified'].strftime('%Y-%m-%d %H:%M'))
            with col4:
                if not item['is_dir']:
                    if st.button("🗑️", key=f"del_{item['name']}"):
                        try:
                            os.remove(item['path'])
                            st.success(f"Deleted {item['name']}")
                            st.rerun()
                        except OSError as e:
                            st.error(f"Error deleting file: {e}")

def create_directory():
    st.header("Create Directory")
    
    with st.form("create_dir_form"):
        dir_name = st.text_input("Directory Name", placeholder="new_directory")
        parent_dir = st.text_input(
            "Parent Directory (leave empty for current)", 
            value=st.session_state.current_dir
        )
        
        if st.form_submit_button("Create Directory"):
            if not dir_name:
                st.error("Please enter a directory name")
            else:
                new_dir = os.path.join(parent_dir, dir_name)
                try:
                    os.makedirs(new_dir, exist_ok=True)
                    st.success(f"Directory created: {new_dir}")
                    st.session_state.current_dir = new_dir
                    st.rerun()
                except OSError as e:
                    st.error(f"Error creating directory: {e}")

def create_file():
    st.header("Create File")
    
    with st.form("create_file_form"):
        file_name = st.text_input("File Name", placeholder="example.txt")
        parent_dir = st.text_input(
            "Parent Directory (leave empty for current)", 
            value=st.session_state.current_dir
        )
        content = st.text_area("File Content", height=100)
        
        if st.form_submit_button("Create File"):
            if not file_name:
                st.error("Please enter a file name")
            else:
                file_path = os.path.join(parent_dir, file_name)
                try:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    st.success(f"File created: {file_path}")
                    st.rerun()
                except IOError as e:
                    st.error(f"Error creating file: {e}")

def copy_move_files():
    st.header("Copy/Move Files")
    
    source = st.text_input("Source Path", placeholder="/path/to/source")
    destination = st.text_input("Destination Path", placeholder="/path/to/destination")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Copy File"):
            if not source or not destination:
                st.error("Please provide both source and destination")
            else:
                try:
                    shutil.copy2(source, destination)
                    st.success(f"File copied from {source} to {destination}")
                    st.rerun()
                except IOError as e:
                    st.error(f"Error copying file: {e}")
    
    with col2:
        if st.button("Move File"):
            if not source or not destination:
                st.error("Please provide both source and destination")
            else:
                try:
                    shutil.move(source, destination)
                    st.success(f"File moved from {source} to {destination}")
                    st.rerun()
                except IOError as e:
                    st.error(f"Error moving file: {e}")

def delete_files():
    st.header("Delete Files/Directories")
    
    target = st.text_input("Path to delete", placeholder="/path/to/target")
    recursive = st.checkbox("Delete directory and all contents (for directories only)")
    
    if st.button("Delete", type="primary"):
        if not target:
            st.error("Please provide a path")
        else:
            try:
                if os.path.isfile(target):
                    os.remove(target)
                    st.success(f"File deleted: {target}")
                elif os.path.isdir(target):
                    if recursive:
                        shutil.rmtree(target)
                        st.success(f"Directory and all contents deleted: {target}")
                    else:
                        os.rmdir(target)
                        st.success(f"Empty directory deleted: {target}")
                st.rerun()
            except OSError as e:
                st.error(f"Error deleting: {e}")

def file_info():
    st.header("File Information")
    
    file_path = st.text_input("File Path", placeholder="/path/to/file")
    
    if file_path and os.path.exists(file_path):
        try:
            stat = os.stat(file_path)
            st.subheader(f"Information for: `{file_path}`")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Size", human_readable_size(stat.st_size))
                st.metric("Created", datetime.fromtimestamp(stat.st_ctime))
            with col2:
                st.metric("Last Modified", datetime.fromtimestamp(stat.st_mtime))
                st.metric("Last Accessed", datetime.fromtimestamp(stat.st_atime))
            
            if os.path.isfile(file_path):
                with st.expander("View File Contents"):
                    try:
                        with open(file_path, 'r') as f:
                            st.code(f.read())
                    except UnicodeDecodeError:
                        st.warning("Cannot display binary file content")
        except OSError as e:
            st.error(f"Error getting file info: {e}")
    elif file_path:
        st.error("File does not exist")

def search_files():
    st.header("Search Files")
    
    with st.form("search_form"):
        search_dir = st.text_input(
            "Search Directory", 
            value=st.session_state.current_dir
        )
        search_term = st.text_input("Search Term (filename contains)")
        extension = st.text_input("File Extension (leave empty for all)")
        
        if st.form_submit_button("Search"):
            if not os.path.isdir(search_dir):
                st.error("Invalid directory path")
            else:
                results = []
                try:
                    for root, dirs, files in os.walk(search_dir):
                        for file in files:
                            match = True
                            if search_term and search_term.lower() not in file.lower():
                                match = False
                            if extension and not file.lower().endswith(f".{extension.lower()}"):
                                match = False
                            if match:
                                results.append(os.path.join(root, file))
                    
                    st.subheader(f"Search Results ({len(results)} found)")
                    for result in results:
                        st.write(result)
                except OSError as e:
                    st.error(f"Error searching files: {e}")

# Main app
def main():
    st.title("📂 File Operations Dashboard")
    
    operation = sidebar_nav()
    
    if operation == "Browse Files":
        browse_files()
    elif operation == "Create Directory":
        create_directory()
    elif operation == "Create File":
        create_file()
    elif operation == "Copy/Move Files":
        copy_move_files()
    elif operation == "Delete Files":
        delete_files()
    elif operation == "File Info":
        file_info()
    elif operation == "Search Files":
        search_files()

if __name__ == "__main__":
    main()