from typing import Literal
from math import floor
import sys
import csv
from decimal import Decimal
from django.core.management.base import BaseCommand

from django.conf import settings
from ...models import (
    LSOA,
    MSOA,
    LocalAuthority,
    Ward,
    GreenSpace,
    DataZone,
    SOA,
    EnglishIndexMultipleDeprivation,
    WelshIndexMultipleDeprivation,
    ScottishIndexMultipleDeprivation,
    NorthernIrelandIndexMultipleDeprivation,
)


IMD_2019_DOMAINS_OF_DEPRIVATION = "File_2_-_IoD2019_Domains_of_Deprivation.csv"
IMD_2019_SUBDOMAINS_OF_DEPRIVATION = "File_4_-_IoD2019_Sub-domains_of_Deprivation.csv"
IMD_2019_SUPPLEMENTARY_INDICES_OF_DEPRIVATION = (
    "File_3_-_IoD2019_Supplementary_Indices_-_IDACI_and_IDAOPI.csv"
)
IMD_2019_SCORES_OF_DEPRIVATION = "File_5_-_IoD2019_Scores.csv"
IMD_2019_TRANSFORMED_SCORES_OF_DEPRIVATION = "File_9_-_IoD2019_Transformed_Scores.csv"
IMD_2019_LSOA_2015_POPULATION_DENOMINATORS = (
    "File_6_-_IoD2019_Population_Denominators.csv"
)
LSOA_2011_WARD_LAD_2019 = "Lower_Layer_Super_Output_Area_(2011)_to_Ward_(2019)_Lookup_in_England_and_Wales.csv"
SCOTTISH_DATA_ZONES_AND_LOCAL_AUTHORITIES = "scottish_dz_lookup.csv"
ACCESS_TO_GREEN_SPACE = "access_to_green_space.csv"  # 2020 data https://www.ons.gov.uk/economy/environmentalaccounts/datasets/accesstogardensandpublicgreenspaceingreatbritain

IMD_WALES_DEPRIVATION_DOMAINS_RANKS = (
    "welsh-index-multiple-deprivation-2019-index-and-domain-ranks-by-small-area.csv"
)

IMD_WALES_DEPRIVATION_SCORES = "wimd-2019-index-and-domain-scores-by-small-area.csv"
IMD_SCOTLAND_RANKS = "SIMD+2020v2.csv"
NORTHERN_IRELAND_SOAS_AND_IMD_RANKS = "NIMDM17_SOAresults.csv"

W = "\033[0m"  # white (normal)
R = "\033[31m"  # red
G = "\033[32m"  # green
O = "\033[33m"  # orange
B = "\033[34m"  # blue
P = "\033[35m"  # purple
BOLD = "\033[1m"
END = "\033[0m"


class Command(BaseCommand):
    help = "seed database with census and IMD data for England, Wales, Scotland and Northern Ireland."

    def add_arguments(self, parser):
        parser.add_argument("--mode", type=str, help="Mode")

    def handle(self, *args, **options):
        if options["mode"] == "add_organisational_areas":
            self.stdout.write(B + "Adding organisational areas..." + W)
            add_lsoas_2011_wards_2019_to_LADS_2019()
            add_scottish_data_zones_and_local_authorities()
            # add_2015_population_denominators()
            add_lad_access_to_outdoor_space()
        elif options["mode"] == "add_welsh_imds":
            self.stdout.write(B + "Adding Welsh IMDs to existing LSOAs" + W)
            add_welsh_2019_domains_and_ranks_to_existing_2019_lsoas()
            add_welsh_2019_scores_to_existing_2019_lsoas()
        elif options["mode"] == "add_english_imds":
            self.stdout.write(B + "Adding English IMDs to existing LSOAs" + W)
            add_english_deprivation_scores_and_domains_to_2011_lsoas()
            update_english_imd_data_with_subdomains()
            update_english_imd_data_with_supplementary_indices()
            update_english_imd_data_with_scores()
            update_english_imd_data_with_transformed_scores()
        elif options["mode"] == "add_scottish_imds":
            self.stdout.write(B + "Adding Scottish IMDs to existing Datazones" + W)
            add_scottish_deprivation_ranks_and_domains_to_2011_datazones()
        elif options["mode"] == "add_northern_ireland_imds":
            self.stdout.write(B + "Adding Northern Ireland SOAs and IMDs" + W)
            add_northern_ireland_soas_and_deprivation_domains_with_ranks()
        else:
            self.stdout.write("No options supplied...")
        self.stdout.write(image())
        self.stdout.write("done.")


