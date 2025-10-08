"""
Diff preview system for YAML changes
"""
import difflib
import io
from typing import Dict, Any, List, Tuple
from .yaml_editor import yaml_editor

class DiffViewer:
    """Generate and display diffs for YAML changes"""

    def generate_yaml_diff(self, original_content: str, new_content: str) -> str:
        """Generate unified diff between two YAML strings"""
        original_lines = original_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile='original',
            tofile='modified',
            lineterm='',
            n=3  # Context lines
        ))

        return '\n'.join(diff) if diff else "No changes detected"

    def generate_token_diff(self, module_name: str, changes: Dict[str, Any]) -> Dict[str, str]:
        """Generate token-level diffs for specific changes"""
        diffs = {}

        try:
            # Read current file content
            config, _ = yaml_editor.read_module_config(module_name)
            string_stream = io.StringIO()
            yaml_editor.yaml.dump(config, string_stream)
            original_content = string_stream.getvalue()

            # Apply changes to create new content
            modified_config = config.copy()
            if "uniquekey" in changes:
                if "uniquekey" not in modified_config:
                    modified_config["uniquekey"] = {}
                modified_config["uniquekey"]["NumUniqKey"] = changes["uniquekey"]

            if "period" in changes:
                modified_config["period"] = changes["period"]

            string_stream = io.StringIO()
            yaml_editor.yaml.dump(modified_config, string_stream)
            new_content = string_stream.getvalue()

            # Generate diff
            full_diff = self.generate_yaml_diff(original_content, new_content)

            # Extract only the changed sections for cleaner display
            clean_diff = self._extract_key_changes(full_diff, changes)

            diffs["full_diff"] = full_diff
            diffs["clean_diff"] = clean_diff
            diffs["summary"] = self._generate_change_summary(changes)

        except Exception as e:
            diffs["error"] = f"Error generating diff: {e}"

        return diffs

    def _extract_key_changes(self, full_diff: str, changes: Dict[str, Any]) -> str:
        """Extract only the relevant changed lines"""
        lines = full_diff.split('\n')
        relevant_lines = []

        for line in lines:
            # Look for lines that contain our changed values
            if any(str(value) in line for value in changes.values() if value is not None):
                relevant_lines.append(line)
            elif line.startswith('@@') or line.startswith('+++') or line.startswith('---'):
                relevant_lines.append(line)

        return '\n'.join(relevant_lines) if relevant_lines else "No significant changes detected"

    def _generate_change_summary(self, changes: Dict[str, Any]) -> str:
        """Generate human-readable summary of changes"""
        summary_parts = []

        if "uniquekey" in changes:
            summary_parts.append(f"NumUniqKey: {changes['uniquekey']}")

        if "period" in changes:
            summary_parts.append(f"Period: {changes['period']}")

        return " → ".join(summary_parts) if summary_parts else "No changes"

    def preview_module_changes(self, module_name: str, new_uniquekey: int = None,
                              new_period: str = None) -> Dict[str, Any]:
        """Preview changes for module configuration"""
        changes = {}
        if new_uniquekey is not None:
            changes["uniquekey"] = new_uniquekey
        if new_period is not None:
            changes["period"] = new_period

        if not changes:
            return {"diffs": {}, "message": "No changes to preview"}

        return {
            "diffs": self.generate_token_diff(module_name, changes),
            "changes": changes,
            "module_name": module_name
        }

    def preview_submodule_changes(self, module_name: str, submodule_name: str,
                                 new_uniquekey: int = None) -> Dict[str, Any]:
        """Preview changes for submodule configuration"""
        changes = {}
        if new_uniquekey is not None:
            changes["uniquekey"] = new_uniquekey

        if not changes:
            return {"diffs": {}, "message": "No changes to preview"}

        try:
            # Read current submodule config
            config, _ = yaml_editor.read_submodule_config(module_name, submodule_name)
            string_stream = io.StringIO()
            yaml_editor.yaml.dump(config, string_stream)
            original_content = string_stream.getvalue()

            # Apply changes
            modified_config = config.copy()
            if "uniquekey" not in modified_config:
                modified_config["uniquekey"] = {}
            modified_config["uniquekey"]["NumUniqKey"] = new_uniquekey

            string_stream = io.StringIO()
            yaml_editor.yaml.dump(modified_config, string_stream)
            new_content = string_stream.getvalue()

            # Generate diff
            full_diff = self.generate_yaml_diff(original_content, new_content)
            clean_diff = self._extract_key_changes(full_diff, changes)

            return {
                "diffs": {
                    "full_diff": full_diff,
                    "clean_diff": clean_diff,
                    "summary": f"Submodule NumUniqKey: {new_uniquekey}"
                },
                "changes": changes,
                "module_name": module_name,
                "submodule_name": submodule_name
            }

        except Exception as e:
            return {
                "diffs": {"error": f"Error generating submodule diff: {e}"},
                "changes": changes
            }


# Global diff viewer instance
diff_viewer = DiffViewer()