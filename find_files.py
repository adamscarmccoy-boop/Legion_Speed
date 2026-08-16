#!/usr/bin/env python3
"""
Script to find .md files and skills folders on specified drives
and provide size summaries.
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

def get_size(path):
    """Get size of file or directory in bytes."""
    if os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
        return total
    return 0

def format_size(size_bytes):
    """Convert bytes to human readable format."""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

def find_md_files_and_skills(drives):
    """Find .md files and skills folders on specified drives."""
    results = {
        'md_files': [],
        'skills_folders': [],
        'md_by_drive': defaultdict(list),
        'skills_by_drive': defaultdict(list)
    }
    
    for drive in drives:
        drive_path = f"{drive}:\\"
        if not os.path.exists(drive_path):
            print(f"Drive {drive}: not found or not accessible")
            continue
            
        print(f"Scanning {drive}:\\...")
        
        for root, dirs, files in os.walk(drive_path):
            # Skip certain directories to speed up search
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in ['$Recycle.Bin', 'System Volume Information', 'Windows', 'Program Files', 'Program Files (x86)']]
            
            # Look for .md files
            for file in files:
                if file.lower().endswith('.md'):
                    full_path = os.path.join(root, file)
                    results['md_files'].append(full_path)
                    results['md_by_drive'][drive].append(full_path)
            
            # Look for skills folders
            for dir_name in dirs:
                if dir_name == 'skills' and '.agents' in root:
                    # Found a .agents\skills folder
                    skills_path = os.path.join(root, dir_name)
                    results['skills_folders'].append(skills_path)
                    results['skills_by_drive'][drive].append(skills_path)
                elif dir_name == '.agents':
                    # Check if this .agents folder has a skills subdirectory
                    skills_path = os.path.join(root, dir_name, 'skills')
                    if os.path.exists(skills_path):
                        results['skills_folders'].append(skills_path)
                        results['skills_by_drive'][drive].append(skills_path)
    
    return results

def main():
    # Drives to search
    drives = ['C', 'E']  # Based on user's environment
    
    print("Starting file search...")
    results = find_md_files_and_skills(drives)
    
    # Print summary
    print("\n" + "="*60)
    print("SEARCH RESULTS SUMMARY")
    print("="*60)
    
    # MD Files summary
    print(f"\n📄 MARKDOWN FILES (.md):")
    print(f"   Total found: {len(results['md_files'])}")
    for drive in drives:
        count = len(results['md_by_drive'][drive])
        if count > 0:
            print(f"   Drive {drive}: {count} files")
    
    # Skills folders summary
    print(f"\n📁 SKILLS FOLDERS:")
    print(f"   Total found: {len(results['skills_folders'])}")
    for drive in drives:
        count = len(results['skills_by_drive'][drive])
        if count > 0:
            print(f"   Drive {drive}: {count} folders")
    
    # Detailed MD files (first 10)
    if results['md_files']:
        print(f"\n📄 FIRST 10 MARKDOWN FILES:")
        for i, file_path in enumerate(results['md_files'][:10]):
            size = get_size(file_path)
            print(f"   {i+1}. {file_path} ({format_size(size)})")
        if len(results['md_files']) > 10:
            print(f"   ... and {len(results['md_files']) - 10} more")
    
    # Detailed skills folders with sizes
    if results['skills_folders']:
        print(f"\n📁 SKILLS FOLDERS WITH SIZES:")
        for i, folder_path in enumerate(results['skills_folders'][:10]):  # Show first 10
            size = get_size(folder_path)
            print(f"   {i+1}. {folder_path}")
            print(f"       Size: {format_size(size)}")
        if len(results['skills_folders']) > 10:
            print(f"   ... and {len(results['skills_folders']) - 10} more")
    
    # Save detailed results to file
    output_file = "file_search_results.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("FILE SEARCH RESULTS\n")
        f.write("="*50 + "\n\n")
        
        f.write(f"Markdown Files (.md): {len(results['md_files'])}\n")
        for drive in drives:
            files = results['md_by_drive'][drive]
            if files:
                f.write(f"  Drive {drive}: {len(files)} files\n")
                for file_path in files[:20]:  # Limit to first 20 per drive
                    size = get_size(file_path)
                    f.write(f"    {file_path} ({format_size(size)})\n")
                if len(files) > 20:
                    f.write(f"    ... and {len(files) - 20} more\n")
        
        f.write(f"\nSkills Folders: {len(results['skills_folders'])}\n")
        for drive in drives:
            folders = results['skills_by_drive'][drive]
            if folders:
                f.write(f"  Drive {drive}: {len(folders)} folders\n")
                for folder_path in folders:
                    size = get_size(folder_path)
                    f.write(f"    {folder_path} ({format_size(size)})\n")
    
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()