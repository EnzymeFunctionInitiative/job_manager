# app/models.py

from datetime import datetime
from typing import Dict, List, Any
import sqlalchemy
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

from app.job_enums import Status, JobType, Pipeline, ImportMode, InfoKeys
from app.flag_enum_type import FlagEnumType

def create_mapper_args(identity: JobType) -> Dict[str, Any]:
    """ """
    return {
        "polymorphic_load": "selectin",
        "polymorphic_identity": identity.value
    }

class Base(DeclarativeBase):
    pass

class Job(Base):
    """
    SQLAlchemy model for the EFI-Web 'Job' table.
    """
    __tablename__ = 'Job'
    
    id: Mapped[int] = mapped_column(
        primary_key=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "job_id"}
    )
    uuid: Mapped[str] = mapped_column(nullable=False)
    user_id: Mapped[int | None] = mapped_column("user")
    status: Mapped[Status] = mapped_column(
        FlagEnumType(Status),
        nullable=False,
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    timeCreated: Mapped[datetime | None]
    timeStarted: Mapped[datetime | None] = mapped_column(
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    timeCompleted: Mapped[datetime | None] = mapped_column(
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    efi_db_version: Mapped[str | None] = mapped_column(
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "efi_db"} # is this the correct mapping?
    )
    jobName: Mapped[str | None] = mapped_column(
        info = {InfoKeys.IS_PARAMETER: True}
    )
    parentJob_id: Mapped[int | None]
    # NOTE: childJob_id maybe?

    isPublic: Mapped[bool] = mapped_column(nullable=False)
    isExample: Mapped[bool | None]
    schedulerJobId: Mapped[int | None] = mapped_column(
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    # is the discriminator column
    job_type: Mapped[str] = mapped_column(nullable=False)
    __mapper_args__ = {
        "polymorphic_on": "job_type",
        "polymorphic_identity": JobType.JOB,
    }

    def __repr__(self):
        if self.status in Status.COMPLETED:
            completed_string = f"timeStarted='{self.timeStarted}', timeCompleted='{self.timeCompleted}'"
        elif self.status == Status.RUNNING:
            completed_string = f"timeStarted='{self.timeStarted}'"
        else:
            completed_string = ""
        return (f"<{self.__class__.__name__}(id={self.id},"
                + f" status='{self.status}',"
                + f" job_type='{self.job_type}',"
                + f" timeCreated='{self.timeCreated}'"
                + f" {completed_string})>")

    ############################################################################
    # Interface methods
    def get_parameters_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary of key:value pairs, where the keys are parameter
        strings used in the nextflow pipelines and the values are the
        columns' values from the Job table.

        This mapping is necessary because naming conventions between symfony
        and nextflow code bases are different. If a column's info attribute
        dictionary contains a `InfoKeys.PARAMETER_KEY` that string will be used
        in the params.json file.
        """
        mapper = inspect(self.__class__)
        return {
            column.info.get(InfoKeys.PARAMETER_KEY,column.name):
                getattr(self, column.name)
            for column in mapper.columns
            if column.info.get(InfoKeys.IS_PARAMETER)
        }
   
    def get_filter_parameters(self) -> List[str]:
        """
        Return a list of column attribute names for columns that are 
        associated with filtering sequences out of an input set of sequences.
        """
        mapper = inspect(self.__class__)
        return [
            column.name for column in mapper.columns
            if column.info.get(InfoKeys.IS_FILTER)
        ]

    def get_updatable_attrs(self) -> List[str]:
        """
        Return a list of column attribute names for columns that are "allowed"
        to be updated. Any column not flagged by `InfoKeys.IS_UPDATABLE` in
        the associated info dict should not be allowed to have its value
        overwritten.
        """
        mapper = inspect(self.__class__)
        return [
            column.name for column in mapper.columns
            if column.info.get(InfoKeys.IS_UPDATABLE)
        ]

    def get_result_key_mapping(self) -> Dict[str, Any]:
        """
        Return a dict of key:value pairs, where the keys are the keys used in
        output files from the nextflow pipelines (generally in `stats.json`).
        The values are the attribute names for the associated MappedColumn
        objects in the Job table.
        """
        mapper = inspect(self.__class__)
        return {
            column.info.get(InfoKeys.RESULT_KEY, column.name): column.name
            for column in mapper.columns
            if column.info.get(InfoKeys.IS_UPDATABLE)
        }
    ############################################################################


################################################################################
# Mixin Column Classes

class AlignmentScoreParameters:
    alignmentScore: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True}
    )

class SequenceLengthParameters:
    minLength: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "min_length"}
    )
    maxLength: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "max_length"}
    )

class ProteinFamilyAdditionParameters:
    families: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True}
    )
    sequence_version: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True}
    )   # NOTE: is an Enum on the symfony-side
    fraction: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.IS_FILTER: True}
    )
    # RESULTS
    numFamilyIds = Mapped[int, None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_family"
        }
    )   # NOTE: this column functions for UniProt, Uniref90, and Uniref50 runs;
    numFullFamilyIds = Mapped[int, None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_full_family"
        }
    )
    numFamilyOverlapIds = Mapped[int, None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_shared_ids"
        }
    )
    numFamilyUnirefOverlapIds = Mapped[int, None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_shared_uniref_ids"
        }
    )
    numFractionFiltered = Mapped[int, None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_filter_fraction"
        }
    )

class DomainBoundariesParameters:
    domain: Mapped[bool | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True}
    )
    domainRegion: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True}
    )   # NOTE: is an Enum on the symfony-side

class ExcludeFragmentsParameters:
    excludeFragments: Mapped[bool | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.IS_FILTER: True}
    )
    # RESULTS
    numFragmentFiltered = Mapped[int, None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_filter_fragment"
        }
    )

class FilterByTaxonomyParameters:
    taxSearch: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.IS_FILTER: True}
    )
    taxSearchName: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.IS_FILTER: True}
    )
    # RESULTS
    numTaxonomyFiltered = Mapped[int, None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_filter_taxonomy"
        }
    )

class FilterByFamiliesParameters:
    filterByFamilies: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.IS_FILTER: True}
    )
    # RESULTS
    numFamilyFiltered = Mapped[int, None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_filter_family"
        }
    )

class UserUploadedIdsParameters:
    # RESULTS
    numMatchedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InforKeys.RESULT_KEY: "num_matched"
        }
    )
    numUnmatchedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_unmatched"
        }
    )

class FilenameParameters:
    uploadedFilename: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True} # this is not a parameter, correct?
    )
    jobFilename: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True} # this needs to be handled pre-job submission
    )
    updatedAt: Mapped[datetime | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_UPDATABLE: True} # this is not updatable, correct?
    )

class SequenceDatabaseParameters:
    blastEValue: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_PARAMETER: True,
            InfoKeys.PARAMETER_KEY: "import_blast_evalue"
        }
    )
    maxBlastSequences: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_PARAMETER: True,
            InfoKeys.PARAMETER_KEY: "import_blast_num_matches"
        }
    )
    sequenceDatabase: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )

class SearchParameters:
    searchType: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )

class ESTGenerateJob:
    allByAllBlastEValue: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_PARAMETER: True,
            InfoKeys.PARAMETER_KEY: "blast_evalue"
        }
    )
    # RESULTS
    numComputedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InforKeys.RESULT_KEY: "num_unique_ids"
        }
    )
    numImportedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InforKeys.RESULT_KEY: "num_ids"
        }
    )
    outputConvergenceRatio: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InforKeys.RESULT_KEY: "convergence_ratio"
        }
    )
    numBlastEdges: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_blast_edges"
        }
    )

class NeighborhoodSizeParameters:
    neighborhoodSize: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "nb_size"}
    )

class ColorSSNParameters:
    # RESULTS
    numSsnClusters: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_ssn_clusters"
        }
    )
    numSsnSingletons: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_ssn_singletons"
        }
    )
    numSsnMetanodes: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_ssn_nodes"
        }
    )
    numSsnAccessionIds: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "num_ssn_accession_ids"
        }
    )
    colorSsnSequenceSoure: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InfoKeys.RESULT_KEY: "ssn_sequence_source"
        }
    )



###############################################################################
# polymorphic_identity / discriminator classes

class ESTGenerateFastaJob(
        Job,
        ESTGenerateJob,
        FilenameParameters,
        ProteinFamilyAdditionParameters,
        UserUploadedIdsParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.EST_GENERATE_FASTA)
    pipeline = Pipeline.EST
    import_mode = ImportMode.FASTA
    
    # RESULTS
    numFastaHeaders: Mapped[int | None] = mapped_column(
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InforKeys.RESULT_KEY: "num_headers"
        }
    )

class ESTGenerateFamiliesJob(
        Job,
        ESTGenerateJob,
        DomainBoundariesParameters,
        ExcludeFragmentsParameters,
        FilterByTaxonomyParameters,
        ProteinFamilyAdditionParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.EST_GENERATE_FAMILIES)
    pipeline = Pipeline.EST
    import_mode = ImportMode.FAMILY

class ESTGenerateBlastJob(
        Job,
        ESTGenerateJob,
        ExcludeFragmentsParameters,
        FilenameParameters,
        FilterByTaxonomyParameters,
        ProteinFamilyAdditionParameters,
        SequenceDatabaseParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.EST_GENERATE_BLAST)
    pipeline = Pipeline.EST
    import_mode = ImportMode.BLAST

    # RESULTS
    numBlastUnmatchedIds: Mapped[int | None] = mapped_column(
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InforKeys.RESULT_KEY: "num_blast_unmatched"
        }
    )
    numBlastRetrievedIds: Mapped[int | None] = mapped_column(
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InforKeys.RESULT_KEY: "num_blast_retr"
        }
    )

class ESTGenerateAccessionJob(
        Job,
        ESTGenerateJob,
        DomainBoundariesParameters,
        ExcludeFragmentsParameters,
        FilenameParameters,
        FilterByFamiliesParameters,
        FilterByTaxonomyParameters,
        ProteinFamilyAdditionParameters,
        UserUploadedIdsParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.EST_GENERATE_ACCESSION)
    pipeline = Pipeline.EST
    import_mode = ImportMode.ACCESSION
    
    domainFamily: Mapped[str | None] = mapped_column(
        info = {
            InfoKeys.IS_PARAMETER: True,
            InfoKeys.PARAMETER_KEY: "domain_family"
        }
    )
    # RESULTS
    numForeignIds: Mapped[int | None] = mapped_column(
        info = {
            InfoKeys.IS_UPDATABLE: True,
            InforKeys.RESULT_KEY: "num_foreign"
        }
    )

class ESTSSNFinalizationJob(
        Job,
        AlignmentScoreParameters,
        ExcludeFragmentsParameters,
        FilterByTaxonomyParameters,
        SequenceLengthParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.EST_SSN_FINALIZATION)
    pipeline = Pipeline.GENERATESSN

    computeNeighborhoodConnectivity: Mapped[bool | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    # RESULTS
    resultFileStats: Mapped[str | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_UPDATABLE: True}
    )

class ESTNeighborhoodConnectivityJob(Job, FilenameParameters):
    __mapper_args__ = create_mapper_args(JobType.EST_NEIGHBORHOOD_CONNECTIVITY)
    pipeline = Pipeline.NEIGHBORHOODCONN

class ESTConvergenceRatioJob(
        Job,
        AlignmentScoreParameters,
        FilenameParameters
    ):
    __mapper_args__ = create_mapper_args(JobType.EST_CONVERGENCE_RATIO)
    pipeline = Pipeline.CONVERGENCERATIO

class ESTClusterAnalysisJob(Job, ColorSSNParameters, FilenameParameters):
    __mapper_args__ = create_mapper_args(JobType.EST_CLUSTER_ANALYSIS)
    pipeline = Pipeline.CLUSTERANALYSIS

    minNumSequences: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    maxNumSequences: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    makeWeblogo: Mapped[bool | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    computeConsensusResidues: Mapped[bool | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    consensusResidues: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    pidThresholds: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    makeHmms: Mapped[bool | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    makeLengthHistograms: Mapped[bool | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )

class ESTColorSSNJob(Job, FilenameParameters, ColorSSNParameters):
    __mapper_args__ = create_mapper_args(JobType.EST_COLOR_SSN)
    pipeline = Pipeline.COLORSSN

class GNTGNNJob(Job, FilenameParameters, NeighborhoodSizeParameters):
    __mapper_args__ = create_mapper_args(JobType.GNT_GNN)
    pipeline = Pipeline.GNT

    cooccurrence: Mapped[float | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "cooc_threshold"}
    )
    neighborhood_size: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "nb_size"}
    )

class GNTDiagramBlastJob(
        Job,
        ExcludeFragmentsParameters,
        FilenameParameters,
        NeighborhoodSizeParameters,
        SequenceDatabaseParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.GNT_DIAGRAM_BLAST)
    pipeline = Pipeline.GND
    import_mode = ImportMode.BLAST

class GNTDiagramFastaJob(Job, FilenameParameters, NeighborhoodSizeParameters):
    __mapper_args__ = create_mapper_args(JobType.GNT_DIAGRAM_FASTA)
    pipeline = Pipeline.GND
    import_mode = ImportMode.FASTA

class GNTDiagramSequenceIdJob(
        Job,
        ExcludeFragmentsParameters,
        FilenameParameters,
        NeighborhoodSizeParameters,
        SequenceDatabaseParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.GNT_DIAGRAM_SEQUENCE_ID)
    pipeline = Pipeline.GND
    import_mode = ImportMode.ACCESSION

class GNTViewDiagramJob(Job, FilenameParameters):
    __mapper_args__ = create_mapper_args(JobType.GNT_VIEW_DIAGRAM)
    pipeline = Pipeline.GND
    import_mode = ImportMode.VIEW

class CGFPIdentifyJob(
        Job,
        FilenameParameters,
        SearchParameters,
        SequenceLengthParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.CGFP_IDENTIFY)

    referenceDatabase: Mapped[str | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    cdhitSequenceIdentity: Mapped[int | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )

    pipeline = Pipeline.CGFP
    import_mode = ImportMode.IDENTIFY

class CGFPQuantifyJob(Job, SearchParameters):
    __mapper_args__ = create_mapper_args(JobType.CGFP_QUANTIFY)
    pipeline = Pipeline.CGFP
    import_mode = ImportMode.QUANTIFY

    metagenomes: Mapped[str | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )

class TaxonomyAccessionJob(
        Job,
        ExcludeFragmentsParameters,
        FilenameParameters,
        FilterByFamiliesParameters,
        FilterByTaxonomyParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.TAXONOMY_ACCESSION)
    pipeline = Pipeline.TAXONOMY
    import_mode = ImportMode.ACCESSION

    sequence_version: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True}
    )   # NOTE: is an Enum on the symfony-side

class TaxonomyFamiliesJob(
        Job,
        ExcludeFragmentsParameters,
        FilterByTaxonomyParameters,
        FilterByFamiliesParameters,
        SequenceLengthParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.TAXONOMY_FAMILIES)
    pipeline = Pipeline.TAXONOMY
    import_mode = ImportMode.FAMILY

class TaxonomyFastaJob(
        Job,
        ExcludeFragmentsParameters,
        FilenameParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.TAXONOMY_FASTA)
    pipeline = Pipeline.TAXONOMY
    import_mode = ImportMode.FASTA

