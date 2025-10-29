#!/bin/bash

# Git push script for Aurora InfoEx Reporting System
echo "🚀 Pushing Aurora InfoEx updates to GitHub..."

# Change to project directory
cd /Users/ben_johns/Projects/report_to_JSON_converter

# Check git status
echo "📊 Current git status:"
git status

# Add files
echo "📁 Adding files..."
git add README.md DATABASE_FUNCTIONS_GUIDE.md GIT_COMMIT_SUMMARY.md

# Commit with detailed message
echo "💾 Committing changes..."
git commit -m "Add database functions for report initialization and validation

- Created PostgreSQL functions for capsule-based workflow
- Added report initialization: start_new_report(), initialize_report_capsules(), populate_initial_capsule()
- Added comprehensive validation: validate_capsule_payload(), update_completion_status(), validate_field_value()
- Added helper functions for field updates and special format validation
- Updated all capsule templates in Supabase with complete JSON structures
- Added DATABASE_FUNCTIONS_GUIDE.md documenting all functions
- Updated README.md to reflect current project status and architecture"

# Push to origin
echo "⬆️  Pushing to GitHub..."
git push origin main

echo "✅ Done! Check GitHub to verify the push was successful."

