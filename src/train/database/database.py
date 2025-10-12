import sqlite3
from typing import List
from torch import Tensor


class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name

        # HEADER INFO
        self.INTEGER_LABELS: List[str] = ["white_elo", "black_elo"]
        self.BOOLEAN_LABELS: List[str] = ["is_black"]
        # Columns exactly as in the provided selection
        self.CLASS_LABELS: List[str] = [
            # board squares
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "A6",
            "A7",
            "A8",
            "B1",
            "B2",
            "B3",
            "B4",
            "B5",
            "B6",
            "B7",
            "B8",
            "C1",
            "C2",
            "C3",
            "C4",
            "C5",
            "C6",
            "C7",
            "C8",
            "D1",
            "D2",
            "D3",
            "D4",
            "D5",
            "D6",
            "D7",
            "D8",
            "E1",
            "E2",
            "E3",
            "E4",
            "E5",
            "E6",
            "E7",
            "E8",
            "F1",
            "F2",
            "F3",
            "F4",
            "F5",
            "F6",
            "F7",
            "F8",
            "G1",
            "G2",
            "G3",
            "G4",
            "G5",
            "G6",
            "G7",
            "G8",
            "H1",
            "H2",
            "H3",
            "H4",
            "H5",
            "H6",
            "H7",
            "H8",
        ]
        self.TARGET_COLUMN: str = "selected_move"

        self.ALL_HEADERS = []
        self.ALL_HEADERS.extend(self.INTEGER_LABELS)
        self.ALL_HEADERS.extend(self.BOOLEAN_LABELS)
        self.ALL_HEADERS.extend(self.CLASS_LABELS)
        self.ALL_HEADERS.append(self.TARGET_COLUMN)

        # FILTERING INFO
        self.MIN_ELO = 600
        self.MAX_ELO = 1900

        self._ensure_table_exist()

    def _ensure_table_exist(self) -> None:
        """
        Ensures the state table exists in the database.

        Attributes:
            db_name: The name of the SQLite database file.
            INTEGER_LABELS: List of column headers for integer-type data.
            BOOLEAN_LABELS: List of column headers for boolean-type data
                           (represented as integers).
            CLASS_LABELS: List of column headers for class data (stored as indexes).
            TARGET_COLUMN: The column header for the target class.

        Raises:
            OperationalError: Raised if an issue occurs during database operations.

        """

        def _append_columns(headers: List[str], data_type: str) -> str:
            new_columns = ""
            for header in headers:
                new_columns += f"{header} {data_type}, "

            return new_columns

        """Create tables if they don't exist"""
        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()

            query = "CREATE TABLE IF NOT EXISTS state ("

            # add the various labels
            query += _append_columns(self.INTEGER_LABELS, "INTEGER")
            query += _append_columns(self.BOOLEAN_LABELS, "INTEGER")
            query += _append_columns(
                self.CLASS_LABELS, "INTEGER"
            )  # classes are stored as indexes

            # add the target class
            query += f"{self.TARGET_COLUMN} TEXT)"
            cur.execute(query)
            conn.commit()

    def _process_row(self, row: List):
        """Process a single row, converting labels to integers in a much more condensed way"""
        try:
            # try and convert all but the target to an int which is a string
            target = row[-1]
            labels = [int(label) for label in row[:-1]]
            labels.append(target)
            return labels  # labels + target
        except ValueError as e:
            print(e)
            print(
                f"Row Processing Warning: Could not convert row to integers: {e}. Ignoring row."
            )
            return None

    def _insert_state(self, state_data: List) -> None:
        """
        Saves the given state data to the database by formatting and inserting it
        into the 'state' SQL table. Converts all labels from the list into integers
        or skips processing if conversion fails for any label. This assumes that the
        ordering of the labels in the list is the same as the ordering of the columns.

        Attributes:
            db_name: The name of the database to which the state data is saved.

        Args:
            state_data (List): A list where all elements are the data for a single
            state in the order they would appear in the columns.

        Raises:
            ValueError: Raised internally when a label cannot be converted to an integer.
        """
        # try and convert all labels to ints if any fail ignore given state and print warning
        labels = state_data[:-1]
        for i in range(len(labels)):
            try:
                labels[i] = int(labels[i])
            except ValueError as e:
                print(
                    f"Insert State Warning:{e} Could not convert label {i} - {labels[i]} to int. Ignoring state."
                )

        # format for SQL insert statement
        processed_data = ""
        for label in labels:
            processed_data += f"{label}, "

        # add target value

        processed_data += f"'{state_data[-1]}'"

        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute(f"INSERT INTO state VALUES ({processed_data})")
            conn.commit()

    def _insert_batch(self, batch: List[List]) -> None:
        # Create placeholders for the INSERT statement
        num_columns = len(self.ALL_HEADERS)
        placeholders = ", ".join(["?"] * num_columns)

        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.executemany(f"INSERT INTO state VALUES ({placeholders})", batch)
            conn.commit()

    @staticmethod
    def _get_target_label(algebraic_notation_move: str):
        pass

    def import_csv(self, csv_path: str, batch_size: int = 32) -> None:
        """
        Imports data from a CSV file by processing each line and saves it using
        the internal storage mechanism. The method reads the file line-by-line
        to extract and process the data.

        Parameters:
        csv_path: str
            The file path of the CSV file to be imported.

        Raises:
        FileNotFoundError
            If the specified file does not exist.
        PermissionError
            If the file cannot be accessed due to insufficient permissions.
        """
        with open(csv_path, "r") as file:
            file.readline()  # skip the header line
            line = file.readline()

            processed_batch = []

            while line:
                line = line.strip()  # remove new-line
                data = line.split(",")
                # self._insert_state(data)
                processed_row = self._process_row(data)
                if processed_row is not None:
                    # check if either elo is outside range
                    white_elo = processed_row[0]
                    black_elo = processed_row[1]

                    if not (
                        white_elo < self.MIN_ELO
                        or white_elo > self.MAX_ELO
                        or black_elo < self.MIN_ELO
                        or black_elo > self.MAX_ELO
                    ):
                        processed_batch.append(self._process_row(data))
                else:
                    print("CSV Warning: Row could not be processed. Skipping.")

                # if processed amount reaches batch_size insert and clear the cache
                if len(processed_batch) == batch_size:
                    print("Batch size reached, inserting batch...")
                    self._insert_batch(processed_batch)
                    processed_batch = []

                line = file.readline()

            # insert the remaining batch
            if processed_batch:
                self._insert_batch(processed_batch)

    def state_count(self) -> int:
        with sqlite3.connect(self.db_name) as conn:
            return conn.execute("SELECT COUNT(*) FROM state").fetchone()[0]

    def get_item(self, index: int) -> Tensor:
        pass
