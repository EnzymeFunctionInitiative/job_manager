
from typing import Union
from enum import Flag, auto, Enum

class Status(Flag):
    """ Setting accessible status states """
    NEW = auto()
    RUNNING = auto()
    FINISHED = auto()
    FAILED = auto()
    CANCELLED = auto()
    ARCHIVED = auto()
    UNKNOWN = auto()
    
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

class BaseEnum(Enum):
    def __str__(self):
        """ Change the str representation to be the lowercased self.name """
        return self.name.lower()


class JobType(str, BaseEnum):
    """
    Setting accessible job types. This class could be used as the data type for
    the polymorphic column that differentiates the Job subclasses. BUT, it
    isn't currently.
    Also, if python version is 3.11 or later, convert this to a StrEnum and
    remove the str data-type from the class def line.
    """
    JOB = "job"
    EST_GENERATE_BLAST = "est_generate_blast"
    EST_GENERATE_FAMILIES = "est_generate_families"
    EST_GENERATE_FASTA = "est_generate_fasta"
    EST_GENERATE_ACCESSION = "est_generate_accession"
    EST_COLOR_SSN = "est_color_ssn"
    EST_NEIGHBORHOOD_CONNECTIVITY = "est_neighborhood_connectivity"
    EST_CLUSTER_ANALYSIS = "est_cluster_analysis"
    EST_CONVERGENCE_RATIO = "est_convergence_ratio"
    EST_SSN_FINALIZATION = "est_ssn_finalization"
    GNT_GNN = "gnt_gnn"
    GNT_DIAGRAM_BLAST = "gnt_diagram_blast"
    GNT_DIAGRAM_FASTA = "gnt_diagram_fasta"
    GNT_DIAGRAM_SEQUENCE_ID = "gnt_diagram_sequence_id"
    GNT_VIEW_DIAGRAM = "gnt_view_diagram"
    CGFP_IDENTIFY = "cgfp_identify"
    CGFP_QUANTIFY = "cgfp_quantify"
    TAXONOMY_ACCESSION = "taxonomy_accession"
    TAXONOMY_FAMILIES = "taxonomy_families"
    TAXONOMY_FASTA = "taxonomy_fasta"


class Pipeline(BaseEnum):
    """ Setting the Job types """
    EST = auto()
    GENERATESSN = auto()
    COLORSSN = auto()
    GNT = auto()
    GND = auto()
    # these names are assuming that the nextflow pipelines are cgfp.nf,
    # taxonomy.nf, neighborhoodconn.nf, etc
    NEIGHBORHOODCONN = auto()
    CONVERGENCERATIO = auto()
    CLUSTERANALYSIS = auto()
    CGFP = auto()
    TAXONOMY = auto()


class ImportMode(BaseEnum):
    """ Setting the import mode types """
    ACCESSION = auto()
    BLAST = auto()
    FAMILY = auto()
    FASTA = auto()
    VIEW = auto()
    IDENTIFY = auto()
    QUANTIFY = auto()


class InfoKeys(str, BaseEnum):
    """
    Setting the metadata info tags for columns in the Job table.
    Also, if python version is 3.11 or later, convert this to a StrEnum and
    remove the str data-type from the class def line.
    """
    IS_PARAMETER = "is_parameter"
    PARAMETER_KEY = "parameter_key"
    IS_UPDATABLE = "is_updatable"
    RESULT_KEY = "result_key"
    IS_FILTER = "is_filter"

