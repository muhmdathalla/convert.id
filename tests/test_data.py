import tempfile
from pathlib import Path
from convert_id.engines.data_engine import DataEngine

def test_data_polyglot():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        engine = DataEngine()

        # 1. JSON to YAML
        json_file = tdp / "data.json"
        json_file.write_text('{"name": "convert.id", "status": "active", "features": 20}', encoding="utf-8")
        
        yaml_file = tdp / "data.yaml"
        res1 = engine.convert(json_file, yaml_file)
        assert res1.success
        assert yaml_file.exists()
        assert "features: 20" in yaml_file.read_text(encoding="utf-8")

        # 2. CSV to SQL Schema & INSERT statements
        csv_file = tdp / "users.csv"
        csv_file.write_text("id,username,email\n1,athalla,athalla@example.com\n2,antigravity,anti@example.com\n", encoding="utf-8")

        sql_file = tdp / "users.sql"
        res2 = engine.convert(csv_file, sql_file, table_name="app_users")
        assert res2.success
        assert sql_file.exists()
        sql_content = sql_file.read_text(encoding="utf-8")
        assert "CREATE TABLE IF NOT EXISTS `app_users`" in sql_content
        assert "INSERT INTO `app_users`" in sql_content
        assert "athalla" in sql_content

        print("Data polyglot test passed successfully!")

if __name__ == "__main__":
    test_data_polyglot()
