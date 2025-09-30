#!/usr/bin/env python3
"""
Publish script for Callosum DSL Python package

This script handles uploading to PyPI or TestPyPI
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🚀 {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"   ✅ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Publish Callosum DSL package")
    parser.add_argument("--test", action="store_true", 
                       help="Upload to TestPyPI instead of PyPI")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check the package, don't upload")
    
    args = parser.parse_args()
    
    print("📤 Callosum DSL Package Publisher")
    print("=" * 40)
    
    # Get the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check if dist directory exists
    dist_dir = project_root / "dist"
    if not dist_dir.exists() or not any(dist_dir.iterdir()):
        print("❌ No packages found in dist/")
        print("💡 Run build_package.py first")
        return False
    
    # Show what we're about to upload
    print("\n📦 Packages to upload:")
    for file in dist_dir.iterdir():
        if file.suffix in ['.whl', '.tar.gz']:
            print(f"   • {file.name} ({file.stat().st_size // 1024} KB)")
    
    # Check the package
    print("\n🔍 Checking Package")
    if not run_command("twine check dist/*", "Validating packages"):
        return False
    
    if args.check_only:
        print("\n✅ Package check complete!")
        return True
    
    # Confirm upload
    target = "TestPyPI" if args.test else "PyPI"
    confirm = input(f"\n❓ Upload to {target}? [y/N]: ").strip().lower()
    
    if confirm != 'y':
        print("❌ Upload cancelled")
        return False
    
    # Upload
    if args.test:
        cmd = "twine upload --repository testpypi dist/*"
        print("\n🧪 Uploading to TestPyPI")
        print("💡 Test with: pip install -i https://test.pypi.org/simple/ callosum-dsl")
    else:
        cmd = "twine upload dist/*"
        print("\n🚀 Uploading to PyPI")
        print("💡 Install with: pip install callosum-dsl")
    
    if run_command(cmd, f"Uploading to {target}"):
        print(f"\n🎉 Successfully uploaded to {target}!")
        
        if args.test:
            print("\n📋 To test the uploaded package:")
            print("   pip install -i https://test.pypi.org/simple/ callosum-dsl")
            print("   python3 -c 'from callosum_dsl import Callosum; print(\"✅ Works!\")'")
        else:
            print("\n📋 Package is now live:")
            print("   pip install callosum-dsl")
            print("   https://pypi.org/project/callosum-dsl/")
        
        return True
    else:
        print(f"\n❌ Upload to {target} failed")
        print("💡 Make sure you have the correct credentials configured")
        print("💡 For PyPI: twine configure")
        return False


if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
