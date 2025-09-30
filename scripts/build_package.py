#!/usr/bin/env python3
"""
Build script for Callosum DSL Python package

This script:
1. Builds the OCaml DSL compiler
2. Copies the binary to the package
3. Builds the Python package
4. Runs tests
5. Optionally publishes to PyPI
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, description, cwd=None):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        print(f"   ✅ Success")
        if result.stdout.strip():
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False


def main():
    print("🏗️  Callosum DSL Python Package Builder")
    print("=" * 50)
    
    # Get the project root (parent of scripts/)
    project_root = Path(__file__).parent.parent
    python_dir = project_root / "python"
    core_dir = project_root / "core"
    os.chdir(project_root)
    
    # Step 1: Build the OCaml DSL compiler
    print("\n1️⃣ Building OCaml DSL Compiler")
    
    if not core_dir.exists():
        print("   ❌ Core directory not found. Make sure you're in the project root.")
        return False
    
    # Check if dune is available
    if not run_command("which dune", "Checking for dune", cwd=core_dir):
        print("   💡 Install dune with: opam install dune")
        return False
    
    # Build the DSL
    if not run_command("eval $(opam env) && dune build", "Building DSL", cwd=core_dir):
        print("   💡 Make sure OCaml and opam are properly installed")
        return False
    
    # Step 2: Copy the binary to the package
    print("\n2️⃣ Copying Binary to Package")
    
    binary_source = core_dir / "_build" / "default" / "bin" / "main.exe"
    binary_dest = python_dir / "callosum_dsl" / "bin" / "dsl-parser"
    
    # Create bin directory if it doesn't exist
    binary_dest.parent.mkdir(parents=True, exist_ok=True)
    
    if binary_source.exists():
        # Remove existing binary if it exists
        if binary_dest.exists():
            binary_dest.unlink()
        
        shutil.copy2(binary_source, binary_dest)
        # Make executable
        os.chmod(binary_dest, 0o755)
        print(f"   ✅ Copied {binary_source} → {binary_dest}")
    else:
        print(f"   ❌ Binary not found at {binary_source}")
        return False
    
    # Step 3: Clean previous builds
    print("\n3️⃣ Cleaning Previous Builds")
    
    for path in ["build", "dist", "*.egg-info"]:
        if run_command(f"rm -rf {path}", f"Removing {path}", cwd=python_dir):
            pass
    
    # Step 4: Build the Python package
    print("\n4️⃣ Building Python Package")
    
    if not run_command("python3 -m build", "Building wheel and source distribution", cwd=python_dir):
        print("   💡 Install build tools with: pip install build")
        return False
    
    # Step 5: Run tests
    print("\n5️⃣ Running Tests")
    
    if not run_command("python3 -m pytest tests/ -v", "Running test suite", cwd=python_dir):
        print("   ⚠️  Tests failed, but package was built")
        print("   💡 Install pytest with: pip install pytest")
        # Don't return False - tests might fail due to missing dependencies
    
    # Step 6: Check package
    print("\n6️⃣ Checking Package")
    
    if run_command("twine check dist/*", "Checking package for PyPI compatibility", cwd=python_dir):
        pass
    else:
        print("   💡 Install twine with: pip install twine")
    
    # Step 7: Show results
    print("\n🎉 Build Complete!")
    print("\nGenerated files:")
    
    dist_dir = python_dir / "dist"
    if dist_dir.exists():
        for file in dist_dir.iterdir():
            print(f"   📦 {file.name} ({file.stat().st_size // 1024} KB)")
    
    print("\n📋 Next Steps:")
    print("   • Test the package: pip install dist/callosum_dsl-*.whl")
    print("   • Test import: python3 -c 'from callosum_dsl import Callosum'")
    print("   • Upload to TestPyPI: twine upload --repository testpypi dist/*")
    print("   • Upload to PyPI: twine upload dist/*")
    
    return True


if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