def add_lsoas_2011_wards_2019_to_LADS_2019():
    # import LSOA 2011/Ward & LAD 2019 boundaries
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{LSOA_2011_WARD_LAD_2019}"

    if LocalAuthority.objects.exists() and LocalAuthority.objects.all().count() == 371:
        print(R + "Local Authorities already added. Skipping..." + W)
        pass
    else:
        lad_counter = 0
        lsoa_counter = 0

        with open(path, "r") as f:
            print(
                G
                + "- Adding English & Welsh 2019 Local Authority Districts and 2011 LSOAs..."
                + W,
                end="\n",
                flush=True,
            )
            data = list(csv.reader(f, delimiter=","))
            for row in data[1:]:
                (
                    local_authority_district_2019,
                    created,
                ) = LocalAuthority.objects.get_or_create(
                    local_authority_district_code=row[5],
                    local_authority_district_name=row[6],
                    year=2019,
                )
                if created:
                    lad_counter += 1

                LSOA.objects.create(
                    lsoa_code=row[1],
                    lsoa_name=row[2],
                    year=2011,
                    local_authority_district=local_authority_district_2019,
                )
                lsoa_counter += 1
                progress_bar(
                    iteration=lsoa_counter,
                    total=34753,
                    prefix="Progress",
                    suffix="Complete",
                )
        print(
            f"Complete. Added total {lad_counter} local authority districts and {lsoa_counter} lsoas.\n",
            flush=True,  # should be a total of 34753 LSOAs and 339 LADs
        )


def add_english_deprivation_scores_and_domains_to_2011_lsoas():
    # import domains of deprivation data

    if (
        EnglishIndexMultipleDeprivation.objects.exists()
        and EnglishIndexMultipleDeprivation.objects.count() == 32844
    ):
        print(R + "English indices already exist! Skipping..." + W)
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_DOMAINS_OF_DEPRIVATION}"
    with open(path, "r") as f:
        print(
            G
            + "- Adding English domains of deprivation to LSOAs with ranks and deciles"
            + W
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:  # skip the first row
            if LSOA.objects.filter(lsoa_code=row[0], year=2011).exists():
                lsoa = LSOA.objects.filter(lsoa_code=row[0], year=2011).get()

                EnglishIndexMultipleDeprivation.objects.create(
                    imd_rank=int(float(row[4])),
                    imd_decile=int(float(row[5])),
                    income_rank=int(float(row[6])),
                    income_decile=int(float(row[7])),
                    employment_rank=int(float(row[8])),
                    employment_decile=int(float(row[9])),
                    education_skills_training_rank=int(float(row[10])),
                    education_skills_training_decile=int(float(row[11])),
                    health_deprivation_disability_rank=int(float(row[12])),
                    health_deprivation_disability_decile=int(float(row[13])),
                    crime_rank=int(float(row[14])),
                    crime_decile=int(float(row[15])),
                    barriers_to_housing_services_rank=int(float(row[16])),
                    barriers_to_housing_services_decile=int(float(row[17])),
                    living_environment_rank=int(float(row[18])),
                    living_environment_decile=int(float(row[19])),
                    lsoa=lsoa,
                )
                count += 1

            progress_bar(
                iteration=count, total=32844, prefix="Progress", suffix="Complete"
            )
            # print(
            #     f"Added {count} records of English deprivation domains (ranks and deciles)",
            #     end="\r",
            # )  # 32844

    print(
        f"{BOLD}Complete.{END} {count} IMD records with domains added (ranks and deciles)\n"
    )


def update_english_imd_data_with_subdomains():
    # import subdomains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SUBDOMAINS_OF_DEPRIVATION}"
    with open(path, "r") as f:
        print(G + "- Adding sub-domains of deprivation to LSOAs" + W)
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:
            lsoa = LSOA.objects.get(lsoa_code=row[0])
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa).update(
                children_young_people_sub_domain_rank=int(float(row[6])),
                children_young_people_sub_domain_decile=int(float(row[7])),
                adult_skills_sub_domain_rank=int(float(row[8])),
                adult_skills_sub_domain_decile=int(float(row[9])),
                geographical_barriers_sub_domain_rank=int(float(row[12])),
                geographical_barriers_sub_domain_decile=int(float(row[13])),
                wider_barriers_sub_domain_rank=int(float(row[14])),
                wider_barriers_sub_domain_decile=int(float(row[15])),
                indoors_sub_domain_rank=int(float(row[18])),
                indoors_sub_domain_decile=int(float(row[19])),
                outdoors_sub_domain_rank=int(float(row[20])),
                outdoors_sub_domain_decile=int(float(row[21])),
            )
            count += 1

            progress_bar(
                iteration=count, total=32844, prefix="Progress", suffix="Complete"
            )
            # print(f"Updated {count} LSOAs with subdomains.", end="\r")
    print(
        f"{BOLD}Complete.{END} Added {count} subdomains of deprivation 2019 to LSOAs\n",
    )


