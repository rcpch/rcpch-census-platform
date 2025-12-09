from enum import Enum
from math import floor
import sys
import csv
from decimal import Decimal
from django.core.management.base import BaseCommand
from tqdm import tqdm
from django.conf import settings
from ...models import (
    LSOA,
    LocalAuthority,
    Ward,
    GreenSpace,
    DataZone,
    SOA,
    EnglishIndexMultipleDeprivation,
    WelshIndexMultipleDeprivation,
    ScottishIndexMultipleDeprivation,
    NorthernIrelandIndexMultipleDeprivation,
    PopulationDensity,
)


class QuantileType(Enum):
    QUARTILE = "quartile"
    QUINTILE = "quintile"
    DECILE = "decile"


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

IMD_2025_DOMAINS_OF_DEPRIVATION = "File_2_IoD2025_Domains_of_Deprivation.csv"
IMD_2025_SUBDOMAINS_OF_DEPRIVATION = "File_4_IoD2025_Sub-domains_of_Deprivation.csv"
IMD_2025_SUPPLEMENTARY_INDICES_OF_DEPRIVATION = (
    "File_3_IoD2025_Supplementary_Indices_IDACI_and_IDAOPI.csv"
)
IMD_2025_SCORES_OF_DEPRIVATION = (
    "File_5_IoD2025_Scores_for_the_Indices_of_Deprivation.csv"
)
IMD_2025_TRANSFORMED_SCORES_OF_DEPRIVATION = (
    "File_9_IoD2025_Transformed_Domain_Scores.csv"
)

LSOA_2021_WARD_LAD_2024 = (
    "LSOA_(2021)_to_Electoral_Ward_(2024)_to_LAD_(2024)_Best_Fit_Lookup_in_EW.csv"
)

SCOTTISH_DATA_ZONES_AND_LOCAL_AUTHORITIES = "scottish_dz_lookup.csv"
ACCESS_TO_GREEN_SPACE = "access_to_green_space.csv"  # 2020 data https://www.ons.gov.uk/economy/environmentalaccounts/datasets/accesstogardensandpublicgreenspaceingreatbritain

IMD_WALES_DEPRIVATION_DOMAINS_RANKS = (
    "welsh-index-multiple-deprivation-2019-index-and-domain-ranks-by-small-area.csv"
)

IMD_WALES_DEPRIVATION_SCORES = "wimd-2019-index-and-domain-scores-by-small-area.csv"
IMD_SCOTLAND_RANKS = "SIMD+2020v2.csv"
NORTHERN_IRELAND_SOAS_AND_IMD_RANKS = "NIMDM17_SOAresults.csv"

POPULATION_DENSITIES = "Access_to_Natural_Green_Space_Inequalities__(LSOA).csv"


W = "\033[0m"  # white (normal)
R = "\033[31m"  # red
G = "\033[32m"  # green
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
            add_lsoas_2021_wards_2024_to_LADS_2024()
            add_scottish_data_zones_and_local_authorities()
            # add_2015_population_denominators()
            add_lad_access_to_outdoor_space()
        elif options["mode"] == "add_welsh_imds":
            self.stdout.write(
                "\n" + B + "Adding Welsh IMDs to existing LSOAs" + W + "\n"
            )
            add_welsh_2019_domains_and_ranks_to_existing_2011_lsoas()
            add_welsh_2019_scores_to_existing_2011_lsoas()
        elif options["mode"] == "add_english_imds":
            self.stdout.write(
                "\n" + B + "Adding 2019 English IMDs to existing 2011 LSOAs" + W + "\n"
            )
            add_english_deprivation_scores_and_domains_to_2011_lsoas()
            update_english_imd_data_with_subdomains()
            update_english_imd_data_with_supplementary_indices()
            update_english_imd_data_with_scores()
            update_english_imd_data_with_transformed_scores()
            # 2025 IMD data for 2021 LSOAs
            self.stdout.write(
                "\n" + B + "Adding 2025 English IMDs to existing 2021 LSOAs" + W + "\n"
            )
            add_english_2025_deprivation_scores_and_domains_to_2021_lsoas()
            update_english_2025_imd_data_with_subdomains()
            update_english_2025_imd_data_with_supplementary_indices()
            update_english_2025_imd_data_with_scores()
            update_english_2025_imd_data_with_transformed_scores()
        elif options["mode"] == "add_scottish_imds":
            self.stdout.write(
                "\n" + B + "Adding Scottish IMDs to existing Datazones" + W + "\n"
            )
            add_scottish_deprivation_ranks_and_domains_to_2011_datazones()
        elif options["mode"] == "add_northern_ireland_imds":
            self.stdout.write(
                "\n" + B + "Adding Northern Ireland SOAs and IMDs" + W + "\n"
            )
            add_northern_ireland_soas_and_deprivation_domains_with_ranks()
        elif options["mode"] == "add_population_densities":
            self.stdout.write("\n" + B + "Adding population densities..." + W + "\n")
            update_population_densities()
        elif options["mode"] == "__all__":
            self.stdout.write("\n" + B + "Seeding all data..." + W + "\n")
            self.stdout.write("\n" + B + "Adding organisational areas..." + W + "\n")
            add_lsoas_2011_wards_2019_to_LADS_2019()
            add_lsoas_2021_wards_2024_to_LADS_2024()
            add_scottish_data_zones_and_local_authorities()
            # add_2015_population_denominators()
            add_lad_access_to_outdoor_space()
            self.stdout.write(
                "\n" + B + "Adding 2019 English IMDs to existing 2011 LSOAs" + W + "\n"
            )
            add_english_deprivation_scores_and_domains_to_2011_lsoas()
            update_english_imd_data_with_subdomains()
            update_english_imd_data_with_supplementary_indices()
            update_english_imd_data_with_scores()
            update_english_imd_data_with_transformed_scores()
            self.stdout.write(
                "\n" + B + "Adding 2025 English IMDs to existing 2021 LSOAs" + W + "\n"
            )
            add_english_2025_deprivation_scores_and_domains_to_2021_lsoas()
            update_english_2025_imd_data_with_subdomains()
            update_english_2025_imd_data_with_supplementary_indices()
            update_english_2025_imd_data_with_scores()
            update_english_2025_imd_data_with_transformed_scores()
            self.stdout.write(
                "\n" + B + "Adding Welsh 2019 IMDs to existing 2011 LSOAs" + W + "\n"
            )
            add_welsh_2019_domains_and_ranks_to_existing_2011_lsoas()
            add_welsh_2019_scores_to_existing_2011_lsoas()
            self.stdout.write(
                "\n" + B + "Adding Scottish IMDs to existing Datazones" + W + "\n"
            )
            add_scottish_deprivation_ranks_and_domains_to_2011_datazones()
            self.stdout.write(
                "\n" + B + "Adding Northern Ireland SOAs and IMDs" + W + "\n"
            )
            add_northern_ireland_soas_and_deprivation_domains_with_ranks()
            self.stdout.write("\n" + B + "Adding population densities..." + W + "\n")
            update_population_densities()
            test_table_totals()
        elif options["mode"] == "test_table_totals":
            test_table_totals()
        else:
            self.stdout.write("No options supplied...")
        self.stdout.write(image())
        self.stdout.write("done.")


