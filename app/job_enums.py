
from typing import Union
from enum import Flag, auto

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

class Pipeline(Flag):
    EST_Blast = auto()
    EST_Families = auto()
    EST_Fasta = auto()
    EST_Accession = auto()
    GenerateSSN = auto()
    NeighborhoodConn = auto()
    ConvergenceRatio = auto()
    ClusterAnalysis = auto()
    ColorSSN = auto()
    GNT = auto()
    GND_Blast = auto()
    GND_Fasta = auto()
    GND_Accession = auto()
    GND_View = auto()
    CGFP_Ident = auto()
    CGFP_Quant = auto()
    Taxon_Families = auto()
    Taxon_Fasta = auto()
    Taxon_Accession = auto()

    EST = EST_Blast | EST_Families | EST_Fasta | EST_Accession
    GND = GND_Blast | GND_Fasta | GND_Accession | GND_View
    CGFP = CGFP_Ident | CGFP_Quant
    Taxonomy = Taxon_Families | Taxon_Fasta | Taxon_Accession

