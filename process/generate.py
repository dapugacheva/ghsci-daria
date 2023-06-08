"""Generate resources supporting urban indicator dissemination and usage."""

import shutil
import sys

import yaml
from subprocesses._utils import (
    check_and_update_config_reporting_parameters,
    generate_metadata_xml,
    generate_metadata_yml,
    generate_report_for_language,
    postgis_to_geopackage,
    print_autobreak,
)
from subprocesses.analysis_report import PDF_Analysis_Report

# Load study region configuration
from subprocesses.ghsci import (
    Region,
    __version__,
    datasets,
    date_hhmm,
    folder_path,
    indicators,
    os,
    policies,
    settings,
)


def generate(codename):
    r = Region(codename)
    print(r.header)
    r.config['codename'] = codename
    r.config['__version__'] = __version__
    r.config['templates'] = ['web']
    r.config[
        'report_configuration'
    ] = './configuration/_report_configuration.xlsx'
    r.config['folder_path'] = folder_path
    r.config['date_hhmm'] = date_hhmm
    r.config['authors'] = settings['documentation']['authors']
    with open(f"{r.config['region_dir']}/_parameters.yml") as f:
        r.config['parameters'] = yaml.safe_load(f)
    if not os.path.exists(r.config['region_dir']):
        sys.exit(
            f"\n\nProcessed resource folder for this city couldn't be located:"
            f'\n[{r.config["region_dir"]}]'
            '\nPlease ensure city has been successfully processed before continuing\n',
        )
    # List existing generated resources
    print('Analysis parameter summary text file')
    print('  _parameters.yml')
    print('\nAnalysis log text file')
    print(f"  __{r.config['name']}__{codename}_processing_log.txt")
    print('\nData files')
    print(f"  {os.path.basename(r.config['gpkg'])}")
    custom_aggregations = r.config.pop('custom_aggregations', {})
    tables = [f'indicators_{x}' for x in custom_aggregations] + [
        r.config['city_summary'],
        r.config['grid_summary'],
        r.config['point_summary'],
        'aos_public_osm',
        'dest_type',
        'destinations',
        r.config['intersections_table'],
        'edges',
        'nodes',
    ]
    if r.config['gtfs_feeds'] is not None:
        tables = tables + [datasets['gtfs']['headway']]
    if r.tables == []:
        sys.exit(
            f"\nResults don't appear to have been processed Please ensure that the analysis process has been run for this study region successfully and then try again.  The specific error raised was:\n{e}\n",
        )
    tables_not_in_database = [x for x in tables if x not in r.tables]
    if len(tables_not_in_database) > 0:
        print(
            f"The following tables were not found in the database, and so not exported: {', '.join(tables_not_in_database)} (please ensure processing has been completed to export these)",
        )
    postgis_to_geopackage(
        r.config['gpkg'],
        settings['sql']['db_host'],
        settings['sql']['db_user'],
        r.config['db'],
        settings['sql']['db_pwd'],
        [t for t in tables if t in r.tables],
    )
    for layer in ['city', 'grid']:
        if r.config[f'{layer}_summary'] in r.tables:
            print(
                '  '
                + os.path.basename(
                    r.to_csv(
                        r.config[f'{layer}_summary'],
                        f"{r.config['region_dir']}/{r.codename}_{r.config[f'{layer}_summary']}.csv",
                    ),
                ),
            )
    for layer in custom_aggregations:
        if layer in r.tables:
            print(
                '  '
                + os.path.basename(
                    r.to_csv(
                        f'indicators_{layer}',
                        f"{r.config['region_dir']}/{r.codename}_indicators_{layer}.csv",
                    ),
                ),
            )
    # Generate data dictionary
    print('\nData dictionaries')
    required_assets = [
        'output_data_dictionary.csv',
        'output_data_dictionary.xlsx',
    ]
    for file in required_assets:
        shutil.copyfile(
            f'./configuration/assets/{file}',
            f"{r.config['region_dir']}/{file}",
        )
        print(f'  {file}')

    # Generate metadata
    print('\nMetadata')
    metadata_yml = generate_metadata_yml(
        r.engine, folder_path, r.config, settings,
    )
    print(f'  {metadata_yml}')
    metadata_xml = generate_metadata_xml(r.config['region_dir'], codename)
    print(f'  {metadata_xml}')
    # Generate web reports by language
    r.config['reporting'] = check_and_update_config_reporting_parameters(
        r.config,
    )
    for language in r.config['reporting']['languages']:
        generate_report_for_language(
            r, language, indicators, policies,
        )
    # Generate analysis report
    print('\nAnalysis report (work in progress...)')
    analysis_report = PDF_Analysis_Report(r.config, settings)
    analysis_report.generate_analysis_report()

    # Advise user to check outputs
    print_autobreak(
        '\n\nIt is important to take the time to familiarise yourself with the various outputs generated from the configuration and analysis of your region of interest to ensure they provide a fair and accurate representation given local knowledge.  Any issues or limitations identified should be understood and can be iteratively addressed and/or acknowledged in documentation prior to dissemination.\n\n',
    )


def main():
    try:
        codename = sys.argv[1]
    except IndexError:
        codename = None
    generate(codename)


if __name__ == '__main__':
    main()