"""
England and Wales LSOAs, Wards and LADS
"""


def add_lsoas_2011_wards_2019_to_LADS_2019():
    # import LSOA 2011/Ward & LAD 2019 boundaries
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{LSOA_2011_WARD_LAD_2019}"

    if (
        LocalAuthority.objects.exists() and LocalAuthority.objects.all().count() >= 371
    ) or (LSOA.objects.exists() and LSOA.objects.all().count() >= 34753):
        sys.stdout.write(
            "\n"
            + R
            + "Local Authorities and LSOAs already added. Skipping..."
            + W
            + "\n"
        )
        return
    else:
        lad_counter = 0
        lsoa_counter = 0

        with open(path, "r") as f:
            sys.stdout.write(
                "\n"
                + G
                + "📎 Adding English & Welsh 2019 Local Authority Districts and 2011 LSOAs..."
                + W
                + "\n"
            )
            data = list(csv.reader(f, delimiter=","))

            for row in tqdm(data[1:], ascii=True, desc="Adding 2011 LSOAs & 2019 LADs"):
                local_authority_district_2019, created = (
                    LocalAuthority.objects.get_or_create(
                        local_authority_district_code=row[5],
                        year=2019,
                        defaults={
                            "local_authority_district_name": row[6],
                        },
                    )
                )
                if created:
                    lad_counter += 1

                _, created = LSOA.objects.get_or_create(
                    lsoa_code=row[1],
                    year=2011,
                    defaults={
                        "lsoa_name": row[2],
                        "local_authority_district": local_authority_district_2019,
                    },
                )
                if created:
                    lsoa_counter += 1
        final = f"  Added total {lad_counter} local authority districts and {lsoa_counter} lsoas."
        sys.stdout.write(BOLD + "\n🔥 Complete." + END + final + W + "\n")
        try:
            assert lsoa_counter == 34753
        except AssertionError:
            sys.stdout.write(
                "\n"
                + R
                + f"😬 Expected 34753 lsoa records, but got {lsoa_counter}."
                + W
                + "\n"
            )
        try:
            assert lad_counter == 339
        except AssertionError:
            sys.stdout.write(
                "\n"
                + R
                + f"😬 Expected 339 lad records, but got {lad_counter}."
                + W
                + "\n"
            )
            pass


def add_lsoas_2021_wards_2024_to_LADS_2024():
    # import LSOA 2021/Ward & LAD 2024 boundaries
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{LSOA_2021_WARD_LAD_2024}"
    if (
        LocalAuthority.objects.exists()
        and LocalAuthority.objects.filter(year=2024).exists()
    ) or (LSOA.objects.exists() and LSOA.objects.filter(year=2021).exists()):
        sys.stdout.write(
            "\n"
            + R
            + "2024 Local Authorities and 2021 LSOAs already added. Skipping..."
            + W
            + "\n"
        )
        return
    else:
        lad_counter = 0
        lsoa_counter = 0

        with open(path, "r", encoding="utf-8") as f:
            sys.stdout.write(
                "\n"
                + G
                + "📎 Adding English & Welsh 2024 Local Authority Districts and 2021 LSOAs..."
                + W
                + "\n"
            )
            data = list(csv.reader(f, delimiter=","))

            for row in tqdm(data[1:], desc="Adding 2021 LSOAs & 2024 LADs"):
                local_authority_district_2024, created = (
                    LocalAuthority.objects.get_or_create(
                        local_authority_district_code=row[6],
                        year=2024,
                        defaults={
                            "local_authority_district_name": row[7],
                        },
                    )
                )
                if created:
                    lad_counter += 1

                _, created = LSOA.objects.get_or_create(
                    lsoa_code=row[0],
                    year=2021,
                    defaults={
                        "lsoa_name": row[1],
                        "local_authority_district": local_authority_district_2024,
                    },
                )
                if created:
                    lsoa_counter += 1
        final = f"  Added total {lad_counter} 2024 local authority districts and {lsoa_counter} 2021 lsoas."
        sys.stdout.write(BOLD + "\n🔥 Complete." + END + final + W + "\n")
        try:
            assert lsoa_counter == 35672
        except AssertionError:
            sys.stdout.write(
                "\n"
                + R
                + f"😬 Expected 35672 lsoa records, but got {lsoa_counter}."
                + W
                + "\n"
            )
        try:
            assert lad_counter == 318
        except AssertionError:
            sys.stdout.write(
                "\n"
                + R
                + f"😬 Expected 318 lad records, but got {lad_counter}."
                + W
                + "\n"
            )
            pass


