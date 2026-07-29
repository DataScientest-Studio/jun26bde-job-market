"""build map representation of job locations"""

import sqlite3
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import folium
import pandas as pd


class JobMapBuilder:
    def __init__(
        self,
        db_path="src/data/processed/job_market.sqlite3",
        table_name="job_locations",
        output_file="map.html",
        host="127.0.0.1",
        port=8000,
    ):
        self.db_path = Path(db_path)
        self.table_name = table_name
        self.output_file = Path(output_file)
        self.host = host
        self.port = port

    def load_data(self) -> pd.DataFrame:
        query = f"""
        SELECT reference_number, latitude, longitude
        FROM {self.table_name}
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        """
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn)
        return df

    def build_map(self, df: pd.DataFrame) -> folium.Map:
        if df.empty:
            raise ValueError("No rows with latitude/longitude found.")

        center_lat = df["latitude"].mean()
        center_lon = df["longitude"].mean()

        m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

        for _, row in df.iterrows():
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=str(row["reference_number"]),
            ).add_to(m)

        return m

    def save_map(self, m: folium.Map) -> Path:
        m.save(str(self.output_file))
        return self.output_file

    def serve_map(self) -> ThreadingHTTPServer:
        output_dir = self.output_file.resolve().parent

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(output_dir), **kwargs)

        server = ThreadingHTTPServer((self.host, self.port), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server

    def open_browser(self):
        webbrowser.open(
            f"http://{self.host}:{self.port}/{self.output_file.name}"
        )

    def run(self, open_browser=True):
        df = self.load_data()
        m = self.build_map(df)
        self.save_map(m)
        server = self.serve_map()

        if open_browser:
            self.open_browser()

        return server


if __name__ == "__main__":
    app = JobMapBuilder()
    app.run()