def update_english_imd_data_with_supplementary_indices():
    # import domains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SUPPLEMENTARY_INDICES_OF_DEPRIVATION}"
    with open(path, "r") as f:
        print(
            G
            + "- Adding supplementary indices (IDACI and IDAOPI) of deprivation to LSOAs"
            + W
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:
            lsoa = LSOA.objects.get(lsoa_code=row[0])
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa).update(
                idaci_rank=int(float(row[6])),
                idaci_decile=int(float(row[7])),
                idaopi_rank=int(float(row[8])),
                idaopi_decile=int(float(row[9])),
            )
            count += 1
            progress_bar(
                iteration=count, total=32844, prefix="Progress", suffix="Complete"
            )
            # print(f"Updated {count} LSOAs with IDACI and IDAOPI data...", end="\r")
    print(
        f"{BOLD}Complete.{END} Added {count} supplementary indices (IDACI and IDAOPI) of deprivation 2019 to LSOAs\n"
    )


def update_english_imd_data_with_scores():
    if EnglishIndexMultipleDeprivation.objects.all()[0].imd_score is not None:
        print("IMD scores already exist for England. Skipping...")
        return
    # import domains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SCORES_OF_DEPRIVATION}"
    with open(path, "r") as f:
        print(G + "- Adding English scores of deprivation to LSOAs" + W)
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:
            lsoa = LSOA.objects.get(lsoa_code=row[0])
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa).update(
                imd_score=Decimal(row[4]),
                income_score=Decimal(row[5]),
                employment_score=Decimal(row[6]),
                education_skills_training_score=Decimal(row[7]),
                health_deprivation_disability_score=Decimal(row[8]),
                crime_score=Decimal(row[9]),
                barriers_to_housing_services_score=Decimal(row[10]),
                living_environment_score=Decimal(row[11]),
                idaci_score=Decimal(row[12]),
                idaopi_score=Decimal(row[13]),
                children_young_people_sub_domain_score=Decimal(row[14]),
                adult_skills_sub_domain_score=Decimal(row[15]),
                geographical_barriers_sub_domain_score=Decimal(row[16]),
                wider_barriers_sub_domain_score=Decimal(row[17]),
                indoors_sub_domain_score=Decimal(row[18]),
                outdoors_sub_domain_score=Decimal(row[19]),
            )
            count += 1
            progress_bar(
                iteration=count, total=32844, prefix="Progress", suffix="Complete"
            )
            # print(
            #     f"Updated {count} indices of deprivation 2019 with scores...", end="\r"
            # )
    print(f"{BOLD}Complete.{END} Added {count} English scores of deprivation 2019\n")


def update_english_imd_data_with_transformed_scores():
    # import domains of deprivation data
    path = (
        f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_TRANSFORMED_SCORES_OF_DEPRIVATION}"
    )
    with open(path, "r") as f:
        print(G + "- Adding English transformed scores of deprivation to LSOAs" + W)
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:
            lsoa = LSOA.objects.get(lsoa_code=row[0])
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa).update(
                income_score_exponentially_transformed=Decimal(row[4]),
                employment_score_exponentially_transformed=Decimal(row[5]),
                education_skills_training_score_exponentially_transformed=Decimal(
                    row[6]
                ),
                health_deprivation_disability_score_exponentially_transformed=Decimal(
                    row[7]
                ),
                crime_score_exponentially_transformed=Decimal(row[8]),
                barriers_to_housing_services_score_exponentially_transformed=Decimal(
                    row[9]
                ),
                living_environment_score_exponentially_transformed=Decimal(row[10]),
            )
            count += 1
            progress_bar(
                iteration=count, total=32844, prefix="Progress", suffix="Complete"
            )
            # print(
            #     f"Updated {count} records with transformed scores of deprivation 2019...",
            #     end="\r",
            # )
    print(
        f"{BOLD}Complete.{END} Added {count} English transformed scores of deprivation 2019\n"
    )


