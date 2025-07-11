# app/plugin_loader.py

import importlib
from config import settings
from plugins.base_connector import BaseConnector

def load_connector_class():
    """
    Dynamically loads the connector class based on the settings.

    This function constructs the module name from the EXECUTION_CONNECTOR setting
    (e.g., 'LOCAL' becomes 'plugins.local_connector'). It then dynamically
    imports this module and looks for a class named 'Connector' within it.

    This approach ensures that the core application code does not need to be
    changed when new plugins are added.
    """
    try:
        connector_name = settings.EXECUTION_CONNECTOR.lower()
        module_name = f"plugins.{connector_name}_connector"
        
        # Dynamically import the module (e.g., plugins.local_connector)
        connector_module = importlib.import_module(module_name)
        
        # Convention: The main class in a plugin module must be named 'Connector'
        connector_class = getattr(connector_module, 'Connector')
        
        # Ensure the loaded class is a valid connector
        if not issubclass(connector_class, BaseConnector):
             raise TypeError(
                f"Connector class in {module_name} must inherit from BaseConnector"
             )
             
        print(f"Successfully loaded connector: {connector_class.__name__} from {module_name}")
        return connector_class
        
    except ImportError:
        raise ImportError(f"Could not import connector module: '{module_name}'. Check if the file exists and the EXECUTION_CONNECTOR setting is correct.")
    except AttributeError:
        raise AttributeError(f"Could not find a class named 'Connector' in module: '{module_name}'. Please ensure the plugin class is named correctly.")