"""
2019 English IMD data
"""


def add_english_deprivation_scores_and_domains_to_2011_lsoas():
    # import domains of deprivation data

    if (
        EnglishIndexMultipleDeprivation.objects.exists()
        and EnglishIndexMultipleDeprivation.objects.count() >= 32844
    ):
        sys.stdout.write(
            "\n" + R + "⏭️ English indices already exist! Skipping..." + W + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_DOMAINS_OF_DEPRIVATION}"
    with open(path, "r") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding English domains of deprivation to LSOAs with ranks and deciles"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in tqdm(
            data[1:], ascii=True, desc="Adding 2019 English IMD domains"
        ):  # skip the first row
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
                    year=2019,
                )
                count += 1
    final = f" {count} IMD records with domains added (ranks and deciles)\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )
        pass


def update_english_imd_data_with_subdomains():
    # import subdomains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SUBDOMAINS_OF_DEPRIVATION}"
    sys.stdout.write(
        "\n" + G + "📎 - Adding sub-domains of deprivation to LSOAs" + W + "\n"
    )
    with open(path, "r") as f:
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in tqdm(
            data[1:], ascii=True, desc="Adding 2019 subdomains"
        ):  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2011)
            except LSOA.DoesNotExist:
                sys.stderr.write(R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W)
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2011).update(
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
    final = f" Added {count} subdomains of deprivation 2019 to LSOAs\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )
        pass


def update_english_imd_data_with_supplementary_indices():
    # import domains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SUPPLEMENTARY_INDICES_OF_DEPRIVATION}"
    with open(path, "r") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding supplementary indices (IDACI and IDAOPI) of deprivation to LSOAs"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in tqdm(
            data[1:], desc="Adding 2019 supplementary indices"
        ):  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2011)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W + "\n"
                )
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2011).update(
                idaci_rank=int(float(row[6])),
                idaci_decile=int(float(row[7])),
                idaopi_rank=int(float(row[8])),
                idaopi_decile=int(float(row[9])),
            )
            count += 1
    final = f" Added {count} supplementary indices (IDACI and IDAOPI) of deprivation 2019 to LSOAs\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )
        pass


def update_english_imd_data_with_scores():
    # import domains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SCORES_OF_DEPRIVATION}"
    with open(path, "r") as f:
        sys.stdout.write(
            "\n" + G + "📎 - Adding English scores of deprivation to LSOAs" + W + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0
        for row in tqdm(data[1:], desc="Adding 2019 scores"):  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2011)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    "\n" + R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W + "\n"
                )
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2011).update(
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
                year=2019,
            )
            count += 1
    final = f" Added {count} English scores of deprivation 2019\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )
        pass


def update_english_imd_data_with_transformed_scores():
    # import domains of deprivation data
    path = (
        f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_TRANSFORMED_SCORES_OF_DEPRIVATION}"
    )
    sys.stdout.write(
        "\n"
        + G
        + "📎 - Adding English transformed scores of deprivation to LSOAs"
        + W
        + "\n"
    )
    with open(path, "r") as f:
        data = list(csv.reader(f, delimiter=","))
        count = 0
        for row in tqdm(data[1:], desc="Adding 2019 transformed scores"):
            lsoa = LSOA.objects.get(lsoa_code=row[0], year=2011)
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2011).update(
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
    final = f" Added {count} English transformed scores of deprivation 2019\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )
        pass


"""
England  IMD 2025 data
"""


def add_english_2025_deprivation_scores_and_domains_to_2021_lsoas():
    """
    Import 2025 domains of deprivation data for 2021 LSOAs
    """
    if (
        EnglishIndexMultipleDeprivation.objects.filter(lsoa__year=2021).exists()
        and EnglishIndexMultipleDeprivation.objects.filter(lsoa__year=2021).count()
        >= 33755
    ):
        sys.stdout.write(
            "\n" + R + "⏭️ English 2025 indices already exist! Skipping..." + W + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/2025/{IMD_2025_DOMAINS_OF_DEPRIVATION}"
    with open(path, "r", encoding="utf-8") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding English 2025 domains of deprivation to 2021 LSOAs with ranks and deciles"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in tqdm(
            data[1:], desc="Adding 2025 English IMD domains"
        ):  # skip the first row
            if LSOA.objects.filter(lsoa_code=row[0], year=2021).exists():
                lsoa = LSOA.objects.filter(lsoa_code=row[0], year=2021).get()

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
                    year=2025,
                )
                count += 1
    final = f" {count} IMD 2025 records with domains added (ranks and deciles)\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 33755
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 33755 records, but got {count}." + W + "\n"
        )
        pass


def update_english_2025_imd_data_with_subdomains():
    """
    Import 2025 subdomains of deprivation data
    """
    path = f"{settings.IMD_DATA_FILES_FOLDER}/2025/{IMD_2025_SUBDOMAINS_OF_DEPRIVATION}"
    sys.stdout.write(
        "\n" + G + "📎 - Adding 2025 sub-domains of deprivation to LSOAs" + W + "\n"
    )
    with open(path, "r", encoding="utf-8") as f:
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in tqdm(data[1:], desc="Adding 2025 subdomains"):  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2021)
            except LSOA.DoesNotExist:
                sys.stderr.write(R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W)
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2025).update(
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
    final = f" Added {count} subdomains of deprivation 2025 to LSOAs\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 33755
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 33755 records, but got {count}." + W + "\n"
        )
        pass


