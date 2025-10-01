"""
Settings Service
Manages user settings and preferences.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing user settings."""
    
    def __init__(self, settings_file: str = "./data/settings.json"):
        self.settings_file = Path(settings_file)
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.default_settings = {
            "general": {
                "theme": "system",
                "language": "English",
                "timezone": "Africa/Nairobi"
            },
            "region": {
                "default_region": "Kenya - National",
                "default_location": {
                    "lat": 0.0236,
                    "lon": 37.9062
                }
            },
            "map": {
                "base_layer": "OpenStreetMap",
                "default_zoom": 6,
                "show_prediction_markers": True,
                "auto_center": True
            },
            "models": {
                "aquifer_model": "XGBoost",
                "recharge_model": "LSTM",
                "confidence_threshold": 0.6
            },
            "notifications": {
                "prediction_complete": True,
                "report_generated": True,
                "model_updates": False,
                "system_alerts": True
            },
            "data": {
                "cache_predictions": True,
                "use_real_data": True,
                "data_sources": {
                    "gee": True,
                    "oracle_adb": True,
                    "oci_storage": True
                }
            }
        }
        
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file or create default."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                logger.info("Loaded settings from file")
                return settings
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                return self.default_settings.copy()
        else:
            self._save_settings(self.default_settings)
            return self.default_settings.copy()
    
    def _save_settings(self, settings: Dict[str, Any]):
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            logger.info("Settings saved to file")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings."""
        return self.settings.copy()
    
    def update_settings(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update settings with new values.
        
        Args:
            updates: Dictionary of settings to update
            
        Returns:
            Updated settings
        """
        # Update nested settings
        for key, value in updates.items():
            if key in self.settings:
                if isinstance(value, dict) and isinstance(self.settings[key], dict):
                    self.settings[key].update(value)
                else:
                    self.settings[key] = value
            else:
                # Handle flat updates (e.g., theme, language)
                for category in self.settings.values():
                    if isinstance(category, dict) and key in category:
                        category[key] = value
                        break
        
        self._save_settings(self.settings)
        return self.settings.copy()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.settings = self.default_settings.copy()
        self._save_settings(self.settings)
        logger.info("Settings reset to defaults")
    
    def get_setting(self, category: str, key: str) -> Any:
        """
        Get a specific setting value.
        
        Args:
            category: Settings category
            key: Setting key
            
        Returns:
            Setting value or None
        """
        return self.settings.get(category, {}).get(key)
    
    def set_setting(self, category: str, key: str, value: Any):
        """
        Set a specific setting value.
        
        Args:
            category: Settings category
            key: Setting key
            value: New value
        """
        if category not in self.settings:
            self.settings[category] = {}
        
        self.settings[category][key] = value
        self._save_settings(self.settings)
