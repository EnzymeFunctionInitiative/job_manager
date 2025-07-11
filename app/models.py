# app/models.py
# This file will contain the SQLAlchemy ORM classes from your
# job_efi_web_orm.py.txt file.

from datetime import datetime
from enum import Flag
from typing import Dict, Any, List
import sqlalchemy
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, sessionmaker

# --- Mocked constants for standalone execution ---
class Status(Flag):
    NEW = 1
    RUNNING = 2
    FINISHED = 4
    FAILED = 8
    CANCELLED = 16
    COMPLETED = FINISHED | FAILED | CANCELLED

class FlagEnumType(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.Integer
    cache_ok = True

    def __init__(self, enum_class):
        super().__init__()
        self.enum_class = enum_class

    def process_bind_param(self, value, dialect):
        if isinstance(value, self.enum_class):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return self.enum_class(value)
        return value

class Base(DeclarativeBase):
    pass

class Job(Base):
    """
    SQLAlchemy model for the EFI-Web 'Job' table.
    """
    __tablename__ = 'Job'
    
    id: Mapped[int] = mapped_column(
        primary_key=True,
        info = {"is_parameter": True, "pipeline_key": "job_id"}
    )
    uuid: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[Status] = mapped_column(
        FlagEnumType(Status),
        nullable=False,
        info = {"is_updatable": True}
    )
    isPublic: Mapped[bool] = mapped_column(nullable=False)
    job_type: Mapped[str] = mapped_column(nullable=False)
    user_id: Mapped[int | None]
    # This is a placeholder for a User table relationship
    # user_email: Mapped[str] = mapped_column(nullable=True) 
    timeCreated: Mapped[datetime | None]
    timeStarted: Mapped[datetime | None] = mapped_column(
        info = {"is_updatable": True}
    )
    timeCompleted: Mapped[datetime | None] = mapped_column(
        info = {"is_updatable": True}
    )
    efi_db_version: Mapped[str | None] = mapped_column(
        info = {"is_parameter": True, "pipeline_key": "job_id"}
    )
    isExample: Mapped[bool | None]
    parentJob_id: Mapped[int | None]
    schedulerJobId: Mapped[int | None] = mapped_column(
        info = {"is_updatable": True}
    )
    jobName: Mapped[str | None] = mapped_column(info = {"is_parameter": True})
    results: Mapped[str | None] = mapped_column(info = {"is_updatable": True})
    
    __mapper_args__ = {
        "polymorphic_on": "job_type",
        "polymorphic_identity": "job",
    }

    def __repr__(self):
        if self.status in Status.COMPLETED:
            completed_string = f"timeStarted='{self.timeStarted}', timeCompleted='{self.timeCompleted}'"
        elif self.status == Status.RUNNING:
            completed_string = f"timeStarted='{self.timeStarted}'"
        else:
            completed_string = ""
        return (f"<self.__class__.__name__(id={self.id},"
                + f" status='{self.status}',"
                + f" job_type='{self.job_type}',"
                + f" timeCreated='{self.timeCreated}'"
                + f" {completed_string})>")

    def get_parameters_dict(self) -> Dict[str, Any]:
        mapper = inspect(self.__class__)
        return {
            column.info.get("pipeline_key",column.name): 
                getattr(self, column.name)
            for column in mapper.columns
            if column.info.get("is_parameter")
        }
    
    def get_updatable_attrs(self) -> List[str]:
        mapper = inspect(self.__class__)
        return [ 
            column.name for column in mapper.columns
            if column.info.get("is_updatable")
        ]


################################################################################
# Mixin Column Classes

class AlignmentScoreParameters:
    alignmentScore: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True, "pipeline_key": "filter"}
    )

class BlastSequenceParameters:
    blastSequence: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True, "pipeline_key": "blast_query_file"}
    )

class SequenceLengthParameters:
    minLength: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True, "pipeline_key": "min_length"}
    )
    maxLength: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True, "pipeline_key": "max_length"}
    )

class ProteinFamilyAdditionParameters:
    families: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True}
    )
    sequence_version: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True}
    )
    fraction: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )
    numUnirefClusters: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )

class DomainBoundariesParameters:
    domain: Mapped[bool | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True}
    )
    domainRegion: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )

class ExcludeFragmentsParameters:
    excludeFragments: Mapped[bool | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )

class FilterByTaxonomyParameters:
    taxSearch: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )
    taxSearchName: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )

class FilterByFamiliesParameters:
    filterByFamilies: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True, "pipeline_key": "filter"}
    )

class UserUploadedIdsParameters:
    # NOTE: these are results parameters?
    numMatchedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_updatable": True}
    )
    numUnmatchedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_updatable": True}
    )

class FilenameParameters:
    uploadedFilename: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )
    jobFilename: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )
    updatedAt: Mapped[datetime | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True, "is_updatable": True}
    )

class SequenceDatabaseParameters:
    blastEValue: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True, "pipeline_key": "import_blast_evalue"}
    )
    maxBlastSequences: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {
            "is_parameter": True,
            "pipeline_key": "import_blast_num_matches"
        }
    )
    sequenceDatabase: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_updatable": True}
    )

class SearchParameters:
    searchType: Mapped[str | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )

