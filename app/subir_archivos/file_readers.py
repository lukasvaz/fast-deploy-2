import csv
import re

import openpyxl


def process_headers(header):
    # Remove text in parentheses, replace _ and / with space, and strip
    return [
        field.strip().replace("_", " ").replace("/", " ") if field else ""
        for field in [re.sub(r"\s*\([^)]*\)", "", h) if h else "" for h in header]
    ]


class CSVStrategy:
    @staticmethod
    def get_reader(file):
        file.seek(0)
        decoded = file.read().decode("utf-8").splitlines()
        return csv.reader(decoded)

    @staticmethod
    def get_processed_header(file):
        try:
            file.seek(0)
            decoded = file.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded)
            header = next(reader)
            return process_headers(header)
        except StopIteration:
            return []

    @staticmethod
    def get_raw_header(file):
        try:
            file.seek(0)
            decoded = file.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded)
            return next(reader)
        except StopIteration:
            return []


# TODO : Add support for XLS files if needed
class XLSXStrategy:
    @staticmethod
    def get_reader(file):
        file.seek(0)
        wb = openpyxl.load_workbook(file)
        sheet = wb.active
        return sheet.iter_rows(values_only=True)

    @staticmethod
    def get_processed_header(reader):
        try:
            header = next(reader)
            return process_headers(header)
        except StopIteration:
            return []

    @staticmethod
    def get_raw_header(reader):
        try:
            return next(reader)
        except StopIteration:
            return []


def get_strategy(file):
    mime_type = file.content_type
    if mime_type == "text/csv":
        return CSVStrategy
    elif mime_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
        return XLSXStrategy
    else:
        raise ValueError("Unsupported file type")
