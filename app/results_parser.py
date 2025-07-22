# app/results_parser.py

import os
from typing import Dict, Any
from datetime import datetime
import json

from app.job_enums import Status, Pipeline, ImportMode
from app.models import Job, FilenameParameters
from config import settings

class ResultsParser:
    def __init__(self):
        self.results_dir = settings.LOCAL_JOB_DIRECTORY
        
    def parse_results(self, job) -> Dict[str, Any]:
        """ 
        Interface method called from the job_handler code to take a Job object
        and gather all necessary result values from output files.
        """
        job_output_dir = os.path.join(self.results_dir, str(job.id))
        
        # parse the stats.json file
        stats_file_path = os.path.join(job_output_dir,"stats.json")
        if os.path.isfile(stats_file_path):
            # names of keys in the stats.json file do not always map directly
            # to columns in the Job table. Need to grab that mapping and apply
            # it while parsing the json file.
            column_mapping = job.get_result_key_mapping()
            results_dict = self._parse_stats_json(
                stats_file_path,
                column_mapping
            )
        else:
            results_dict = {}

        # are there pipeline specific result files that should also be
        # parsed/gathered for the job table?
        ## if job.pipeline == Pipeline.EST:
        ##      do something here

        return results_dict

    def _parse_stats_json(
            self,
            file_path: str,
            column_mapping_dict: Dict[str,str]
        ) -> Dict[str, Any]:
        """ Gather the python dict from the json-formatted stats.json file """
        # gather the json file's contents in the form of a python dict
        with open(file_path) as stats:
            results_dict = json.load(stats)
        
        # loop over the key:value pairs from the nf-output dict, check whether 
        # the key maps to a column name in the Job table, and apply mapping
        # when needed. Add key:value pairs to the updates_dict.
        updates_dict = {}
        for key, val in results_dict.items():
            # get the value associated with key from the mapping dict or get key
            new_key = column_mapping_dict.get(key, key)
            updates_dict[new_key] = val

        return updates_dict

