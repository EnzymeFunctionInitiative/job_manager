# app/plugin_loader.py

import importlib
import logging

from config import settings
from plugins.base_connector import BaseConnector
from app.job_logger import logger_names

module_logger = logging.getLogger(logger_names.PLUGIN_LOADER)

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
        module_name = f"plugins.connectors.{connector_name}_connector"
        
        # Dynamically import the module (e.g., plugins.local_connector)
        connector_module = importlib.import_module(module_name)
        
        # Convention: The main class in a plugin module must be named 'Connector'
        connector_class = getattr(connector_module, 'Connector')
        
        # Ensure the loaded class is a valid connector
        if not issubclass(connector_class, BaseConnector):
            module_logger.error(
                "Connector class in '%s' must inherit from BaseConnector",
                module_name,
            )
            raise TypeError
             
        module_logger.info(
            "Successfully loaded connector: %s from %s",
            connector_class.__name__,
            module_name
        )
        return connector_class
        
    except ImportError as e:
        module_logger.error(
            "Could not import connector module: '%s'. Check if the file exists"
            + " and the EXECUTION_CONNECTOR setting is correct.",
            module_name,
            exc_info = e
        )
        raise

    except AttributeError as e:
        module_logger.error(
            "Could not find a class named 'Connector' in module: '%s'. Please"
            + " ensure the plugin class is named correctly.",
            module_name,
            exc_info = e
        )
        raise