class ESTGenerateJob:
    allByAllBlastEValue: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True, "pipeline_key": "blast_evalue"}
    )
    # results columns, not important parameters for nextflow pipelines
    numFamilyOverlap: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_updatable": True}
    )
    numNonFamily: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_updatable": True}
    )
    numUnirefFamilyOverlap: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_updatable": True}
    )
    numComputedSequences: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_updatable": True}
    )
    numUniqueSequences: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_updatable": True}
    )
    numBlastEdges: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_updatable": True}
    )

class GNTDiagramJob:
    neighborhoodWindowSize: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True, "pipeline_key": "nb_size"}
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
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_fasta"
    }
    inputFasta: Mapped[str | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True, }
    )
    pipeline = "est"

class ESTGenerateFamiliesJob(
        Job,
        ESTGenerateJob,
        DomainBoundariesParameters,
        ExcludeFragmentsParameters,
        FilterByTaxonomyParameters,
        ProteinFamilyAdditionParameters,
    ):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_families"
    }
    pipeline = "est"

class ESTGenerateBlastJob(
        Job,
        ESTGenerateJob,
        BlastSequenceParameters,
        ExcludeFragmentsParameters,
        FilterByTaxonomyParameters,
        ProteinFamilyAdditionParameters,
        SequenceDatabaseParameters,
    ):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_blast"
    }
    pipeline = "est"

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
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_accession"
    }
    domainFamily: Mapped[str | None] = mapped_column(
        info = {"is_parameter": True, "pipeline_key": "domain_family"}
    )
    pipeline = "est"

class ESTSSNFinalizationJob(
        Job,
        AlignmentScoreParameters,
        ExcludeFragmentsParameters,
        FilterByTaxonomyParameters,
        SequenceLengthParameters,
    ):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_ssn_finalization"
    }
    computeNeighborhoodConnectivity: Mapped[bool | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )
    pipeline = "generatessn"

class ESTNeighborhoodConnectivityJob(Job, FilenameParameters):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_neighborhood_connectivity"
    }
    pipeline = "neighborhoodconnectivity"

class ESTConvergenceRatioJob(
        Job,
        AlignmentScoreParameters,
        FilenameParameters
    ):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_convergence_ratio"
    }
    pipeline = "convergenceratio"

class ESTClusterAnalysisJob(Job, FilenameParameters):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_cluster_analysis"
    }
    minSeqMSA: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )
    maxSeqMSA: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )
    pipeline = "clusteranalysis"

class ESTColorSSNJob(Job, FilenameParameters):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_color_ssn"
    }
    pipeline = "colorssn"

class GNTGNNJob(Job, GNTDiagramJob, FilenameParameters):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_gnn"
    }
    cooccurrence: Mapped[float | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True, "pipeline_key": "cooc_threshold"}
    )
    neighborhood_size: Mapped[int | None] = mapped_column(
        use_existing_column=True,
        info = {"is_parameter": True, "pipeline_key": "nb_size"}
    )
    pipeline = "gnt"

class GNTDiagramBlastJob(
        Job,
        GNTDiagramJob,
        BlastSequenceParameters,
        ExcludeFragmentsParameters,
        SequenceDatabaseParameters,
    ):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_diagram_blast"
    }
    pipeline = "gnd"

class GNTDiagramFastaJob(Job, GNTDiagramJob, FilenameParameters):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_diagram_fasta"
    }
    pipeline = "gnd"

class GNTDiagramSequenceIdJob(
        Job,
        GNTDiagramJob,
        ExcludeFragmentsParameters,
        FilenameParameters,
        SequenceDatabaseParameters,
    ):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_diagram_sequence_id"
    }
    pipeline = "gnd"

class GNTViewDiagramJob(Job, FilenameParameters):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_view_diagram"
    }
    pipeline = "gnd"

class CGFPIdentifyJob(
        Job,
        FilenameParameters,
        SearchParameters,
        SequenceLengthParameters,
    ):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "cgfp_identify"
    }
    referenceDatabase: Mapped[str | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )
    cdhitSequenceIdentity: Mapped[int | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )
    pipeline = "cgfp"

class CGFPQuantifyJob(Job,SearchParameters):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "cgfp_quantify"
    }
    metagenomes: Mapped[str | None] = mapped_column(
        # NOTE: does this map to a params in the nextflow pipeline(s)
        info = {"is_parameter": True}
    )
    pipeline = "cgfp"

class TaxonomyAccessionJob(
        Job,
        ExcludeFragmentsParameters,
        FilterByFamiliesParameters,
        FilterByTaxonomyParameters,
        FilenameParameters,
        SequenceDatabaseParameters,
    ):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "taxonomy_accession"
    }
    pipeline = "taxonomy"

class TaxonomyFamiliesJob(
        Job,
        ExcludeFragmentsParameters,
        FilterByFamiliesParameters,
        FilterByTaxonomyParameters,
        SequenceLengthParameters,
    ):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "taxonomy_families"
    }
    pipeline = "taxonomy"

class TaxonomyFastaJob(
        Job,
        ExcludeFragmentsParameters,
        FilenameParameters,
        FilterByFamiliesParameters,
        FilterByTaxonomyParameters,
    ):
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "taxonomy_fasta"
    }
    pipeline = "taxonomy"