def add_scottish_data_zones_and_local_authorities():
    """
    Add data zones and scottish local authorities
    """
    path = (
        f"{settings.IMD_DATA_FILES_FOLDER}/{SCOTTISH_DATA_ZONES_AND_LOCAL_AUTHORITIES}"
    )
    with open(path, "r", encoding="windows-1252") as f:
        print(G + "- Adding 2011 Scottish Data Zones and Local Authorities" + W)
        data = list(csv.reader(f, delimiter=","))
        lad_count = 0
        dz_count = 0

        for row in data[1:]:
            local_authority, created = LocalAuthority.objects.get_or_create(
                local_authority_district_code=row[6],
                local_authority_district_name=row[7],
                year=2011,
            )

            if created:
                lad_count += 1

            data_zone, created = DataZone.objects.get_or_create(
                data_zone_code=row[0],
                data_zone_name=row[1],
                year=2011,
                local_authority=local_authority,
            )

            if created:
                dz_count += 1
            print(
                f"Added {lad_count} Scottish Local Authorities and {dz_count} data zones...",
                end="\r",
            )
            # progress_bar(current=dz_count, total=6976, bar_length=40)
    print(
        f"{BOLD}Complete.{END} Added {lad_count} Scottish Local Authorities and {dz_count} data zones...\n",
    )


def add_2015_population_denominators():
    # import domains of deprivation data
    # note this includes scotland so must load data zones first
    path = (
        f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_LSOA_2015_POPULATION_DENOMINATORS}"
    )
    with open(path, "r") as f:
        print(G + "- Adding 2015 population denominators to LSOAs" + W)
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:
            LSOA.objects.filter(lsoa_code=row[0]).update(
                total_population_mid_2015=int(float(row[4])),
                dependent_children_mid_2015=int(float(row[5])),
                population_16_59_mid_2015=int(float(row[6])),
                older_population_over_16_mid_2015=int(float(row[7])),
                working_age_population_over_18_mid_2015=int(float(row[8])),
            )

            count += 1
            print(
                f"Updated {count} LSOAs with 2015 Population Denominators...", end="\r"
            )
    print(f"{BOLD}Complete.{END} Added {count} 2015 population denominators to LSOAs\n")


def add_lad_access_to_outdoor_space():
    # import domains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{ACCESS_TO_GREEN_SPACE}"
    with open(path, "r") as f:
        print(G + "- Adding Local Authority green space records." + W)
        data = list(csv.reader(f, delimiter=","))
        count = 0

    for row in data[2:]:  # header is on row 3
        local_authority = LocalAuthority.objects.get(
            local_authority_district_code=row[4]
        )
        if GreenSpace.objects.filter(local_authority=local_authority).exists():
            print("Greenspace data already available for this Local Authority")
            pass
        else:
            GreenSpace.objects.create(
                local_authority=local_authority,
                houses_address_count=int(float(row[6])),
                houses_addresses_with_private_outdoor_space_count=int(float(row[7])),
                houses_outdoor_space_total_area=int(float(row[8])),
                houses_percentage_of_addresses_with_private_outdoor_space=int(
                    float(row[9])
                ),
                houses_average_size_private_outdoor_space=int(float(row[10])),
                houses_median_size_private_outdoor_space=int(float(row[11])),
                flats_address_count=int(float(row[12])),
                flats_addresses_with_private_outdoor_space_count=int(float(row[13])),
                flats_outdoor_space_total_area=int(float(row[14])),
                flats_outdoor_space_count=int(float(row[15])),
                flats_percentage_of_addresses_with_private_outdoor_space=int(
                    float(row[16])
                ),
                flats_average_size_private_outdoor_space=int(float(row[17])),
                flats_average_number_of_flats_sharing_a_garden=int(float(row[18])),
                total_addresses_count=int(float(row[19])),
                total_addresses_with_private_outdoor_space_count=int(float(row[20])),
                total_percentage_addresses_with_private_outdoor_space=int(
                    float(row[21])
                ),
                total_average_size_private_outdoor_space=int(float(row[22])),
            )

            count += 1
            progress_bar(
                iteration=count, total=371, prefix="Progress", suffix="Complete"
            )
            # print(f"Created {count} Local Authority green space records...", end="\r")
    print(f"{BOLD}Complete.{END} Added {count} Local Authority green space records.\n")


