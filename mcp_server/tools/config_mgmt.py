"""
Configuration Management Tools

Implements configuration query and management functions.
"""

from typing import Dict, Optional

from ..services.data_service import DataService
from ..utils.validators import validate_config_section
from ..utils.errors import MCPError


class ConfigManagementTools:
    """Configuration management tools class"""

    def __init__(self, project_root: str = None):
        """
        Initialize configuration management tools

        Args:
            project_root: Project root directory
        """
        self.data_service = DataService(project_root)

    def get_current_config(self, section: Optional[str] = None) -> Dict:
        """
        Get current system configuration

        Args:
            section: Configuration section - all/crawler/push/keywords/weights, default is 'all'

        Returns:
            Configuration dictionary

        Example:
            >>> tools = ConfigManagementTools()
            >>> result = tools.get_current_config(section="crawler")
            >>> print(result['crawler']['platforms'])
        """
        try:
            # Parameter validation
            section = validate_config_section(section)

            # Get configuration
            config = self.data_service.get_current_config(section=section)

            return {
                "config": config,
                "section": section,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }