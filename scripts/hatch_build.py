import os
import subprocess
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        # Only build frontend if we are building a wheel or sdist
        # and not just installing in editable mode (unless desired)
        print("Building React frontend...")

        front_app_dir = os.path.join(self.root, "front", "app")

        # Check if node_modules exists
        node_modules_path = os.path.join(front_app_dir, "node_modules")
        if not os.path.exists(node_modules_path):
            print(f"node_modules not found in {front_app_dir}. Installing dependencies...")
            # Use shell=True for Windows compatibility if npm is a batch file
            subprocess.check_call("npm ci", cwd=front_app_dir, shell=True)

        # Run npm run build
        print(f"Running npm run build in {front_app_dir}...")
        subprocess.check_call("npm run build", cwd=front_app_dir, shell=True)