def update_english_2025_imd_data_with_supplementary_indices():
    """
    Import 2025 supplementary indices (IDACI and IDAOPI) data
    """
    path = f"{settings.IMD_DATA_FILES_FOLDER}/2025/{IMD_2025_SUPPLEMENTARY_INDICES_OF_DEPRIVATION}"
    with open(path, "r", encoding="utf-8") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding 2025 supplementary indices (IDACI and IDAOPI) of deprivation to LSOAs"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in tqdm(
            data[1:], desc="Adding 2025 supplementary indices"
        ):  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2021)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W + "\n"
                )
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa).update(
                idaci_rank=int(float(row[6])),
                idaci_decile=int(float(row[7])),
                idaopi_rank=int(float(row[8])),
                idaopi_decile=int(float(row[9])),
            )
            count += 1
    final = f" Added {count} supplementary indices (IDACI and IDAOPI) of deprivation 2025 to LSOAs\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 33755
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 33755 records, but got {count}." + W + "\n"
        )
        pass


def update_english_2025_imd_data_with_scores():
    """
    Import 2025 scores of deprivation data
    """
    path = f"{settings.IMD_DATA_FILES_FOLDER}/2025/{IMD_2025_SCORES_OF_DEPRIVATION}"
    with open(path, "r", encoding="utf-8") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding English 2025 scores of deprivation to LSOAs"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0
        for row in tqdm(data[1:], desc="Adding 2025 scores"):  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2021)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    "\n" + R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W + "\n"
                )
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2025).update(
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
    final = f" Added {count} English scores of deprivation 2025\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 33755
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 33755 records, but got {count}." + W + "\n"
        )
        pass


def update_english_2025_imd_data_with_transformed_scores():
    """
    Import 2025 transformed scores of deprivation data
    """
    path = f"{settings.IMD_DATA_FILES_FOLDER}/2025/{IMD_2025_TRANSFORMED_SCORES_OF_DEPRIVATION}"
    sys.stdout.write(
        "\n"
        + G
        + "📎 - Adding English 2025 transformed scores of deprivation to LSOAs"
        + W
        + "\n"
    )
    with open(path, "r", encoding="utf-8") as f:
        data = list(csv.reader(f, delimiter=","))
        count = 0
        for row in tqdm(data[1:], desc="Adding 2025 transformed scores"):
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2021)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    "\n" + R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W + "\n"
                )
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2025).update(
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
    final = f" Added {count} English transformed scores of deprivation 2025\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 33755
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 33755 records, but got {count}." + W + "\n"
        )
        pass


"""
Scottish organisational areas and deprivation data
"""


def add_scottish_data_zones_and_local_authorities():
    """
    Add data zones and scottish local authorities
    """
    path = (
        f"{settings.IMD_DATA_FILES_FOLDER}/{SCOTTISH_DATA_ZONES_AND_LOCAL_AUTHORITIES}"
    )
    with open(path, "r", encoding="windows-1252") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding 2011 Scottish Data Zones and Local Authorities"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        lad_count = 0
        dz_count = 0
        for row in tqdm(data[1:], desc="Adding Scottish Data Zones & LADs"):
            local_authority, created = LocalAuthority.objects.update_or_create(
                local_authority_district_code=row[6],
                year=2011,
                defaults={"local_authority_district_name": row[7]},
            )

            if created:
                lad_count += 1

            _, created = DataZone.objects.update_or_create(
                data_zone_code=row[0],
                year=2011,
                defaults={
                    "data_zone_name": row[1],
                    "local_authority": local_authority,
                },
            )

            if created:
                dz_count += 1
    final = (
        f"  Added {lad_count} Scottish Local Authorities and {dz_count} data zones...\n"
    )
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert dz_count == 6976
    except AssertionError:
        sys.stdout.write(
            "\n"
            + R
            + f"😬 Expected 6976 data zone records, but got {dz_count}."
            + W
            + "\n"
        )
    try:
        assert lad_count == 32
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32 lad records, but got {lad_count}." + W + "\n"
        )
        pass


def add_scottish_deprivation_ranks_and_domains_to_2011_datazones():
    # import domains of deprivation data

    if (
        ScottishIndexMultipleDeprivation.objects.exists()
        and ScottishIndexMultipleDeprivation.objects.count() == 6976
    ):
        sys.stdout.write(
            R + "\n⏭️ Scottish indices already exist! Skipping..." + W + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_SCOTLAND_RANKS}"
    with open(path, "r") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding Scottish domains of deprivation to data zones with ranks"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in tqdm(
            data[1:], desc="Adding Scottish IMD ranks"
        ):  # skip the first row
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

    final = f" {count} Scottish IMD records with domains added (ranks).\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final + W + "\n")
    try:
        assert count == 6976
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 6976 records, but got {count}." + W + "\n"
        )
        pass


"""
Welsh deprivation data
"""


