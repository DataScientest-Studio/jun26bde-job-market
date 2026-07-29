"""Build and serve a map representation of job locations."""

from __future__ import annotations

import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import folium
import pandas as pd


class JobMapBuilder:
    def __init__(
        self,
        db_path: str = "src/data/processed/job_market.sqlite3",
        table_name: str = "job_locations",
        output_file: str = "map.html",
        host: str = "0.0.0.0",
        port: int = 8000,
    ) -> None:
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
            return pd.read_sql_query(query, conn)

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
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        m.save(str(self.output_file))
        return self.output_file

    def build(self) -> Path:
        df = self.load_data()
        m = self.build_map(df)
        return self.save_map(m)

    def serve_forever(self) -> None:
        output_dir = self.output_file.resolve().parent

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(output_dir), **kwargs)

        server = ThreadingHTTPServer((self.host, self.port), Handler)
        print(
            f"Serving map at http://{self.host}:"
            f"{self.port}/{self.output_file.name}"
        )
        server.serve_forever()

    def run(self) -> None:
        output_path = self.build()
        print(f"Map written to {output_path.resolve()}")
        self.serve_forever()


def main() -> None:
    app = JobMapBuilder()
    app.run()


if __name__ == "__main__":
    main()
