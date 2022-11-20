import csv
from django.core.management.base import BaseCommand

from django.conf import settings
from ...models import LSOA, MSOA, LocalAuthority, Ward, IndexMultipleDeprivation


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
        if options["mode"] == "add_census_areas":
            self.stdout.write(B + "Adding census areas..." + W)
            add_census_areas()

        else:
            self.stdout.write("No options supplied...")
        self.stdout.write(image())
        self.stdout.write("done.")


def add_census_areas():

    if LocalAuthority.objects.count() == 339:
        print("Local Authority Districts already loaded. Passing...")
    else:
        add_lsoas_2011_wards_2019_to_LADS_2019()
        add_2015_population_denominators()

    if IndexMultipleDeprivation.objects.count() == 32844:
        print("IMD Domains already added. Passing....")
    else:
        add_deprivation_scores_and_domains_to_2011_lsoas()
        update_imd_data_with_subdomains()
        update_imd_data_with_supplementary_indices()
        update_imd_data_with_scores()
        update_imd_data_with_transformed_scores()


def add_lsoas_2011_wards_2019_to_LADS_2019():
    # import LSOA 2011/Ward & LAD 2019 boundaries
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{LSOA_2011_WARD_LAD_2019}"
    with open(path, "r") as f:
        print(G + "Adding 2019 LADs and 2011 LSOAs..." + W)
        lad_counter = 0
        lsoa_counter = 0
        data = list(csv.reader(f, delimiter=","))

        for row in data[1:]:  # skip the first row

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

            lsoa_2011, created = LSOA.objects.get_or_create(
                lsoa_code=row[1],
                lsoa_name=row[2],
                year=2011,
                local_authority_district=local_authority_district_2019,
            )
            if created:
                lsoa_counter += 1

            print(
                f"{lad_counter} local authority districts and {lsoa_counter} lsoas added.",
                end="\r",
            )
    print(
        f"Complete. Added total {lad_counter} local authority districts and {lsoa_counter} lsoas."
    )


def add_deprivation_scores_and_domains_to_2011_lsoas():
    # import domains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SUBDOMAINS_OF_DEPRIVATION}"
    with open(path, "r") as f:
        print(G + "Adding domains of deprivation to LSOAs" + W)
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:  # skip the first row
            if LSOA.objects.filter(lsoa_code=row[0], year=2011).exists():
                lsoa = LSOA.objects.filter(lsoa_code=row[0], year=2011).get()

                IndexMultipleDeprivation.objects.create(
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

                print(f"Added {count} records of deprivation domains", end="\r")

        print(f"{BOLD}Complete.{END} {count} IMD records with domains added")


def update_imd_data_with_subdomains():
    # import domains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SUBDOMAINS_OF_DEPRIVATION}"
    with open(path, "r") as f:
        print(G + "Adding sub-domains of deprivation to LSOAs" + W)
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:
            lsoa = LSOA.objects.get(lsoa_code=row[0])
            IndexMultipleDeprivation.objects.filter(lsoa=lsoa).update(
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
            print(f"Updated {count} LSOAs with subdomains.", end="\r")
    print(f"{BOLD}Complete.{END} Added {count} subdomains of deprivation 2019 to LSOAs")


def update_imd_data_with_supplementary_indices():
    # import domains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SUPPLEMENTARY_INDICES_OF_DEPRIVATION}"
    with open(path, "r") as f:
        print(
            G
            + "Adding supplementary indices (IDACI and IDAOPI) of deprivation to LSOAs"
            + W
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:
            lsoa = LSOA.objects.get(lsoa_code=row[0])
            IndexMultipleDeprivation.objects.filter(lsoa=lsoa).update(
                idaci_rank=int(float(row[6])),
                idaci_decile=int(float(row[7])),
                idaopi_rank=int(float(row[8])),
                idaopi_decile=int(float(row[9])),
            )
            count += 1
            print(f"Updated {count} LSOAs with IDACI and IDAOPI data...", end="\r")
    print(
        f"{BOLD}Complete.{END} Added {count} supplementary indices (IDACI and IDAOPI) of deprivation 2019 to LSOAs"
    )


def update_imd_data_with_scores():
    # import domains of deprivation data
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SCORES_OF_DEPRIVATION}"
    with open(path, "r") as f:
        print(G + "Adding scores of deprivation to LSOAs" + W)
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:
            lsoa = LSOA.objects.get(lsoa_code=row[0])
            IndexMultipleDeprivation.objects.filter(lsoa=lsoa).update(
                imd_score=int(float(row[4])),
                income_score=int(float(row[5])),
                employment_score=int(float(row[6])),
                education_skills_training_score=int(float(row[7])),
                health_deprivation_disability_score=int(float(row[8])),
                crime_score=int(float(row[9])),
                barriers_to_housing_services_score=int(float(row[10])),
                living_environment_score=int(float(row[11])),
                idaci_score=int(float(row[12])),
                idaopi_score=int(float(row[13])),
                children_young_people_sub_domain_score=int(float(row[14])),
                adult_skills_sub_domain_score=int(float(row[15])),
                geographical_barriers_sub_domain_score=int(float(row[16])),
                wider_barriers_sub_domain_score=int(float(row[17])),
                indoors_sub_domain_score=int(float(row[18])),
                outdoors_sub_domain_score=int(float(row[19])),
            )
            count += 1
            print(f"Updated {count} LSOAs with scores of deprivation 2019...", end="\r")
    print(f"{BOLD}Complete.{END} Added {count} scores of deprivation 2019 to LSOAs")


def update_imd_data_with_transformed_scores():
    # import domains of deprivation data
    path = (
        f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_TRANSFORMED_SCORES_OF_DEPRIVATION}"
    )
    with open(path, "r") as f:
        print(G + "Adding transformed_scores of deprivation to LSOAs" + W)
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:
            lsoa = LSOA.objects.get(lsoa_code=row[0])
            IndexMultipleDeprivation.objects.filter(lsoa=lsoa).update(
                income_score_exponentially_transformed=int(float(row[4])),
                employment_score_exponentially_transformed=int(float(row[5])),
                education_skills_training_score_exponentially_transformed=int(
                    float(row[6])
                ),
                health_deprivation_disability_score_exponentially_transformed=int(
                    float(row[7])
                ),
                crime_score_exponentially_transformed=int(float(row[8])),
                barriers_to_housing_services_score_exponentially_transformed=int(
                    float(row[9])
                ),
                living_environment_score_exponentially_transformed=int(float(row[10])),
            )
            count += 1
            print(
                f"Updated {count} LSOAs with transformed scores of deprivation 2019...",
                end="\r",
            )
    print(
        f"{BOLD}Complete.{END} Added {count} transformed scores of deprivation 2019 to LSOAs"
    )


def add_2015_population_denominators():
    # import domains of deprivation data
    path = (
        f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_LSOA_2015_POPULATION_DENOMINATORS}"
    )
    with open(path, "r") as f:
        print(G + "Adding 2019 population denominators to LSOAs" + W)
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
    print(f"{BOLD}Complete.{END} Added {count} 2015 population denominators to LSOAs")


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
