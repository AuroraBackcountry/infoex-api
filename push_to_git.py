#!/usr/bin/env python3
"""
Git push script for Aurora InfoEx Reporting System
"""

import subprocess
import os
import sys

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    print("🚀 Pushing Aurora InfoEx updates to GitHub...")
    
    # Change to project directory
    project_dir = "/Users/ben_johns/Projects/report_to_JSON_converter"
    try:
        os.chdir(project_dir)
        print(f"✅ Changed to directory: {os.getcwd()}")
    except Exception as e:
        print(f"❌ Failed to change directory: {e}")
        sys.exit(1)
    
    # Check git status
    print("\n📊 Checking git status...")
    ret, out, err = run_command("git status --porcelain")
    if ret != 0:
        print(f"❌ Git status failed: {err}")
    else:
        if out:
            print("Files to commit:")
            print(out)
        else:
            print("No changes to commit")
    
    # Add files
    print("\n📁 Adding files...")
    files_to_add = ["README.md", "DATABASE_FUNCTIONS_GUIDE.md", "GIT_COMMIT_SUMMARY.md"]
    for file in files_to_add:
        if os.path.exists(file):
            ret, out, err = run_command(f"git add {file}")
            if ret == 0:
                print(f"✅ Added {file}")
            else:
                print(f"⚠️  Failed to add {file}: {err}")
        else:
            print(f"⚠️  File not found: {file}")
    
    # Commit
    print("\n💾 Committing changes...")
    commit_msg = """Add database functions for report initialization and validation

- Created PostgreSQL functions for capsule-based workflow
- Added report initialization: start_new_report(), initialize_report_capsules(), populate_initial_capsule()
- Added comprehensive validation: validate_capsule_payload(), update_completion_status(), validate_field_value()
- Added helper functions for field updates and special format validation
- Updated all capsule templates in Supabase with complete JSON structures
- Added DATABASE_FUNCTIONS_GUIDE.md documenting all functions
- Updated README.md to reflect current project status and architecture"""
    
    ret, out, err = run_command(f'git commit -m "{commit_msg}"')
    if ret == 0:
        print("✅ Commit successful!")
        print(out)
    else:
        print(f"❌ Commit failed: {err}")
        if "nothing to commit" in err or "nothing to commit" in out:
            print("ℹ️  No changes to commit. Files may already be committed.")
    
    # Push
    print("\n⬆️  Pushing to GitHub...")
    ret, out, err = run_command("git push origin main")
    if ret == 0:
        print("✅ Push successful!")
        print(out)
    else:
        print(f"❌ Push failed: {err}")
        print("You may need to run 'git push origin main' manually")
    
    print("\n✨ Done!")

if __name__ == "__main__":
    main()

