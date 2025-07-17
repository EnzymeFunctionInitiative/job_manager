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
    status: Mapped[Status] = mapped_column(
        FlagEnumType(Status),
        nullable=False,
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    isPublic: Mapped[bool] = mapped_column(nullable=False)
    job_type: Mapped[str] = mapped_column(nullable=False)
    user_id: Mapped[int | None]
    # This is a placeholder for a User table relationship
    # user_email: Mapped[str] = mapped_column(nullable=True)
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
    isExample: Mapped[bool | None]
    parentJob_id: Mapped[int | None]
    schedulerJobId: Mapped[int | None] = mapped_column(
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    jobName: Mapped[str | None] = mapped_column(
        info = {InfoKeys.IS_PARAMETER: True}
    )
    #results: Mapped[str | None] = mapped_column(
    #    info = {InfoKeys.IS_UPDATABLE: True}
    #)
    
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

    def get_parameters_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary of key:value pairs, where the keys are parameter
        strings used in the EST nextflow pipelines and the values are the
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
    )
    fraction: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    numUnirefClusters: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )

class DomainBoundariesParameters:
    domain: Mapped[bool | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True}
    )
    domainRegion: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )

class ExcludeFragmentsParameters:
    excludeFragments: Mapped[bool | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )

class FilterByTaxonomyParameters:
    taxSearch: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    taxSearchName: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )

class FilterByFamiliesParameters:
    filterByFamilies: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "filter"}
    )

class UserUploadedIdsParameters:
    # NOTE: these are results parameters?
    numMatchedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    numUnmatchedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_UPDATABLE: True}
    )

class FilenameParameters:
    uploadedFilename: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    jobFilename: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    updatedAt: Mapped[datetime | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.IS_UPDATABLE: True}
    )

class SequenceDatabaseParameters:
    blastEValue: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "import_blast_evalue"}
    )
    maxBlastSequences: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            InfoKeys.IS_PARAMETER: True,
            InfoKeys.PARAMETER_KEY: "import_blast_num_matches"
        }
    )
    # why is this updatable ???
    sequenceDatabase: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_UPDATABLE: True}
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
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "blast_evalue"}
    )
    numFamilyOverlap: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    numNonFamily: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    numUnirefFamilyOverlap: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    numComputedSequences: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    numUniqueSequences: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_UPDATABLE: True}
    )
    numBlastEdges: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_UPDATABLE: True}
    )

class GNTDiagramJob:
    neighborhoodWindowSize: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "nb_size"}
    )

###############################################################################
# polymorphic_identity classes

class ESTGenerateFastaJob(
        Job,
        ESTGenerateJob,
        FilenameParameters,
        FilterByFamiliesParameters,
        ProteinFamilyAdditionParameters,
        UserUploadedIdsParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.EST_GENERATE_FASTA)
    
    pipeline = Pipeline.EST
    import_mode = ImportMode.FASTA

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
    import_mode = ImportMode.FAMILIES

class ESTGenerateBlastJob(
        Job,
        ESTGenerateJob,
        FilenameParameters,
        ExcludeFragmentsParameters,
        FilterByTaxonomyParameters,
        ProteinFamilyAdditionParameters,
        SequenceDatabaseParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.EST_GENERATE_BLAST)

    pipeline = Pipeline.EST
    import_mode = ImportMode.BLAST

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
    domainFamily: Mapped[str | None] = mapped_column(
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "domain_family"}
    )

    pipeline = Pipeline.EST
    import_mode = ImportMode.ACCESSION

class ESTSSNFinalizationJob(
        Job,
        AlignmentScoreParameters,
        ExcludeFragmentsParameters,
        FilterByTaxonomyParameters,
        SequenceLengthParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.EST_SSN_FINALIZATION)
    computeNeighborhoodConnectivity: Mapped[bool | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    pipeline = Pipeline.GENERATESSN

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

class ESTClusterAnalysisJob(Job, FilenameParameters):
    __mapper_args__ = create_mapper_args(JobType.EST_CLUSTER_ANALYSIS)
    minSeqMSA: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    maxSeqMSA: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )
    pipeline = Pipeline.CLUSTERANALYSIS

class ESTColorSSNJob(Job, FilenameParameters):
    __mapper_args__ = create_mapper_args(JobType.EST_COLOR_SSN)

    pipeline = Pipeline.COLORSSN

class GNTGNNJob(Job, GNTDiagramJob, FilenameParameters):
    __mapper_args__ = create_mapper_args(JobType.GNT_GNN)

    cooccurrence: Mapped[float | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "cooc_threshold"}
    )
    neighborhood_size: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {InfoKeys.IS_PARAMETER: True, InfoKeys.PARAMETER_KEY: "nb_size"}
    )
    pipeline = Pipeline.GNT

class GNTDiagramBlastJob(
        Job,
        GNTDiagramJob,
        ExcludeFragmentsParameters,
        FilenameParameters,
        SequenceDatabaseParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.GNT_DIAGRAM_BLAST)

    pipeline = Pipeline.GND
    import_mode = ImportMode.BLAST

class GNTDiagramFastaJob(Job, GNTDiagramJob, FilenameParameters):
    __mapper_args__ = create_mapper_args(JobType.GNT_DIAGRAM_FASTA)

    pipeline = Pipeline.GND
    import_mode = ImportMode.FASTA

class GNTDiagramSequenceIdJob(
        Job,
        GNTDiagramJob,
        ExcludeFragmentsParameters,
        FilenameParameters,
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

class CGFPQuantifyJob(Job,SearchParameters):
    __mapper_args__ = create_mapper_args(JobType.CGFP_QUANTIFY)

    metagenomes: Mapped[str | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {InfoKeys.IS_PARAMETER: True}
    )

    pipeline = Pipeline.CGFP
    import_mode = ImportMode.QUANTIFY

class TaxonomyAccessionJob(
        Job,
        ExcludeFragmentsParameters,
        FilterByFamiliesParameters,
        FilterByTaxonomyParameters,
        FilenameParameters,
        SequenceDatabaseParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.TAXONOMY_ACCESSION)

    pipeline = Pipeline.TAXON
    import_mode = ImportMode.ACCESSION

class TaxonomyFamiliesJob(
        Job,
        ExcludeFragmentsParameters,
        FilterByFamiliesParameters,
        FilterByTaxonomyParameters,
        SequenceLengthParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.TAXONOMY_FAMILIES)

    pipeline = Pipeline.TAXON
    import_mode = ImportMode.FAMILIES

class TaxonomyFastaJob(
        Job,
        ExcludeFragmentsParameters,
        FilenameParameters,
        FilterByFamiliesParameters,
        FilterByTaxonomyParameters,
    ):
    __mapper_args__ = create_mapper_args(JobType.TAXONOMY_FASTA)

    pipeline = Pipeline.TAXON
    import_mode = ImportMode.FASTA