def add_welsh_2019_domains_and_ranks_to_existing_2011_lsoas():
    """
    import Welsh domains and ranks 2019 data
    """
    if (
        WelshIndexMultipleDeprivation.objects.exists()
        and WelshIndexMultipleDeprivation.objects.count() >= 1909
    ):
        sys.stdout.write(R + "⏭️ Welsh indices already present. Skipping..." + W)
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_WALES_DEPRIVATION_DOMAINS_RANKS}"
    with open(path, "r") as f:
        sys.stdout.write("\n" + G + "📎 - Adding Welsh IMD ranks/quantiles" + W + "\n")
        data = list(csv.reader(f, delimiter=","))
        count = 0
        for record in tqdm(
            data[1:], desc="Adding Welsh IMD ranks"
        ):  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=record[0], year=2011)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    "\n" + R + f"⏭️ LSOA {record[0]} not found. Skipping..." + W + "\n"
                )
                continue
            WelshIndexMultipleDeprivation.objects.create(
                imd_rank=int(record[3]),
                imd_quartile=quantile_for_rank(
                    rank=int(record[3]), quantile=QuantileType.QUARTILE
                ),
                imd_quintile=quantile_for_rank(
                    rank=int(record[3]), quantile=QuantileType.QUINTILE
                ),
                imd_decile=quantile_for_rank(
                    rank=int(record[3]), quantile=QuantileType.DECILE
                ),
                imd_score=None,
                income_rank=int(record[4]),
                income_quartile=quantile_for_rank(
                    rank=int(record[4]), quantile=QuantileType.QUARTILE
                ),
                income_quintile=quantile_for_rank(
                    rank=int(record[4]), quantile=QuantileType.QUINTILE
                ),
                income_decile=quantile_for_rank(
                    rank=int(record[4]), quantile=QuantileType.DECILE
                ),
                income_score=None,
                employment_rank=int(record[5]),
                employment_quartile=quantile_for_rank(
                    rank=int(record[5]), quantile=QuantileType.QUARTILE
                ),
                employment_quintile=quantile_for_rank(
                    rank=int(record[5]), quantile=QuantileType.QUINTILE
                ),
                employment_decile=quantile_for_rank(
                    rank=int(record[5]), quantile=QuantileType.DECILE
                ),
                employment_score=None,
                health_rank=int(record[6]),
                health_quartile=quantile_for_rank(
                    rank=int(record[6]), quantile=QuantileType.QUARTILE
                ),
                health_quintile=quantile_for_rank(
                    rank=int(record[6]), quantile=QuantileType.QUINTILE
                ),
                health_decile=quantile_for_rank(
                    rank=int(record[6]), quantile=QuantileType.DECILE
                ),
                health_score=None,
                education_rank=int(record[7]),
                education_quartile=quantile_for_rank(
                    rank=int(record[7]), quantile=QuantileType.QUARTILE
                ),
                education_quintile=quantile_for_rank(
                    rank=int(record[7]), quantile=QuantileType.QUINTILE
                ),
                education_decile=quantile_for_rank(
                    rank=int(record[7]), quantile=QuantileType.DECILE
                ),
                education_score=None,
                access_to_services_rank=int(record[8]),
                access_to_services_quartile=quantile_for_rank(
                    rank=int(record[8]), quantile=QuantileType.QUARTILE
                ),
                access_to_services_quintile=quantile_for_rank(
                    rank=int(record[8]), quantile=QuantileType.QUINTILE
                ),
                access_to_services_decile=quantile_for_rank(
                    rank=int(record[8]), quantile=QuantileType.DECILE
                ),
                access_to_services_score=None,
                housing_rank=int(record[9]),
                housing_quartile=quantile_for_rank(
                    rank=int(record[9]), quantile=QuantileType.QUARTILE
                ),
                housing_quintile=quantile_for_rank(
                    rank=int(record[9]), quantile=QuantileType.QUINTILE
                ),
                housing_decile=quantile_for_rank(
                    rank=int(record[9]), quantile=QuantileType.DECILE
                ),
                housing_score=None,
                community_safety_rank=int(record[10]),
                community_safety_quartile=quantile_for_rank(
                    rank=int(record[10]), quantile=QuantileType.QUARTILE
                ),
                community_safety_quintile=quantile_for_rank(
                    rank=int(record[10]), quantile=QuantileType.QUINTILE
                ),
                community_safety_decile=quantile_for_rank(
                    rank=int(record[10]), quantile=QuantileType.DECILE
                ),
                community_safety_score=None,
                physical_environment_rank=int(record[11]),
                physical_environment_quartile=quantile_for_rank(
                    rank=int(record[11]), quantile=QuantileType.QUARTILE
                ),
                physical_environment_quintile=quantile_for_rank(
                    rank=int(record[11]), quantile=QuantileType.QUINTILE
                ),
                physical_environment_decile=quantile_for_rank(
                    rank=int(record[11]), quantile=QuantileType.DECILE
                ),
                physical_environment_score=None,
                lsoa=lsoa,
                year=2019,
            )
            count += 1
    final = f" Added {count} Welsh IMD ranks/quantiles.\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)  # should be 1909
    try:
        assert count == 1909
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 1909 records, but got {count}." + W + "\n"
        )
        pass


def add_welsh_2019_scores_to_existing_2011_lsoas():
    """
    import Welsh IMD scores 2019 and add to existing ranks/imds
    """
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_WALES_DEPRIVATION_SCORES}"
    with open(path, "r") as f:
        sys.stdout.write(G + "\n📎 - Adding Welsh IMD scores" + W + "\n")
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for record in tqdm(
            data[1:], desc="Adding Welsh IMD scores"
        ):  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=record[0], year=2011)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    R + f"\n⏭️ LSOA {record[0]} not found. Skipping..." + W + "\n"
                )
                continue
            WelshIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2011).update(
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
            count += 1
    final = f" Added {count} Welsh IMD scores.\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)  # should be 1909
    try:
        assert count == 1909
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 1909 records, but got {count}." + W + "\n"
        )
        pass


