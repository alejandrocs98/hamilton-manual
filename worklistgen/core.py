# core.py

import pandas as pd
from typing import List, Dict
from .labware_config import LABWARE_TYPES

class Source:
    def __init__(self, name: str, source_type: str, labware_type: str, input: List, well_map: pd.DataFrame = None):
        """
        Initialize a source labware object with a well map.
        :param name: Name of the source labware
        :param source_type: Type of the source (e.g., 'species', 'media')
        :param labware_type: Type of the labware (e.g., '96wellplate', 'tuberack')
        :param input: List of species to be transferred
        :param well_map: Optional custom well map as a pandas DataFrame
        """
        if source_type not in ['species', 'media']:
            raise ValueError("Type must be either 'species' or 'media'.")
        if labware_type not in LABWARE_TYPES:
            raise ValueError(f"Labware type '{labware_type}' is not recognized.")
        if len(input) != len(set(input)):
            raise ValueError("Input species list contains duplicates.")
        
        self.input = input
        self.labware_needed = len(input) // len(LABWARE_TYPES[labware_type]['layout']) + 1
        self.name = name
        self.source_type = source_type
        self.labware_type = labware_type
        self.layout = LABWARE_TYPES[labware_type]['layout']
        
        if well_map is not None:
            self.update_well_map(well_map)
        else:
            self.well_map = self._build_well_map()

    def _build_well_map(self) -> pd.DataFrame:
        """
        Build the well map for the source labware.
        :return: pandas DataFrame with the columns: input, well, plate number, and labware type
        """
        well_map = []
        input_chunks = [self.input[i:i + len(self.layout)] for i in range(0, len(self.input), len(self.layout))]
        for plate_num, chunk in enumerate(input_chunks, start=1):
            for input, well in zip(chunk, self.layout[:len(chunk)]):
                well_map.append({
                    'Source_type': self.source_type,
                    'Input': input,
                    'Well': well,
                    'Name': f'{self.name}-{plate_num}',
                    'Labware_type': self.labware_type
                })
        return pd.DataFrame(well_map)
    
    def update_well_map(self, new_well_map: pd.DataFrame):
        """
        Update the well map with a custom DataFrame.
        :param new_well_map: pandas DataFrame with columns: Input and Well
        """
        if not {'Input', 'Well'}.issubset(new_well_map.columns):
            raise ValueError("The new well map must contain 'Input' and 'Well' columns.")
        if not all(item in self.input for item in new_well_map['Input']):
            raise ValueError("Some inputs in the new well map are not in the original input list.")
        if not all(item in self.layout for item in new_well_map['Well']):
            raise ValueError("Some wells in the new well map are not in the original layout.")
        
        self.well_map = new_well_map

class Destination:
    def __init__(self, name: str, labware_type: str, experiments: pd.DataFrame, blanks: List[str], replicates: int = 3, blanks_replicates: int = 1):
        """
        Initialize a destination labware object with a well map.
        :param name: Name of the destination labware
        :param labware_type: Type of the labware (e.g., '96wellplate', 'tuberack')
        :param experiments: DataFrame containing: communities and conditions to be transferred
        :param blanks: List of conditions to make blanks of
        :param replicates: Number of replicates for each community
        :param blanks_replicates: Number of replicates for each blank condition in each labware unit
        """
        if replicates < 1:
            raise ValueError("Replicates must be at least 1.")
        if blanks_replicates < 1:
            raise ValueError("Blanks replicates must be at least 1.")
        if labware_type not in LABWARE_TYPES:
            raise ValueError(f"Labware type '{labware_type}' is not recognized.")
        if not {'community', 'condition'}.issubset(experiments.columns):
            raise ValueError("The experiments DataFrame must contain 'community' and 'condition' columns.")
        
        self.communities = list(experiments['community'])
        self.conditions = list(experiments['condition'])
        self.experiments = experiments
        self.replicates = replicates
        self.blanks_replicates = blanks_replicates
        self.blanks = blanks
        self.labware_type = labware_type
        self.layout = LABWARE_TYPES[labware_type]['layout']
        self.labware_needed = (len(self.communities) * replicates + len(self.blanks) * blanks_replicates) // len(self.layout) + 1
        self.name = name
        self.well_map = self._build_well_map()

    def _build_well_map(self) -> pd.DataFrame:
        """
        Build the well map for the destination labware.
        :return: pandas DataFrame with columns: community, condition, replicate, well, plate number, and labware type
        """
        well_map = []
        well = 0
        for blank_condition in self.blanks:
            for blank_rep in range(1, self.blanks_replicates + 1):
                well_map.append({
                    'Community': 'blank',
                    'Condition': blank_condition,
                    'Replicate': blank_rep,
                    'Well': self.layout[well % len(self.layout)],
                    'Name': f'{self.name}-{(well // len(self.layout)) + 1}',
                    'Labware_type': self.labware_type
                })
                well += 1

        for community, condition in zip(self.communities, self.conditions):
            for rep in range(1, self.replicates + 1):
                well_map.append({
                    'Community': community,
                    'Condition': condition,
                    'Replicate': rep,
                    'Well': self.layout[well % len(self.layout)],
                    'Name': f'{self.name}-{(well // len(self.layout)) + 1}',
                    'Labware_type': self.labware_type
                })
                well += 1

        return pd.DataFrame(well_map)

