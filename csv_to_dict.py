import csv

def load_commandments(csv_file="commandments.csv"):
    """
    Reads a CSV of commandments and returns a dictionary:
    { reference_id: scripture_english }
    """
    data_dict = {}
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ref = row['reference_id'].strip()
            scripture = row['scripture_english'].strip().replace('"""', '')
            data_dict[ref] = scripture
    return data_dict
