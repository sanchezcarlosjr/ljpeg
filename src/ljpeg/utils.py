# https://github.com/fjeg/ddsm_tools/blob/master/ddsm_tools/ddsm_util.py#L1
import os


####################################################
# Extract value from split list of data
####################################################
def get_value(lst, row_name, idx):
    """
    :param lst: data list, each entry is another list with whitespace separated data
    :param row_name: name of the row to find data
    :param idx: numeric index of desired value
    :return: value
    """
    val = None
    for element in lst:
        if not element:
            continue
        if element[0] == row_name:
            try:
                val = element[idx]
            except Exception:
                val = None
            break
    return val


####################################################
# ICS Information extraction
####################################################
scanner_map = {
    ('A', 'DBA'): 'MGH',
    ('A', 'HOWTEK'): 'MGH',
    ('B', 'LUMISYS'): 'WFU',
    ('C', 'LUMISYS'): 'WFU',
    ('D', 'HOWTEK'): 'ISMD'
}


def get_ics_info_from_text(ics_text, letter):
    lines = list(map(lambda line: line.strip().split(), ics_text))
    # map ics data to values
    ics_dict = {
        'patient_id': get_value(lines, 'filename', 1),
        'age': get_value(lines, 'PATIENT_AGE', 1),
        'scanner_type': get_value(lines, 'DIGITIZER', 1),
        'scan_institution': scanner_map[(letter, get_value(lines, 'DIGITIZER', 1))],
        'density': get_value(lines, 'DENSITY', 1)
    }

    for sequence in ['LEFT_CC', 'RIGHT_CC', 'LEFT_MLO', 'RIGHT_MLO']:
        if get_value(lines, sequence, 0) is None:
            continue

        sequence_dict = {
            'height': int(get_value(lines, sequence, 2)),
            'width': int(get_value(lines, sequence, 4)),
            'bpp': int(get_value(lines, sequence, 6)),
            'resolution': float(get_value(lines, sequence, 8))
        }

        ics_dict[sequence] = sequence_dict

    return ics_dict


def get_ics_info(ics_file_path):
    """
    :param ics_file_path: path to ics file
    :return: dictionary containing all relevant data in ics file
    """
    # get letter for scanner type
    ics_file_name = os.path.basename(ics_file_path)
    letter = ics_file_name[0]
    print(letter)

    # get data from ics file
    with open(ics_file_path, 'r') as f:
        return get_ics_info_from_text(f.readlines(), letter)
    return dict()


####################################################
# Overlay Information extraction
####################################################
def get_abnormality_data(file_name):
    """
    :param file_name: file path of overlay file
    :return: data about abnormality
    """

    # read lines, strip newlines, split them by whitespace, remove empty lines
    with open(file_name, 'r') as file_ptr:
        lines = list(map(lambda s: s.strip().split(), file_ptr.readlines()))
        lines = list(filter(lambda element: element != [], lines))
    try:
        total_abnormalities = int(lines[0][1])
    except ValueError:
        total_abnormalities = 0

    if total_abnormalities == 0:
        return []

    # get index of all lines that start a new abnormality
    try:
        abnormal_idx = [
           idx for idx, l in enumerate(lines) if l[0].find("ABNORMALITY") == 0
        ]
        abnormal_idx.append(len(lines))
    except Exception:
        return []
    abnormality_data = []
    for idx in range(len(abnormal_idx) - 1):
        lesion_data = lines[abnormal_idx[idx]:abnormal_idx[idx + 1]]
        lesion_type = lesion_data[1][1].lower()
        abnormality_data.append((file_name, lesion_type, lesion_data))
    return abnormality_data
