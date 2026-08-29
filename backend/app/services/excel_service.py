import pandas as pd


def read_excel(file_path):

    dataframe = pd.read_excel(
        file_path,
        engine="openpyxl"
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