class Worklist:
    def __init__(self, name: str, total_volume: float):
        """
        Initialize an Worklist object.
        :param name: Name of the worklist
        :param total_volume: Total volume to transfer to each well in microliters
        """
        self.name = name
        self.total_volume = total_volume
        self.sources: List[Source] = []
        self.destinations: List[Destination] = []
        self.worklist: Dict[str, List] = {
            'Source_plate_Name': [],
            'Source_Plate_Type': [],
            'Source_Plate_Well': [],
            'Destination_plate_Name': [],
            'Destination_Plate_Type': [],
            'Destination_Plate_Well': [],
            'Transfer_Volume': []
        }
        self.worklist_df = pd.DataFrame(self.worklist)

    def add_source(self, source: Source):
        """
        Add a source to the worklist.
        :param source: Source object
        """
        self.sources.append(source)

    def add_destination(self, destination: Destination):
        """
        Add a destination to the worklist.
        :param destination: Destination object
        """
        self.destinations.append(destination)

    def generate_worklist(self):
        """
        Generate the worklist mapping all transfer actions from sources to destinations.
        Sources of type 'species' map to the 'community' column.
        Sources of type 'media' map to the 'condition' column.
        If community == 'blank', no species transfers are done.
        """
        # for quick lookup: for each source object, build a dict by input->(name, type, well)
        source_lookup = {}
        for src in self.sources:
            df = src.well_map
            for _, row in df.iterrows():
                key = (src.source_type, row['Input'])
                source_lookup[key] = {
                    'plate_name': row['Name'],
                    'plate_type': row['Labware_type'],
                    'well': row['Well']
                }

        # now iterate every destination well
        for dest in self.destinations:
            dest_df = dest.well_map
            for _, drow in dest_df.iterrows():
                community = drow['Community']
                condition = drow['Condition']
                dest_name = drow['Name']
                dest_type = drow['Labware_type']
                dest_well = drow['Well']

                # 1) species transfers, unless blank
                if community != 'blank':
                    species_list = community.split('-')
                    vol_each = self.total_volume / len(species_list)
                    for sp in species_list:
                        key = ('species', sp)
                        if key not in source_lookup:
                            raise ValueError(f"No species source for '{sp}'")
                        src = source_lookup[key]
                        self.worklist['Source_plate_Name'].append(src['plate_name'])
                        self.worklist['Source_Plate_Type'].append(src['plate_type'])
                        self.worklist['Source_Plate_Well'].append(src['well'])
                        self.worklist['Destination_plate_Name'].append(dest_name)
                        self.worklist['Destination_Plate_Type'].append(dest_type)
                        self.worklist['Destination_Plate_Well'].append(dest_well)
                        self.worklist['Transfer_Volume'].append(vol_each)

                # 2) media transfers (conditions)
                media_list = condition.split('-')
                vol_each = self.total_volume / len(media_list)
                for cond in media_list:
                    key = ('media', cond)
                    if key not in source_lookup:
                        raise ValueError(f"No media source for '{cond}'")
                    src = source_lookup[key]
                    self.worklist['Source_plate_Name'].append(src['plate_name'])
                    self.worklist['Source_Plate_Type'].append(src['plate_type'])
                    self.worklist['Source_Plate_Well'].append(src['well'])
                    self.worklist['Destination_plate_Name'].append(dest_name)
                    self.worklist['Destination_Plate_Type'].append(dest_type)
                    self.worklist['Destination_Plate_Well'].append(dest_well)
                    self.worklist['Transfer_Volume'].append(vol_each)
        # convert to DataFrame
        self.worklist_df = pd.DataFrame(self.worklist)

    def get_worklist_df(self) -> pd.DataFrame:
        """
        Get the worklist DataFrame.
        :return: pandas DataFrame with the worklist
        """
        if self.worklist_df.empty:
            raise ValueError("Worklist is empty. Please generate the worklist first.")
        return self.worklist_df
