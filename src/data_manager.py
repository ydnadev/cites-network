import duckdb
import pandas as pd


class CITESDataManager:
    def __init__(self, parquet_path, countries_csv, itis_csv):
        self.parquet_path = parquet_path
        self.countries_csv = countries_csv
        self.itis_csv = itis_csv
        self.duckdb_conn = duckdb.connect()
        self._load_countries()
        self._load_itis()

    def _load_countries(self):
        self.countries = pd.read_csv(self.countries_csv, keep_default_na=False)

    def _load_itis(self):
        self.itis = pd.read_csv(self.itis_csv, keep_default_na=False)

    def unique_taxa(self):
        query = f"SELECT DISTINCT Taxon FROM '{self.parquet_path}'"
        return self.duckdb_conn.execute(query).fetchdf()

    def summary_stats(self):
        row_count = (
            self.duckdb_conn.execute(
                f"SELECT COUNT(*) AS rows FROM '{self.parquet_path}'"
            )
            .fetchdf()
            .iat[0, 0]
        )
        taxon_count = (
            self.duckdb_conn.execute(
                f"SELECT COUNT(DISTINCT Taxon) AS taxon FROM '{self.parquet_path}'"
            )
            .fetchdf()
            .iat[0, 0]
        )
        importer_count = (
            self.duckdb_conn.execute(
                f"SELECT COUNT(DISTINCT Importer) AS importer FROM '{self.parquet_path}'"
            )
            .fetchdf()
            .iat[0, 0]
        )
        exporter_count = (
            self.duckdb_conn.execute(
                f"SELECT COUNT(DISTINCT Exporter) AS exporter FROM '{self.parquet_path}'"
            )
            .fetchdf()
            .iat[0, 0]
        )
        return {
            "taxa": taxon_count,
            "importers": importer_count,
            "exporters": exporter_count,
            "rows": row_count,
        }

    # def filter_by_taxon(self, taxon, year_range=None, term=None):
    #     query = f"SELECT * FROM '{self.parquet_path}' WHERE Taxon = ?"
    #     params = [taxon]
    #     if year_range:
    #         query += " AND Year >= ? AND Year <= ?"
    #         params.extend(year_range)
    #     if term:
    #         query += " AND Term = ?"
    #         params.append(term)
    #     return self.duckdb_conn.execute(query, params).fetchdf()

    def get_terms_for_taxon(self, taxon, year_range):
        query = (
            f"SELECT DISTINCT Term FROM '{self.parquet_path}' "
            "WHERE Taxon = ? AND Year >= ? AND Year <= ?"
        )
        try:
            return self.duckdb_conn.execute(
                query, [taxon, year_range[0], year_range[1]]
            ).fetchdf()
        except duckdb.ProgrammingError as e:
            return pd.DataFrame()

    def get_purpose_for_taxon(self, taxon, year_range=None, term=None):
        query = f"SELECT DISTINCT Purpose FROM '{self.parquet_path}' WHERE Taxon = ?"
        params = [taxon]
        #if year_range:
        #    query = (
        #        f"SELECT DISTINCT Purpose FROM '{self.parquet_path}' "
        #        "WHERE Taxon = ? AND Year >= ? AND Year <= ?"
        #    )
        if year_range:
            query += " AND cast(Year as integer) >= ? AND cast(Year as integer) <= ? AND Exporter is not null and Importer is not null"
            params.extend(year_range)
        if term != "ALL" and term != None:
            query += " AND Term = ?"
            params.append(term)
        #return self.duckdb_conn.execute(
        #    query, [taxon, year_range[0], year_range[1]]
        #).fetchdf()
        try:
            return self.duckdb_conn.execute(query, params).fetchdf()
        except duckdb.ProgrammingError as e:
            return pd.DataFrame()

    def get_source_for_taxon(self, taxon, year_range=None, term=None, purpose=None):
        query = f"SELECT DISTINCT Source FROM '{self.parquet_path}' WHERE Taxon = ?"
        params = [taxon]
        # if year_range:
        #    query = (
        #        f"SELECT DISTINCT Purpose FROM '{self.parquet_path}' "
        #        "WHERE Taxon = ? AND Year >= ? AND Year <= ?"
        #    )
        if year_range:
            query += " AND cast(Year as integer) >= ? AND cast(Year as integer) <= ? AND Exporter is not null and Importer is not null"
            params.extend(year_range)
        if term != "ALL" and term != None:
            query += " AND Term = ?"
            params.append(term)
        if purpose != "ALL" and purpose != None:
            query += " AND Purpose = ?"
            params.append(purpose)
        # return self.duckdb_conn.execute(
        #    query, [taxon, year_range[0], year_range[1]]
        # ).fetchdf()
        #return self.duckdb_conn.execute(query, params).fetchdf()
        try:
            return self.duckdb_conn.execute(query, params).fetchdf()
        except duckdb.ParserException as e:
            return pd.DataFrame()

    def filter_by_taxon(self, taxon, year_range=None, term=None, purpose=None, source=None):
        #query = f"SELECT Exporter, Importer, Unit, sum(cast(Quantity as integer)) as Weight FROM '{self.parquet_path}' WHERE Taxon = ?"
        query = f"""SELECT Exporter, Importer, Unit, sum(cast(Quantity as integer)) as Weight FROM "{self.parquet_path}" WHERE Taxon = ? and "Reporter.type" = 'E'"""
        params = [taxon]
        if year_range:
            query += " AND cast(Year as integer) >= ? AND cast(Year as integer) <= ? AND Exporter is not null and Importer is not null"
            params.extend(year_range)
        if term != "ALL" and term != None:
            query += " AND Term = ?"
            params.append(term)
        if purpose != "ALL" and purpose != None:
            query += " AND Purpose = ?"
            params.append(purpose)
        if source != "ALL" and source != None:
            query += " AND Source = ?"
            params.append(source)
        query += "group by Exporter, Importer, Unit"
        try:
            return self.duckdb_conn.execute(query, params).fetchdf()
        except duckdb.ParserException as e:
            return pd.DataFrame()

    def filter_by_taxon_results(self, taxon, year_range=None, term=None, purpose=None, source=None):
        query = f"SELECT * FROM '{self.parquet_path}' WHERE Taxon = ?"
        params = [taxon]
        if year_range:
            query += " AND cast(Year as integer) >= ? AND cast(Year as integer) <= ? AND Exporter is not null and Importer is not null"
            params.extend(year_range)
        if term != "ALL" and term != None:
            query += " AND Term = ?"
            params.append(term)
        if purpose != "ALL" and purpose != None:
            query += " AND Purpose = ?"
            params.append(purpose)
        if source != "ALL" and source != None:
            query += " AND Source = ?"
            params.append(source)
        #return self.duckdb_conn.execute(query, params).fetchdf()
        try:
            return self.duckdb_conn.execute(query, params).fetchdf()
        except duckdb.ParserException as e:
            return pd.DataFrame()

