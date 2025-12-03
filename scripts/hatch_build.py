import os
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        # Only build frontend if we are building a wheel or sdist
        # and not just installing in editable mode (unless desired)
        print("Building React frontend...")

        front_app_dir = os.path.join(self.root, "front", "app")

        # # Check if npm is installed
        # try:
        #     subprocess.check_call(["npm", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # except (subprocess.CalledProcessError, FileNotFoundError):
        #     print("Warning: npm not found. Skipping frontend build.")
        #     return

        # # Run npm install
        # print(f"Running npm install in {front_app_dir}...")
        # subprocess.check_call(["npm", "install"], cwd=front_app_dir, shell=True)
        os.system(f"cd {front_app_dir} && npm run build")

        # # Run npm run build
        # print(f"Running npm run build in {front_app_dir}...")
        # subprocess.check_call(["npm", "run", "build"], cwd=front_app_dir, shell=True)