"""
Northern Ireland SOAs and deprivation data
"""


def add_northern_ireland_soas_and_deprivation_domains_with_ranks():
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{NORTHERN_IRELAND_SOAS_AND_IMD_RANKS}"

    if (
        NorthernIrelandIndexMultipleDeprivation.objects.exists()
        and NorthernIrelandIndexMultipleDeprivation.objects.all().count()
        >= SOA.objects.all().count()
    ):  # 891
        sys.stdout.write(
            "\n" + R + "⏭️ Northern Ireland SOAs already added. Skipping..." + W + "\n"
        )
        return
    else:
        imd_counter = 0

        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding Northern Ireland 2001 SOAs and 2017 deprivation domains and ranks..."
            + W
            + "\n"
        )
        with open(path, "r") as f:
            data = list(csv.reader(f, delimiter=","))
            for row in tqdm(
                data[1:891], desc="Adding NI SOAs & IMDs"
            ):  # skip the first row: run up to to 890
                soa, created = SOA.objects.update_or_create(
                    soa_code=row[2], soa_name=row[3], year=2001
                )

                NorthernIrelandIndexMultipleDeprivation.objects.update_or_create(
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

                imd_counter += 1
    final = f" {imd_counter} Northern Ireland SOAs and IMD domains and ranks added.\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final + W + "\n")
    try:
        assert imd_counter == 890
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 890 records, but got {imd_counter}." + W + "\n"
        )
        pass


"""
Green space and population density data
"""


def add_2015_population_denominators():
    # import domains of deprivation data
    # note this includes scotland so must load data zones first
    path = (
        f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_LSOA_2015_POPULATION_DENOMINATORS}"
    )
    with open(path, "r") as f:
        sys.stdout.write(
            G + "\n📎 - Adding 2015 population denominators to LSOAs" + W + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in tqdm(
            data[1:], desc="Adding 2015 population denominators"
        ):  # skip the first row
            LSOA.objects.filter(lsoa_code=row[0], year=2011).update(
                total_population_mid_2015=int(float(row[4])),
                dependent_children_mid_2015=int(float(row[5])),
                population_16_59_mid_2015=int(float(row[6])),
                older_population_over_16_mid_2015=int(float(row[7])),
                working_age_population_over_18_mid_2015=int(float(row[8])),
            )

            count += 1
    final = f" Added {count} 2015 population denominators to LSOAs\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )


def add_lad_access_to_outdoor_space():
    # import domains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{ACCESS_TO_GREEN_SPACE}"
    sys.stdout.write(
        "\n"
        + G
        + "📎 - Adding 2020 green space records to Local Authorities."
        + W
        + "\n"
    )
    with open(path, "r") as f:
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in tqdm(
            data[2:], desc="Adding 2020 green space records"
        ):  # header is on row 3
            la_code = row[4]
            # Scottish LAs were created with year=2011, English & Welsh with year=2019
            la_year = 2011 if la_code.startswith("S") else 2019
            try:
                local_authority = LocalAuthority.objects.get(
                    local_authority_district_code=la_code,
                    year=la_year,
                )
            except LocalAuthority.DoesNotExist:
                sys.stderr.write(
                    "\n"
                    + R
                    + f"⏭️ Local Authority {row[4]} not found. Skipping..."
                    + W
                    + "\n"
                )
                continue
            if GreenSpace.objects.filter(
                local_authority=local_authority, year=2011
            ).exists():
                final = f"⏭️ Green space data already available for {local_authority.local_authority_district_name}.\n"
                sys.stdout.write(final)
                pass
            else:
                GreenSpace.objects.create(
                    local_authority=local_authority,
                    houses_address_count=int(float(row[6])),
                    houses_addresses_with_private_outdoor_space_count=int(
                        float(row[7])
                    ),
                    houses_outdoor_space_total_area=int(float(row[8])),
                    houses_percentage_of_addresses_with_private_outdoor_space=int(
                        float(row[9])
                    ),
                    houses_average_size_private_outdoor_space=int(float(row[10])),
                    houses_median_size_private_outdoor_space=int(float(row[11])),
                    flats_address_count=int(float(row[12])),
                    flats_addresses_with_private_outdoor_space_count=int(
                        float(row[13])
                    ),
                    flats_outdoor_space_total_area=int(float(row[14])),
                    flats_outdoor_space_count=int(float(row[15])),
                    flats_percentage_of_addresses_with_private_outdoor_space=int(
                        float(row[16])
                    ),
                    flats_average_size_private_outdoor_space=int(float(row[17])),
                    flats_average_number_of_flats_sharing_a_garden=int(float(row[18])),
                    total_addresses_count=int(float(row[19])),
                    total_addresses_with_private_outdoor_space_count=int(
                        float(row[20])
                    ),
                    total_percentage_addresses_with_private_outdoor_space=int(
                        float(row[21])
                    ),
                    total_average_size_private_outdoor_space=int(float(row[22])),
                    year=2020,
                )

                count += 1
    final = f" Added {count} Local Authority green space records.\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 371
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 371 records, but got {count}." + W + "\n"
        )
        pass


