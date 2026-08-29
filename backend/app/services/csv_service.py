import pandas as pd


def read_csv(file_path):

    dataframe = pd.read_csv(
        file_path
    )

    dataframe = dataframe.fillna("")

    dataframe.columns = [
        str(column)
        .strip()
        .lower()
        for column in dataframe.columns
    ]

    return dataframe.to_dict(
        orient="records"
    )