def add_welsh_2019_domains_and_ranks_to_existing_2019_lsoas():
    """
    import Welsh domains and ranks 2019 data
    """
    if (
        WelshIndexMultipleDeprivation.objects.exists()
        and WelshIndexMultipleDeprivation.objects.count() == 1909
    ):
        print(R + "Welsh indices already present. Skipping..." + W)
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_WALES_DEPRIVATION_DOMAINS_RANKS}"
    with open(path, "r") as f:
        print(G + "- Adding Welsh IMD ranks/quantiles" + W)
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for record in data[1:]:
            lsoa = LSOA.objects.get(lsoa_code=record[0])
            WelshIndexMultipleDeprivation.objects.create(
                imd_rank=int(record[3]),
                imd_quartile=quantile_for_rank(
                    rank=int(record[3]), quantile="quartile"
                ),
                imd_quintile=quantile_for_rank(
                    rank=int(record[3]), quantile="quintile"
                ),
                imd_decile=quantile_for_rank(rank=int(record[3]), quantile="decile"),
                imd_score=None,
                income_rank=int(record[4]),
                income_quartile=quantile_for_rank(
                    rank=int(record[4]), quantile="quartile"
                ),
                income_quintile=quantile_for_rank(
                    rank=int(record[4]), quantile="quintile"
                ),
                income_decile=quantile_for_rank(rank=int(record[4]), quantile="decile"),
                income_score=None,
                employment_rank=int(record[5]),
                employment_quartile=quantile_for_rank(
                    rank=int(record[5]), quantile="quartile"
                ),
                employment_quintile=quantile_for_rank(
                    rank=int(record[5]), quantile="quintile"
                ),
                employment_decile=quantile_for_rank(
                    rank=int(record[5]), quantile="decile"
                ),
                employment_score=None,
                health_rank=int(record[6]),
                health_quartile=quantile_for_rank(
                    rank=int(record[6]), quantile="quartile"
                ),
                health_quintile=quantile_for_rank(
                    rank=int(record[6]), quantile="quintile"
                ),
                health_decile=quantile_for_rank(rank=int(record[6]), quantile="decile"),
                health_score=None,
                education_rank=int(record[7]),
                education_quartile=quantile_for_rank(
                    rank=int(record[7]), quantile="quartile"
                ),
                education_quintile=quantile_for_rank(
                    rank=int(record[7]), quantile="quintile"
                ),
                education_decile=quantile_for_rank(
                    rank=int(record[7]), quantile="decile"
                ),
                education_score=None,
                access_to_services_rank=int(record[8]),
                access_to_services_quartile=quantile_for_rank(
                    rank=int(record[8]), quantile="quartile"
                ),
                access_to_services_quintile=quantile_for_rank(
                    rank=int(record[8]), quantile="quintile"
                ),
                access_to_services_decile=quantile_for_rank(
                    rank=int(record[8]), quantile="decile"
                ),
                access_to_services_score=None,
                housing_rank=int(record[9]),
                housing_quartile=quantile_for_rank(
                    rank=int(record[9]), quantile="quartile"
                ),
                housing_quintile=quantile_for_rank(
                    rank=int(record[9]), quantile="quintile"
                ),
                housing_decile=quantile_for_rank(
                    rank=int(record[9]), quantile="decile"
                ),
                housing_score=None,
                community_safety_rank=int(record[10]),
                community_safety_quartile=quantile_for_rank(
                    rank=int(record[10]), quantile="quartile"
                ),
                community_safety_quintile=quantile_for_rank(
                    rank=int(record[10]), quantile="quintile"
                ),
                community_safety_decile=quantile_for_rank(
                    rank=int(record[10]), quantile="decile"
                ),
                community_safety_score=None,
                physical_environment_rank=int(record[11]),
                physical_environment_quartile=quantile_for_rank(
                    rank=int(record[11]), quantile="quartile"
                ),
                physical_environment_quintile=quantile_for_rank(
                    rank=int(record[11]), quantile="quintile"
                ),
                physical_environment_decile=quantile_for_rank(
                    rank=int(record[11]), quantile="decile"
                ),
                physical_environment_score=None,
                lsoa=lsoa,
                year=2019,
            )
            progress_bar(
                iteration=count, total=1909, prefix="Progress", suffix="Complete"
            )
            count += 1
    print(
        f"{BOLD}Complete.{END} Added {count} Welsh IMD ranks/quantiles.\n"
    )  # should be 1909