def update_population_densities():
    """
    Processes population density data from a list of dictionaries, creating PopulationDensity objects.

    Args:
        data: A list of dictionaries, where each dictionary represents a row of data.
                The first row is assumed to be a header and is skipped.  The order of
                data in subsequent rows is assumed to match the order of fields
                used to create the PopulationDensity object.

    Returns:
        None.  The function creates PopulationDensity objects in the database.

    Thanks to the remarkable alex.gilroy@theriverstrust for this resource
    """
    if (
        PopulationDensity.objects.exists()
        and PopulationDensity.objects.all().count() >= 32058
    ):
        sys.stdout.write(
            "\n" + R + "⏭️ Population density data already added. Skipping..." + W + "\n"
        )  # should be 32058
        return

    count = 0

    path = f"{settings.POPULATION_DENSITIES_FOLDER}/{POPULATION_DENSITIES}"
    with open(path, "r") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding population densities for England by LSOA and ethnicities\n"
            + W
        )
        data = list(csv.reader(f, delimiter=","))

        for row in tqdm(
            data[1:], desc="Adding population densities"
        ):  # Iterate starting from the second row (index 1)
            lsoa11cd = row[1]  # Access the first element (index 1) which is 'lsoa11cd'
            lsoa = None
            if LSOA.objects.filter(lsoa_code=lsoa11cd, year=2011).exists():
                lsoa = LSOA.objects.filter(lsoa_code=lsoa11cd, year=2011).get()
            if lsoa is None:
                error = (
                    "\n"
                    + R
                    + f"⏭️ LSOA with code {lsoa11cd} not found. Skipping row...."
                    + W
                    + "\n"
                )
                sys.stderr.write(error)
                continue

            PopulationDensity.objects.update_or_create(
                lsoa=lsoa,
                year=2024,
                defaults={
                    "perc_buff200": row[8] if row[8] else None,
                    "perc_buff300": row[9] if row[9] else None,
                    "perc_buff1k": row[10] if row[10] else None,
                    "perc_buff2k": row[11] if row[11] else None,
                    "perc_buff5k": row[12] if row[12] else None,
                    "perc_buff10k": row[13] if row[13] else None,
                    "imd_decile": row[14] if row[14] else None,
                    "population_density_2011": row[15] if row[15] else None,
                    "population_2011": row[16] if row[16] else None,
                    "buff200_popdens_deficit": row[17] if row[17] else None,
                    "buff300_popdens_deficit": row[18] if row[18] else None,
                    "buff1k_popdens_deficit": row[19] if row[19] else None,
                    "buff2k_popdens_deficit": row[20] if row[20] else None,
                    "buff5k_popdens_deficit": row[21] if row[21] else None,
                    "buff10k_popdens_deficit": row[22] if row[22] else None,
                    "buff200_imd_deficit": row[23] if row[23] else None,
                    "buff300_imd_deficit": row[24] if row[24] else None,
                    "buff1k_imd_deficit": row[25] if row[25] else None,
                    "buff2k_imd_deficit": row[26] if row[26] else None,
                    "buff5k_imd_deficit": row[27] if row[27] else None,
                    "buff10k_imd_deficit": row[28] if row[28] else None,
                    "ag_area_ha": row[29] if row[29] else None,
                    "index_multiple_deprivation_2019": row[30] if row[30] else None,
                    "population_estimate2018": row[31] if row[31] else None,
                    "population_growth_2011_2018": row[32] if row[32] else None,
                    "ethnic_white_2011": row[33] if row[33] else None,
                    "ethnic_mixed_2011": row[34] if row[34] else None,
                    "ethnic_asian_2011": row[35] if row[35] else None,
                    "ethnic_black_african_caribbean": row[36] if row[36] else None,
                    "ethnic_other_2011": row[37] if row[37] else None,
                    "population_2011_1000s": row[38] if row[38] else None,
                    "nr_area_ha": row[39] if row[39] else None,
                    "nr_percentage": row[40] if row[40] else None,
                    "ruc_category": row[41] if row[41] else None,
                    "ruc11": row[42] if row[42] else None,
                    "lnr_area_ha": row[43] if row[43] else None,
                    "residentialaddress_count": row[44] if row[44] else None,
                    "pg_area": row[45] if row[45] else None,
                    "pg_area_per1kpeople": row[46] if row[46] else None,
                    "perc_osmmgs": row[47] if row[47] else None,
                    "pgarea_resaddress_ratio": row[48] if row[48] else None,
                    "accessiblewoodland_ha": row[49] if row[49] else None,
                    "mean_manmade_percentage": row[50] if row[50] else None,
                    "cohort_age_0_to_4": row[51] if row[51] else None,
                    "cohort_age_5_to_7": row[52] if row[52] else None,
                    "cohort_age_8_to_9": row[53] if row[53] else None,
                    "cohort_age_10_to_14": row[54] if row[54] else None,
                    "cohort_age_15": row[55] if row[55] else None,
                    "cohort_age_16_to_17": row[56] if row[56] else None,
                    "cohort_age_18_to_19": row[57] if row[57] else None,
                    "cohort_age_20_to_24": row[58] if row[58] else None,
                    "cohort_age_25_to_29": row[59] if row[59] else None,
                    "cohort_age_30_to_44": row[60] if row[60] else None,
                    "cohort_age_45_to_59": row[61] if row[61] else None,
                    "cohort_age_60_to_64": row[62] if row[62] else None,
                    "cohort_age_65_to_74": row[63] if row[63] else None,
                    "cohort_age_75_to_84": row[64] if row[64] else None,
                    "cohort_age_85_to_89": row[65] if row[65] else None,
                    "cohort_age_90_and_over": row[66] if row[66] else None,
                    "perc_close2home": row[67] if row[67] else None,
                    "popn_close2home": row[68] if row[68] else None,
                    "cohort_children": row[69] if row[69] else None,
                    "cohort_olderpeople": row[70] if row[70] else None,
                    "perc_pop_close2home": row[71] if row[71] else None,
                    "popn_children_close2home": row[72] if row[72] else None,
                    "popn_olderpeople_close2home": row[73] if row[73] else None,
                    "imd_reversed": row[74] if row[74] else None,
                    "ag_area_ha_per_person": row[75] if row[75] else None,
                },
            )

            count += 1

        final = f" {count} Population Density records by LSOA stored.\n"
        sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
        try:
            # Check if the count matches the expected number of records
            assert count == 32844
        except AssertionError:
            sys.stdout.write(
                "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
            )
            pass


