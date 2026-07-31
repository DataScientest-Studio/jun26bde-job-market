"""Build and serve a map representation of job locations."""

from __future__ import annotations

import os
import sqlite3
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import folium
import pandas as pd


def running_in_docker() -> bool:
    return os.environ.get("RUNNING_IN_DOCKER") == "1"

class JobMapBuilder:
    def __init__(
        self,
        db_path: str = "src/data/processed/job_market.sqlite3",
        table_name: str = "job_locations",
        output_file: str = "map.html",
        host: str | None = None,
        port: int = 8000,
        open_browser: bool | None = None,
    ) -> None:
        in_docker = running_in_docker()

        self.db_path = Path(db_path)
        self.table_name = table_name
        self.output_file = Path(output_file)
        self.host = host or ("0.0.0.0" if in_docker else "127.0.0.1")
        self.port = port
        self.open_browser_flag = (
            open_browser if open_browser is not None else not in_docker
        )

    def load_data(self) -> pd.DataFrame:
        query = f"""
            SELECT
                jl.reference_number,
                jl.latitude,
                jl.longitude,
                j.title AS job
            FROM {self.table_name} AS jl
            JOIN jobs AS j ON jl.reference_number = j.reference_number
            WHERE jl.latitude IS NOT NULL
                AND jl.longitude IS NOT NULL
                AND j.title IS NOT NULL
        """
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn)

    def build_map(self, df: pd.DataFrame) -> folium.Map:
        if df.empty:
            raise ValueError("No rows with latitude/longitude found.")

        center_lat = df["latitude"].mean()
        center_lon = df["longitude"].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

        palette = [
            "red", "blue", "green", "purple", "orange",
            "darkred", "lightred", "beige", "darkblue", "darkgreen",
            "cadetblue", "darkpurple", "pink", "lightblue",
            "lightgreen", "gray", "lightgray",
        ]

        jobs = sorted(df["job"].fillna("Unknown").unique())
        color_map = {job: palette[i % len(palette)] for i, job in enumerate(jobs)}

        for _, row in df.iterrows():
            job = row["job"] if pd.notna(row["job"]) else "Unknown"
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=f"{row['reference_number']}<br>{job}",
                icon=folium.Icon(color=color_map[job], icon="briefcase", prefix="fa"),
            ).add_to(m)

        return m

    def save_map(self, m: folium.Map) -> Path:
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        html = m.get_root().render()

        referrer_meta = (
            '<meta name="referrer" content="strict-origin-when-cross-origin">'
        )
        if "<head>" in html:
            html = html.replace("<head>", f"<head>{referrer_meta}", 1)
        else:
            html = referrer_meta + html

        self.output_file.write_text(html, encoding="utf-8")
        return self.output_file

    def serve(self, block: bool) -> ThreadingHTTPServer:
        output_dir = self.output_file.resolve().parent

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(output_dir), **kwargs)

            def end_headers(self) -> None:
                self.send_header(
                    "Referrer-Policy", "strict-origin-when-cross-origin"
                )
                super().end_headers()

        server = ThreadingHTTPServer((self.host, self.port), Handler)
        url = f"http://{self.host}:{self.port}/{self.output_file.name}"
        print(f"Serving map at {url}")

        if self.open_browser_flag:
            webbrowser.open(url)

        if block:
            server.serve_forever()
        else:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

        return server

    def build(self) -> Path:
        df = self.load_data()
        m = self.build_map(df)
        return self.save_map(m)

    def run(self, block: bool | None = None) -> ThreadingHTTPServer:
        output_path = self.build()
        print(f"Map written to {output_path.resolve()}")
        should_block = block if block is not None else running_in_docker()
        return self.serve(block=should_block)


def main() -> None:
    app = JobMapBuilder()
    app.run()


if __name__ == "__main__":
    main()