def add_welsh_2019_scores_to_existing_2019_lsoas():
    """
    import Welsh IMD scores 2019 and add to existing ranks/imds
    """
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_WALES_DEPRIVATION_SCORES}"
    with open(path, "r") as f:
        print(G + "- Adding Welsh IMD scores" + W)
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for record in data[1:]:
            lsoa = LSOA.objects.get(lsoa_code=record[0])
            WelshIndexMultipleDeprivation.objects.filter(lsoa=lsoa).update(
                imd_score=record[3],
                income_score=record[4],
                employment_score=record[5],
                health_score=record[6],
                education_score=record[7],
                access_to_services_score=record[8],
                housing_score=record[9],
                community_safety_score=record[10],
                physical_environment_score=record[11],
                lsoa=lsoa,
                year=2019,
            )
            progress_bar(
                iteration=count, total=1909, prefix="Progress", suffix="Complete"
            )
            count += 1
    print(f"{BOLD}Complete.{END} Added {count} Welsh IMD scores.\n")  # should be 1909


def add_northern_ireland_soas_and_deprivation_domains_with_ranks():
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{NORTHERN_IRELAND_SOAS_AND_IMD_RANKS}"

    if SOA.objects.exists() and SOA.objects.all().count() == 890:
        print(R + "Northern Ireland SOAs already added. Skipping..." + W)
        pass
    else:
        imd_counter = 0

        with open(path, "r") as f:
            print(
                G
                + "- Adding Northern Ireland 2001 SOAs and 2017 deprivation domains and ranks...\n"
                + W
            )
            data = list(csv.reader(f, delimiter=","))
            for row in data[1:891]:
                soa = SOA.objects.create(soa_code=row[2], soa_name=row[3], year=2001)

                NorthernIrelandIndexMultipleDeprivation.objects.create(
                    year=2017,
                    imd_rank=row[4],
                    income_rank=row[5],
                    employment_rank=row[6],
                    health_deprivation_and_disability_rank=row[7],
                    education_skills_and_training_rank=row[8],
                    access_to_services_rank=row[9],
                    living_environment_rank=row[10],
                    crime_and_disorder_rank=row[11],
                    soa=soa,
                )

                progress_bar(
                    iteration=imd_counter,
                    total=891,
                    prefix="Progress",
                    suffix="Complete",
                )
                imd_counter += 1
    print(
        f"{BOLD}Complete.{END} {imd_counter} Northern Ireland SOAs and IMD domains and ranks added."
        + W
    )


def calculated_quantile_for_rank(rank, total_records, quantile_type):
    """
    Return a quantile against a rank and a total
    Params:
    rank: integer - represents rank in a list of records
    total_records: integer - represents the total number of records
    quantile_type: integer - the number of equally sized groups the records are divided into
    """
    quantile_names = [
        "median",
        "tertile",
        "quartile",
        "quintile",
        "sextile",
        "septile",
        "octile",
        "decile",
        "duodecile",
        "hexadecile",
        "vigintile",
    ]

    tile_size = floor(total_records / quantile_type)
    if tile_size <= rank:
        return 1
    else:
        return floor(rank / tile_size)