"""
Quantile calculations
"""


def calculated_quantile_for_rank(rank, total_records, quantile_type):
    """
    Return a quantile against a rank and a total
    Params:
    rank: integer - represents rank in a list of records
    total_records: integer - represents the total number of records
    quantile_type: integer - the number of equally sized groups the records are divided into
    """
    _ = [
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


def quantile_for_rank(rank: int, quantile: QuantileType) -> int:
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
        (quantile == QuantileType.QUARTILE and rank <= 478)
        or (rank <= 191 and quantile == QuantileType.DECILE)
        or (rank <= 382 and quantile == QuantileType.QUINTILE)
    ):
        return 1
    elif (
        (quantile == QuantileType.QUARTILE and rank <= 955)
        or (rank <= 382 and quantile == QuantileType.DECILE)
        or (rank <= 764 and quantile == QuantileType.QUINTILE)
    ):
        return 2
    elif (
        (quantile == QuantileType.QUARTILE and rank <= 1432)
        or (rank <= 573 and quantile == QuantileType.DECILE)
        or (rank <= 1146 and quantile == QuantileType.QUINTILE)
    ):
        return 3
    elif (
        (quantile == QuantileType.QUARTILE and rank <= 1909)
        or (rank <= 764 and quantile == QuantileType.DECILE)
        or (rank <= 1528 and quantile == QuantileType.QUINTILE)
    ):
        return 4
    elif (rank <= 955 and quantile == QuantileType.DECILE) or (
        rank <= 1909 and quantile == QuantileType.QUINTILE
    ):
        return 5
    elif rank <= 1146 and quantile == QuantileType.DECILE:
        return 6
    elif rank <= 1337 and quantile == QuantileType.DECILE:
        return 7
    elif rank <= 1528 and quantile == QuantileType.DECILE:
        return 8
    elif rank <= 1719 and quantile == QuantileType.DECILE:
        return 9
    elif rank <= 1909 and quantile == QuantileType.DECILE:
        return 10
    else:
        raise ValueError(f"Incorrect rank {rank} passed for {quantile.value}")


def test_table_totals():
    """
    Test the total number of records in each table
    """
    sys.stdout.write("\n" + G + "📎 - Testing table totals..." + W + "\n")
    # Check if the count matches the expected number of records
    normal_vals = [
        {
            "model": LSOA,
            "count": LSOA.objects.filter(year=2011).count(),
            "expected": 34753,
            "message": "2011 LSOA should have 34753 (32844 in England, 1909 in wales) rows.",
        },
        {
            "model": LSOA,
            "count": LSOA.objects.filter(year=2021).count(),
            "expected": 35672,
            "message": "2021 LSOA should have 35672 rows.",
        },
        {
            "model": DataZone,
            "count": DataZone.objects.count(),
            "expected": 6976,
            "message": "DataZone should have 6976 rows.",
        },
        {
            "model": LocalAuthority,
            "count": LocalAuthority.objects.filter(year=2011).count(),
            "expected": 32,
            "message": "2011 LocalAuthority for Scotland should have 32 .",
        },
        {
            "model": LocalAuthority,
            "count": LocalAuthority.objects.filter(year=2019).count(),
            "expected": 339,
            "message": "2019 LocalAuthority for England and Wales should have 339 (317 in England, 22 in Wales) rows (the 11 Northern Irish Local Authorities are not included here). ",
        },
        {
            "model": LocalAuthority,
            "count": LocalAuthority.objects.filter(year=2024).count(),
            "expected": 318,
            "message": "2024 LocalAuthority should have 318 rows. ",
        },
        {
            "model": PopulationDensity,
            "count": PopulationDensity.objects.count(),
            "expected": 32844,
            "message": "PopulationDensity should have 32844 rows.",
        },
        {
            "model": GreenSpace,
            "count": GreenSpace.objects.count(),
            "expected": 371,
            "message": "GreenSpace should have 371 rows.",
        },
        {
            "model": SOA,
            "count": SOA.objects.count(),
            "expected": 890,
            "message": "SOA should have 890 rows.",
        },
        {
            "model": WelshIndexMultipleDeprivation,
            "count": WelshIndexMultipleDeprivation.objects.count(),
            "expected": 1909,
            "message": "WelshIndexMultipleDeprivation should have 1909 rows.",
        },
        {
            "model": NorthernIrelandIndexMultipleDeprivation,
            "count": NorthernIrelandIndexMultipleDeprivation.objects.count(),
            "expected": 890,
            "message": "NorthernIrelandIndexMultipleDeprivation should have 890 rows.",
        },
        {
            "model": ScottishIndexMultipleDeprivation,
            "count": ScottishIndexMultipleDeprivation.objects.count(),
            "expected": 6976,
            "message": "ScottishIndexMultipleDeprivation should have 6976 rows.",
        },
    ]
    for val in normal_vals:
        try:
            assert val["count"] == val["expected"]
        except AssertionError:
            sys.stdout.write(
                "\n" + R + f"😬 {val['message']} But got {val['count']}." + W + "\n"
            )
            continue
        sys.stdout.write(
            W + f"✅ {val['model'].__name__} has {val['count']} records." + W + "\n"
        )


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
