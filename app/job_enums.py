
from typing import Union
from enum import Enum, Flag, auto

class Status(Flag):
    """ Setting accessible status states """
    NEW = auto()
    RUNNING = auto()
    FINISHED = auto()
    FAILED = auto()
    CANCELLED = auto()
    ARCHIVED = auto()
    
    # flag combinations
    INCOMPLETE = NEW | RUNNING
    COMPLETED = FINISHED | FAILED | CANCELLED | ARCHIVED
    CURRENT = NEW | RUNNING | FINISHED | FAILED
    ALL = NEW | RUNNING | FINISHED | FAILED | ARCHIVED

    def __str__(self):
        return self.name.lower()

    @classmethod
    def get_flag(cls, status: Union[int, str]):
        try:
            if type(status) == int:
                return cls(status)
            elif type(status) == str:
                return getattr(cls, status.upper())
            else:
                raise ValueError(f"Given status value ({status}) is" 
                    + " incorrectly typed.")
        except (ValueError, AttributeError) as e:
            print(f"Given status value ({status}) does not match a Status" 
                + f" Flag.\n{e}")
            raise

class Pipeline(Enum):
    """ Setting the Job types """
    EST = auto()
    GENERATESSN = auto()
    COLORSSN = auto()
    GNT = auto()
    GND = auto()
    # these names are assuming that the nextflow pipelines are cgfp.nf and 
    # taxon.nf, etc
    NEIGHBORHOODCONN = auto()
    CONVERGENCERATIO = auto()
    CLUSTERANALYSIS = auto()
    CGFP = auto()
    TAXON = auto()

    def __str__(self):
        return self.name.lower()


class ImportMode(Enum):
    """ Setting the import mode types """
    ACCESSION = auto()
    BLAST = auto()
    FAMILIES = auto()
    FASTA = auto()
    VIEW = auto()
    IDENTIFY = auto()
    QUANTIFY = auto()

    def __str__(self):
        return self.name.lower()