def quantile_for_rank(rank, quantile=Literal["quartile", "quintile", "decile"]):
    """
    returns a quantile for a rank in WIMD data

    WIMD 2019 Rank	Decile
            1-191	    1
            192-382	    2
            383-573	    3
            574-764	    4
            765-955	    5
            956-1146	6
            1147-1337	7
            1338-1528	8
            1529-1719	9
            1720-1909	10
    WIMD 2019 Rank	Quintile
            1-382	    1
            383-764	    2
            765-1146	3
            1147-1528	4
            1529-1909	5
    WIMD 2019 Rank	Quartile
            1-478	    1
            479-955	    2
            956-1432	3
            1433-1909	4
    """
    if (
        (quantile == "quartile" and rank <= 478)
        or (rank <= 191 and quantile == "decile")
        or (rank <= 382 and quantile == "quintile")
    ):
        return 1
    elif (
        (quantile == "quartile" and rank <= 955)
        or (rank <= 382 and quantile == "decile")
        or (rank <= 764 and quantile == "quintile")
    ):
        return 2
    elif (
        (quantile == "quartile" and rank <= 1432)
        or (rank <= 573 and quantile == "decile")
        or (rank <= 1146 and quantile == "quintile")
    ):
        return 3
    elif (
        (quantile == "quartile" and rank <= 1909)
        or (rank <= 764 and quantile == "decile")
        or (rank <= 1528 and quantile == "quintile")
    ):
        return 4
    elif (rank <= 955 and quantile == "decile") or (
        rank <= 1909 and quantile == "quintile"
    ):
        return 5
    elif rank <= 1146 and quantile == "decile":
        return 6
    elif rank <= 1337 and quantile == "decile":
        return 7
    elif rank <= 1528 and quantile == "decile":
        return 8
    elif rank <= 1719 and quantile == "decile":
        return 9
    elif rank <= 1909 and quantile == "decile":
        return 10
    else:
        raise ValueError(f"Incorrect rank {rank} passed for {quantile}")


def add_scottish_deprivation_ranks_and_domains_to_2011_datazones():
    # import domains of deprivation data

    if (
        ScottishIndexMultipleDeprivation.objects.exists()
        and ScottishIndexMultipleDeprivation.objects.count() == 6976
    ):
        print(R + "Scottish indices already exist! Skipping..." + W)
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_SCOTLAND_RANKS}"
    with open(path, "r") as f:
        print(
            G
            + "- Adding Scottish domains of deprivation to data zones with ranks\n"
            + W
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:  # skip the first row
            if DataZone.objects.filter(data_zone_code=row[0], year=2011).exists():
                data_zone = DataZone.objects.filter(
                    data_zone_code=row[0], year=2011
                ).get()

                ScottishIndexMultipleDeprivation.objects.create(
                    imd_rank=row[2],
                    version=2,
                    income_rank=round(float(row[6])),
                    employment_rank=round(float(row[7])),
                    education_rank=round(float(row[8])),
                    health_rank=round(float(row[9])),
                    access_rank=round(float(row[10])),
                    crime_rank=round(float(row[11])),
                    housing_rank=round(float(row[12])),
                    data_zone=data_zone,
                    year=2020,
                )
                count += 1

            progress_bar(
                iteration=count, total=6976, prefix="Progress", suffix="Complete"
            )
            # print(
            #     f"Added {count} records of English deprivation domains (ranks and deciles)",
            #     end="\r",
            # )  # 32844

    print(
        f"{BOLD}Complete.{END} {count} Scottish IMD records with domains added (ranks).\n"
    )


def progress_bar(
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=100,
    fill="█",
    printEnd="\r",
):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def image():
    return """

                                .^~^      ^777777!~:       ^!???7~:
                                ^JJJ:.:!^ 7#BGPPPGBGY:   !5BBGPPGBBY.
                                 :~!!?J~. !BBJ    YBB?  ?BB5~.  .~J^
                              .:~7?JJ?:   !BBY^~~!PBB~ .GBG:
                              .~!?JJJJ^   !BBGGGBBBY^  .PBG^
                                 ?J~~7?:  !BBJ.:?BB5^   ~GBG?^:^~JP7
                                :?:   .   !BBJ   ~PBG?.  :?PBBBBBG5!
                                ..::...     .::. ...:^::. .. .:^~~^:.
                                !GPGGGGPY7.   :!?JJJJ?7~..PGP:    !GGJ
                                7BBY~~!YBBY  !JJ?!^^^!??::GBG:    7BBJ
                                7BB?   .GBG.^JJ7.     .. .GBG!^^^^JBBJ
                                7BB577?5BBJ ~JJ!         .GBBGGGGGGBBJ
                                7BBGPPP5J~  :JJJ^.   .^^ .GBG^.::.?BBJ
                                7#B?         :7JJ?77?JJ?^:GBB:    7##Y
                                ~YY!           :~!77!!^. .JYJ.    ~YY7


                                       RCPCH Census Platform 2022

                """
